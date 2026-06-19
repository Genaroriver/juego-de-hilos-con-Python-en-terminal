 ⚔️ Battle Quest

> Juego de rol por turnos en la terminal, con historias creadas por los propios jugadores, sprites ASCII animados y persistencia de datos en JSON.

## 📖 Descripción

Battle Quest es un juego de combate por turnos que corre directamente en la consola. Cada partida se desarrolla dentro de una historia creada por otro jugador: tú escribes el escenario, defines al enemigo y dejas que alguien más lo enfrente. El sistema de combate incluye golpes críticos, defensa táctica e inteligencia artificial básica para el enemigo.

Todo el historial de partidas y las historias se guardan localmente en archivos JSON, por lo que no necesitas ninguna base de datos ni conexión a internet.

 ✨ Características

- 🎭 **Dos roles**: juega como **Héroe** (atacas al enemigo) o como **Enemigo** (controlas al villano contra la IA).
- 📜 **Historias comunitarias**: cualquier jugador puede escribir su propia historia y definir las estadísticas del enemigo.
- ⚔️ **Sistema de combate por turnos** con ataques normales, golpes críticos (20 % de probabilidad) y postura defensiva (reduce el daño a la mitad).
- 🤖 **IA adaptativa**: el enemigo controlado por la IA tiene más probabilidad de defenderse cuando su vida baja del 50 %.
- 🖼️ **Sprites ASCII** que cambian según la acción del turno: reposo, ataque, defensa y muerte.
- 📊 **Historial de partidas** con resumen de victorias y derrotas.
- 🎨 **Interfaz de consola con colores ANSI**, barras de HP dinámicas y mensajes contextuales.

---

🖥️ Capturas

```
════════════════════════════════════════════════════════
  ¡COMIENZA EL COMBATE!
════════════════════════════════════════════════════════

     _O_             /\_/\
    /. .\--         ( o.o )
    | . |~~          > ^ <
    \_._/            |   |
    /|||/           /|\ /|\
   / |.|             |   |
    _/ \_           /|   |\
   /     \

  HÉROE  Arturo            ENEMIGO  Dragón Oscuro
  HP [████████████████░░░░] 80/100
  HP [██████████░░░░░░░░░░] 75/150

  ⚔  Arturo atacó a Dragón Oscuro causando 15 de daño.
  💥  ¡GOLPE CRÍTICO! 44 de daño extra.
```

---

 🗂️ Estructura del proyecto

```
battle-quest/
│
├── battle_game.py       # Archivo principal (juego completo)
│
└── data/                # Generado automáticamente al ejecutar
    ├── stories.json     # Historias creadas por los jugadores
    └── history.json     # Historial de partidas jugadas
```

El código está organizado en capas lógicas dentro del mismo archivo:

| Sección | Responsabilidad |
|---|---|
| `Config` | Constantes del juego (HP, daño, probabilidades) |
| `UI` | Presentación: colores, barras de HP, sprites, prompts |
| `Storage` | Lectura y escritura de archivos JSON |
| `Character / Player / Enemy` | Modelos del dominio con lógica de combate |
| `CombatEngine` | Motor de turnos, resolución de acciones y resultado |
| `Game` | Flujo del menú principal y navegación entre pantallas |

---

## ⚙️ Requisitos

- Python **3.10** o superior (se usa `match/case` y `dataclasses`).
- Sin dependencias externas. Solo biblioteca estándar de Python.

---

## 🚀 Cómo ejecutar

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/battle-quest.git
cd battle-quest

# 2. Ejecuta el juego
python battle_game.py
```

La carpeta `data/` se crea automáticamente en la primera ejecución.

---

## 🎮 Cómo jugar

### Primera vez
1. Selecciona **"Crear historia"** en el menú principal.
2. Escribe un nombre de autor, describe el escenario y define las estadísticas del enemigo.
3. Vuelve al menú y selecciona **"Jugar"**.

### Partida
1. Escribe tu nombre de héroe.
2. Elige tu rol: **Héroe** o **Enemigo**.
3. Elige una historia de la lista disponible.
4. En cada turno decide si **Atacar** o **Defender**.
5. El combate termina cuando uno de los dos llega a 0 HP.

### Historial
Selecciona **"Ver historial"** para revisar todas las partidas anteriores con sus resultados.

---

## 🧮 Mecánicas de combate

| Mecánica | Valor |
|---|---|
| HP del héroe | 100 |
| HP del enemigo | 150 (configurable al crear historia) |
| Daño base | 10 – 30 aleatorio |
| Reducción por defensa del objetivo | `daño - defensa_objetivo` |
| Reducción al estar en postura defensiva | 50 % del daño final |
| Probabilidad de golpe crítico | 20 % |
| Daño crítico extra | 31 – 59 aleatorio |
| IA del enemigo: probabilidad de defenderse (HP < 50 %) | 30 % |

---

## 📁 Formato de datos

**`data/stories.json`**
```json
{
  "stories": [
    {
      "author": "Ana",
      "narrative": "En las profundidades del volcán duerme un dragón anciano...",
      "enemy": {
        "name": "Dragón Oscuro",
        "hp": 150,
        "hp_max": 150,
        "atk": 25,
        "defense": 8
      }
    }
  ]
}
```

**`data/history.json`**
```json
{
  "history": [
    {
      "player": "Carlos",
      "role": "hero",
      "result": "victoria",
      "story": "En las profundidades del volcán duerme un dragón anciano..."
    }
  ]
}
```

---

## 🛠️ Posibles mejoras futuras

- [ ] Sistema de niveles y experiencia para el héroe.
- [ ] Múltiples habilidades especiales por personaje.
- [ ] Modo multijugador local (dos jugadores en la misma terminal).
- [ ] Exportar historial a CSV o HTML.
- [ ] Soporte para sprites ASCII personalizados al crear historia.

---

## 👤 Autor

Desarrollado como proyecto personal de aprendizaje en Python.  
Si encuentras algún bug o quieres contribuir, abre un **Issue** o un **Pull Request**.

---

## 📄 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).
