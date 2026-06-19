"""
Battle Quest — Juego de batalla por turnos
==========================================
Arquitectura: módulos lógicos separados dentro de un solo archivo.
  · config.py   → constantes y rutas
  · storage     → capa de persistencia JSON
  · models      → entidades del dominio (Personaje, Jugador, Enemigo)
  · combat      → motor de combate
  · ui          → presentación en consola
  · game        → flujo principal y menú
"""

from __future__ import annotations

import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────

class Config:
    DATA_DIR        = Path("data")
    STORIES_FILE    = DATA_DIR / "stories.json"
    HISTORY_FILE    = DATA_DIR / "history.json"

    PLAYER_HP       = 100
    PLAYER_ATK      = 20
    PLAYER_DEF      = 5

    ENEMY_HP        = 150
    ENEMY_ATK       = 20
    ENEMY_DEF       = 5

    MIN_DAMAGE      = 10
    MAX_DAMAGE      = 30
    CRIT_CHANCE     = 0.20
    CRIT_MIN        = 31
    CRIT_MAX        = 59
    DEFEND_REDUCE   = 0.50
    LOW_HP_RATIO    = 0.50
    DEFEND_AI_PROB  = 0.30


# ──────────────────────────────────────────────
#  SPRITES ASCII
# ──────────────────────────────────────────────

HERO_IDLE = [
    r"   _O_   ",
    r"  /. .\  ",
    r"  | . |  ",
    r"  \_._/  ",
    r"  /|||\ ",
    r" / |.| \ ",
    r"  _/ \_  ",
    r" /     \ ",
]

HERO_ATTACK = [
    r"   _O_   ",
    r"  /. .\--",
    r"  | . |~~",
    r"  \_._/  ",
    r"  /|||/  ",
    r" / |.|   ",
    r"  _/ \_  ",
    r" /     \ ",
]

HERO_DEFEND = [
    r"   _O_   ",
    r"  /. .\  ",
    r" [| . |] ",
    r" [\_._/] ",
    r"  /||\  ",
    r"   |.|   ",
    r"  _/ \_  ",
    r" /     \ ",
]

HERO_DEAD = [
    r"         ",
    r"         ",
    r"  x . x  ",
    r" /\_._/\ ",
    r" ||||||| ",
    r"_________",
    r"         ",
    r"         ",
]

ENEMY_IDLE = [
    r"  /\_/\  ",
    r" ( o.o ) ",
    r"  > ^ <  ",
    r"  |   |  ",
    r" /|\ /|\ ",
    r"  |   |  ",
    r" /|   |\ ",
    r"         ",
]

ENEMY_ATTACK = [
    r"  /\_/\  ",
    r" ( >.< ) ",
    r"  > ^ <  ",
    r"--\   |  ",
    r"~~\|\ /|\ ",
    r"  |   |  ",
    r" /|   |\ ",
    r"         ",
]

ENEMY_DEFEND = [
    r"  /\_/\  ",
    r" ( -.- ) ",
    r" [> ^ <] ",
    r" [|   |] ",
    r"  /|\ /|\ ",
    r"  |   |  ",
    r" /|   |\ ",
    r"         ",
]

ENEMY_DEAD = [
    r"         ",
    r"         ",
    r" ( x.x ) ",
    r" /\_._/\ ",
    r" ||||||| ",
    r"_________",
    r"         ",
    r"         ",
]


def _render_side_by_side(left_lines: list[str], right_lines: list[str],
                          gap: int = 6) -> list[str]:
    """Une dos sprites lado a lado con un hueco entre ellos."""
    max_len = max((len(l) for l in left_lines), default=0)
    rows = max(len(left_lines), len(right_lines))
    result = []
    for i in range(rows):
        l = left_lines[i]  if i < len(left_lines)  else ""
        r = right_lines[i] if i < len(right_lines) else ""
        result.append(l.ljust(max_len) + " " * gap + r)
    return result


# ──────────────────────────────────────────────
#  CAPA DE PRESENTACIÓN (UI)
# ──────────────────────────────────────────────

