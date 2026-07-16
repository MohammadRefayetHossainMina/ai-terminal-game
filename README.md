# Australian Jones 🏍️

A terminal-based treasure hunting game built in Python. Navigate a 16x16 grid, collect treasures, avoid volcanic traps, and survive within a 2-minute time limit — all from your command line.

## Narrative

You are **Australian Jones**, a daring treasure hunter on a mission to recover lost relics scattered across a dangerous, wall-filled ruin. Volcanic traps lurk around every corner, slowly creeping toward you. You have a limited supply of ammo and only two lives. Collect 10 treasures before time runs out, or the ruins claim another victim.

## Features

### Movement
- **Arrow keys** (Up, Down, Left, Right) to navigate the 16x16 grid
- Walls (🧱) block both you and the hazards — use them strategically to funnel traps away from you

### Collectibles
- 📦 treasures spawn at random locations on the grid
- Collect 10 to win the game
- A new treasure appears immediately after each pickup

### Shooting
- **Spacebar** fires a 🔴 bullet at the nearest 🌋 hazard (auto-targeted, no manual aiming)
- Bullets travel in a straight line (horizontal or vertical) and stop at walls
- Only the first hazard in the bullet's path is destroyed

### Hazard AI
- 3–5 volcanic traps spawn on the grid and chase you using greedy pathfinding
- Hazards respect walls and try alternate routes when blocked
- Destroyed hazards respawn after a 2-second delay at a random empty location

### Win and Lose Conditions
- **Win:** Collect 10 📦 treasures
- **Lose:** Hit a 🌋 trap twice (2 lives) or let the 120-second timer expire
- After each game, choose to **play again (y)** or **quit (n)**

## How to Run

### Launch the Game
```bash
python game.py
```

### Run Tests
```bash
python -m pytest test_game.py -v
```

The test suite includes 107 tests covering movement, walls, shooting, hazard AI, spawning, collisions, respawn delays, win/lose conditions, and theme consistency.

## Project Structure

```
ai-terminal-game/
  game.py         # Main game logic, rendering, and game loop
  test_game.py    # pytest test suite (107 tests)
  README.md       # This file
```

## What I Learned

### Iterative Development
This game was built one feature at a time: movement first, then collectibles, then hazards, then shooting, then walls. Each layer was tested before adding the next. This made it easy to pinpoint exactly where bugs were introduced — if shooting broke after adding walls, the problem had to be in the new wall-collision logic, not the movement code.

### Engineering Prompts to Prevent Regression
When adding new features like hazard respawning or wall-aware AI, careful prompt design was essential. Describing *exactly* what should and should not change prevented earlier features from breaking. For example, when adding the alternate screen buffer to fix flicker, the prompt explicitly preserved all existing game mechanics while only modifying screen rendering.

### Automated Tests as a Safety Net
Writing 107 tests meant that every change could be verified in under a second. Tests caught regressions immediately — a wrong emoji constant, a broken wall check, or a hazard that could walk through walls. The discipline of running `pytest` before every commit ensured that only working code reached GitHub.