class UI:
    WIDTH = 56

    # ── colores ANSI ──
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"

    @classmethod
    def _supports_color(cls) -> bool:
        return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    @classmethod
    def color(cls, text: str, *codes: str) -> str:
        if not cls._supports_color():
            return text
        return "".join(codes) + text + cls.RESET

    # ── primitivas de layout ──
    @classmethod
    def line(cls, char: str = "─") -> None:
        print(cls.color(char * cls.WIDTH, cls.DIM))

    @classmethod
    def header(cls, title: str) -> None:
        print()
        cls.line("═")
        print(cls.color(f"  {title.upper()}", cls.BOLD + cls.CYAN))
        cls.line("═")

    @classmethod
    def section(cls, title: str) -> None:
        print()
        cls.line()
        print(cls.color(f"  {title}", cls.BOLD))
        cls.line()

    @classmethod
    def success(cls, msg: str) -> None:
        print(cls.color(f"  ✓  {msg}", cls.GREEN))

    @classmethod
    def warn(cls, msg: str) -> None:
        print(cls.color(f"  ⚠  {msg}", cls.YELLOW))

    @classmethod
    def error(cls, msg: str) -> None:
        print(cls.color(f"  ✗  {msg}", cls.RED))

    @classmethod
    def info(cls, msg: str) -> None:
        print(f"  {msg}")

    @classmethod
    def prompt(cls, label: str) -> str:
        try:
            return input(cls.color(f"\n  ▸ {label}: ", cls.CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise SystemExit(0)

    @classmethod
    def hp_bar(cls, current: int, maximum: int, length: int = 20) -> str:
        ratio       = current / maximum if maximum > 0 else 0
        filled      = round(ratio * length)
        bar         = "█" * filled + "░" * (length - filled)
        color_code  = cls.GREEN if ratio > 0.6 else (cls.YELLOW if ratio > 0.3 else cls.RED)
        return cls.color(f"[{bar}]", color_code) + f" {current}/{maximum}"

    @classmethod
    def combat_status(cls, player_name: str, player_hp: int, player_hp_max: int,
                      enemy_name: str, enemy_hp: int, enemy_hp_max: int,
                      player_sprite=None, enemy_sprite=None) -> None:
        print()
        p_sprite = player_sprite if player_sprite else HERO_IDLE
        e_sprite = enemy_sprite  if enemy_sprite  else ENEMY_IDLE
        scene    = _render_side_by_side(p_sprite, e_sprite, gap=8)
        for row in scene:
            print(f"  {cls.color(row, cls.DIM)}")
        print()
        p_col = cls.color("HÉROE",   cls.BOLD + cls.CYAN)
        e_col = cls.color("ENEMIGO", cls.BOLD + cls.RED)
        print(f"  {p_col} {player_name:<25}  {e_col} {enemy_name}")
        print(f"  HP {cls.hp_bar(player_hp, player_hp_max)}")
        print(f"  HP {cls.hp_bar(enemy_hp,  enemy_hp_max)}")
        print()

    @classmethod
    def choose(cls, options: list[str]) -> int:
        """Muestra opciones numeradas y devuelve el índice elegido (0-based)."""
        for i, opt in enumerate(options, start=1):
            print(cls.color(f"  [{i}]", cls.YELLOW) + f" {opt}")
        while True:
            raw = cls.prompt("Elige una opción")
            if raw.isdigit():
                idx = int(raw) - 1
                if 0 <= idx < len(options):
                    return idx
            cls.error("Opción inválida, intenta de nuevo.")


# ──────────────────────────────────────────────
#  CAPA DE PERSISTENCIA
# ──────────────────────────────────────────────

class Storage:

    @staticmethod
    def _ensure_dir() -> None:
        Config.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _read(path: Path, default: dict) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (FileNotFoundError, json.JSONDecodeError):
            return default

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        Storage._ensure_dir()
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)

    # ── historias ──
    @classmethod
    def load_stories(cls) -> list[dict]:
        return cls._read(Config.STORIES_FILE, {"stories": []})["stories"]

    @classmethod
    def save_story(cls, author: str, narrative: str,
                   enemy_name: str, hp: int, atk: int, defense: int) -> None:
        data = cls._read(Config.STORIES_FILE, {"stories": []})
        data["stories"].append({
            "author":    author,
            "narrative": narrative,
            "enemy": {
                "name":    enemy_name,
                "hp":      hp,
                "hp_max":  hp,
                "atk":     atk,
                "defense": defense,
            }
        })
        cls._write(Config.STORIES_FILE, data)

    # ── historial ──
    @classmethod
    def save_match(cls, player: str, role: str, result: str, story: str) -> None:
        data = cls._read(Config.HISTORY_FILE, {"history": []})
        data["history"].append({
            "player":  player,
            "role":    role,
            "result":  result,
            "story":   story,
        })
        cls._write(Config.HISTORY_FILE, data)

    @classmethod
    def load_history(cls) -> list[dict]:
        return cls._read(Config.HISTORY_FILE, {"history": []})["history"]


# ──────────────────────────────────────────────
#  MODELOS DE DOMINIO
# ──────────────────────────────────────────────

@dataclass
class Character:
    name:          str
    hp:            int
    hp_max:        int
    atk:           int
    defense:       int
    _defending:    bool = field(default=False, init=False, repr=False)

    # ── propiedades ──
    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    @property
    def is_defending(self) -> bool:
        return self._defending

    @property
    def hp_ratio(self) -> float:
        return self.hp / self.hp_max if self.hp_max > 0 else 0

    # ── acciones ──
    def take_damage(self, amount: int) -> int:
        """Aplica daño y devuelve el daño real recibido."""
        actual = max(1, amount)
        self.hp = max(0, self.hp - actual)
        return actual

    def set_defending(self, state: bool) -> None:
        self._defending = state

    def attack(self, target: "Character") -> list[str]:
        """
        Realiza un ataque y devuelve los mensajes del turno.
        Separar la lógica de la presentación facilita el testing.
        """
        messages: list[str] = []

        base_damage = random.randint(Config.MIN_DAMAGE, Config.MAX_DAMAGE)
        reduced     = max(1, base_damage - target.defense)
        if target.is_defending:
            reduced = max(1, int(reduced * Config.DEFEND_REDUCE))
        dealt = target.take_damage(reduced)
        messages.append(f"{self.name} atacó a {target.name} causando {dealt} de daño.")

        if random.random() < Config.CRIT_CHANCE:
            crit = random.randint(Config.CRIT_MIN, Config.CRIT_MAX)
            target.take_damage(crit)
            messages.append(f"¡GOLPE CRÍTICO! {crit} de daño extra.")

        return messages

    def defend(self) -> str:
        self.set_defending(True)
        return f"{self.name} adopta postura defensiva."

    def reset_defense(self) -> None:
        self.set_defending(False)


class Player(Character):
    """Personaje controlado por el usuario."""

    def choose_action(self) -> str:
        UI.info(UI.color("¿Qué haces este turno?", UI.BOLD))
        idx = UI.choose(["Atacar", "Defender"])
        return "attack" if idx == 0 else "defend"


class Enemy(Character):
    """Personaje controlado por IA."""

    def decide_action(self) -> str:
        if self.hp_ratio < Config.LOW_HP_RATIO and random.random() < Config.DEFEND_AI_PROB:
            return "defend"
        return "attack"


# ──────────────────────────────────────────────
#  MOTOR DE COMBATE
# ──────────────────────────────────────────────

class CombatEngine:

    def __init__(self, player: Player, enemy: Enemy, user_role: str) -> None:
        self._player         = player
        self._enemy          = enemy
        self._role           = user_role  # "hero" | "enemy"
        self._turn           = 1
        self._active         = "player"   # quién mueve ahora
        self._player_sprite  = HERO_IDLE
        self._enemy_sprite   = ENEMY_IDLE

    # ── bucle principal ──
    def run(self) -> str:
        """Ejecuta el combate y devuelve 'victory' o 'defeat'."""
        UI.header("¡Comienza el combate!")

        while self._player.is_alive and self._enemy.is_alive:
            UI.section(f"Turno {self._turn}")
            UI.combat_status(
                self._player.name, self._player.hp, self._player.hp_max,
                self._enemy.name,  self._enemy.hp,  self._enemy.hp_max,
                player_sprite=self._player_sprite,
                enemy_sprite=self._enemy_sprite,
            )
            self._player_sprite = HERO_IDLE
            self._enemy_sprite  = ENEMY_IDLE
            self._execute_turn()
            self._turn += 1

        return self._resolve_result()

    # ── lógica de turno ──
    def _execute_turn(self) -> None:
        if self._active == "player":
            self._player_phase()
            self._enemy.reset_defense()
        else:
            self._enemy_phase()
            self._player.reset_defense()

        self._active = "enemy" if self._active == "player" else "player"

    def _player_phase(self) -> None:
        if self._role == "hero":
            action = self._player.choose_action()
        else:
            action = "attack"

        if action == "attack":
            self._player_sprite = HERO_ATTACK
        else:
            self._player_sprite = HERO_DEFEND
        self._apply_action(self._player, self._enemy, action)

    def _enemy_phase(self) -> None:
        if self._role == "enemy":
            UI.info(UI.color(f"Controlas a {self._enemy.name}:", UI.BOLD))
            action = self._player.choose_action()
            if action == "attack":
                self._enemy_sprite = ENEMY_ATTACK
            else:
                self._enemy_sprite = ENEMY_DEFEND
            self._apply_action(self._enemy, self._player, action)
        else:
            action = self._enemy.decide_action()
            if action == "attack":
                self._enemy_sprite = ENEMY_ATTACK
            else:
                self._enemy_sprite = ENEMY_DEFEND
            self._apply_action(self._enemy, self._player, action)

    def _apply_action(self, actor: Character, target: Character, action: str) -> None:
        if action == "attack":
            for msg in actor.attack(target):
                icon = "⚔" if "CRÍTICO" not in msg else "💥"
                print(f"  {icon}  {msg}")
        else:
            msg = actor.defend()
            print(f"  🛡  {msg}")

    # ── resultado ──
    def _resolve_result(self) -> str:
        if self._player.is_alive and not self._enemy.is_alive:
            winner, loser    = self._player, self._enemy
            p_sprite, e_sprite = HERO_IDLE, ENEMY_DEAD
        else:
            winner, loser    = self._enemy, self._player
            p_sprite, e_sprite = HERO_DEAD, ENEMY_IDLE

        UI.combat_status(
            self._player.name, self._player.hp, self._player.hp_max,
            self._enemy.name,  self._enemy.hp,  self._enemy.hp_max,
            player_sprite=p_sprite, enemy_sprite=e_sprite,
        )
        print()
        UI.line("═")
        print(UI.color(f"  🏆  ¡{winner.name} ha ganado el combate!", UI.BOLD + UI.YELLOW))
        UI.line("═")

        if self._role == "hero":
            return "victoria" if self._player.is_alive else "derrota"
        return "victoria" if self._enemy.is_alive else "derrota"


# ──────────────────────────────────────────────
#  FLUJO DE JUEGO
# ──────────────────────────────────────────────

class Game:

    # ── menú principal ──
    def run(self) -> None:
        UI.header("Battle Quest")
        while True:
            UI.section("Menú principal")
            option = UI.choose([
                "Jugar",
                "Crear historia",
                "Ver historial",
                "Salir",
            ])
            actions = [self._play, self._create_story, self._show_history, self._exit]
            actions[option]()

    # ── opción 1: jugar ──
    def _play(self) -> None:
        stories = Storage.load_stories()
        if not stories:
            UI.warn("No hay historias disponibles. ¡Crea una primero!")
            return
        1
        
        player_name = UI.prompt("Tu nombre de héroe")
        if not player_name:
            UI.error("El nombre no puede estar vacío.")
            return

        UI.section("Elige tu rol")
        role = "hero" if UI.choose(["Héroe", "Enemigo"]) == 0 else "enemy"

        UI.section("Historias disponibles")
        self._list_stories(stories)
        story_idx = UI.choose([h["narrative"][:50] + "…" if len(h["narrative"]) > 50
                               else h["narrative"] for h in stories])
        chosen = stories[story_idx]

        UI.section("Historia")
        UI.info(chosen["narrative"])

        e_data = chosen["enemy"]
        player = Player(
            name=player_name,
            hp=Config.PLAYER_HP, hp_max=Config.PLAYER_HP,
            atk=Config.PLAYER_ATK, defense=Config.PLAYER_DEF,
        )
        enemy = Enemy(
            name=e_data["name"],
            hp=e_data["hp"], hp_max=e_data["hp_max"],
            atk=e_data["atk"], defense=e_data["defense"],
        )

        engine = CombatEngine(player, enemy, role)
        result = engine.run()

        if result == "victoria":
            UI.success("¡Ganaste la partida!")
        else:
            UI.warn("Perdiste esta vez. ¡Vuelve a intentarlo!")

        Storage.save_match(player_name, role, result, chosen["narrative"])

    # ── opción 2: crear historia ──
    def _create_story(self) -> None:
        UI.header("Crear nueva historia")

        author    = UI.prompt("Tu nombre (autor)")
        narrative = UI.prompt("Describe la historia")
        enemy_nm  = UI.prompt("Nombre del enemigo")

        try:
            atk = int(UI.prompt(f"Ataque del enemigo  (sugerido {Config.ENEMY_ATK})"))
            dfs = int(UI.prompt(f"Defensa del enemigo (sugerida {Config.ENEMY_DEF})"))
        except ValueError:
            UI.error("Los valores de ataque/defensa deben ser números enteros.")
            return

        if not all([author, narrative, enemy_nm]):
            UI.error("Todos los campos son obligatorios.")
            return

        Storage.save_story(author, narrative, enemy_nm,
                           hp=Config.ENEMY_HP, atk=atk, defense=dfs)
        UI.success(f"Historia de {author} guardada con éxito.")

    # ── opción 3: historial ──
    def _show_history(self) -> None:
        history = Storage.load_history()
        UI.header("Historial de partidas")

        if not history:
            UI.warn("Aún no hay partidas registradas.")
            return

        victories = sum(1 for m in history if m["result"] == "victoria")
        defeats   = len(history) - victories

        print(f"  Total: {len(history)} partidas  "
              f"{UI.color(f'✓ {victories}', UI.GREEN)}  "
              f"{UI.color(f'✗ {defeats}', UI.RED)}")
        UI.line()

        for i, match in enumerate(history, start=1):
            icon = UI.color("✓", UI.GREEN) if match["result"] == "victoria" else UI.color("✗", UI.RED)
            story_preview = (match["story"][:40] + "…") if len(match["story"]) > 40 else match["story"]
            print(f"  {i:>3}.  {icon}  "
                  f"{UI.color(match['player'], UI.BOLD)}  [{match['role']}]"
                  f"  —  {story_preview}")

    # ── opción 4: salir ──
    @staticmethod
    def _exit() -> None:
        UI.section("Hasta la próxima")
        UI.info("¡Gracias por jugar Battle Quest!")
        print()
        raise SystemExit(0)

    # ── helpers ──
    @staticmethod
    def _list_stories(stories: list[dict]) -> None:
        for i, s in enumerate(stories, start=1):
            e = s["enemy"]
            print(f"  {UI.color(str(i), UI.YELLOW)}.  {UI.color(s['author'], UI.BOLD)}"
                  f"  •  {e['name']}"
                  f"  (ATK {e['atk']} / DEF {e['defense']})")
            preview = s["narrative"][:60] + ("…" if len(s["narrative"]) > 60 else "")
            print(f"       {UI.color(preview, UI.DIM)}")


# ──────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ──────────────────────────────────────────────

def main() -> None:
    try:
        Game().run()
    except KeyboardInterrupt:
        print(UI.color("\n\n  Sesión interrumpida. ¡Hasta pronto!\n", UI.DIM))
        sys.exit(0)


if __name__ == "__main__":
    main()