# Ultimate Aim Trainer

A fast-paced, polished aim trainer built with **Pygame**.  
Click shrinking targets, build combos, manage lives, and chase high scores across three difficulty levels.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.5%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

- **Dynamic Targets** – Circular targets grow to max size then shrink. Miss the timing and they disappear.
- **Combo & Multiplier System** – Hit targets within 0.5 seconds of each other to build combos and multiply your score.
- **Lives System** – Start with 10 lives. Every miss costs a life and triggers screen shake feedback.
- **Three Difficulty Levels** – Easy, Medium, and Hard with different spawn rates and growth speeds.
- **Dynamic Difficulty Scaling** – Targets speed up as the round progresses.
- **Particle Effects** – Satisfying yellow/orange particles on every successful hit.
- **Clean UI** – Animated main menu, options menu, pause menu, and detailed end screen.
- **Restart Support** – Instantly restart after a game ends.
- **Custom Crosshair** – Precise white crosshair with black outline.
- **Smooth Transitions** – Fade effects between menus and gameplay.
- **60-Second Rounds** – Or until you run out of lives.

---

## Screenshots

> Add your own screenshots here after running the game

```
[Main Menu]   [Gameplay]   [End Screen]
```

---

## Requirements

| Requirement       | Details                                      |
|-------------------|----------------------------------------------|
| Operating System  | Windows, macOS, or Linux                     |
| Python            | 3.10 – 3.12 recommended (3.13/3.14 not fully supported yet) |
| Pygame            | 2.5 or higher                                |
| Hardware          | Mouse recommended (trackpad works but less precise) |
| Display           | Minimum 1280×720                             |

---

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/MeazbahMehedi/Ultimate-Aim-Trainer.git
   cd Ultimate-Aim-Trainer
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv .venv

   # Windows
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install pygame
   ```

4. **Run the game**
   ```bash
   python aim_trainer.py
   ```

---

## Project Structure

```
Ultimate-Aim-Trainer/
├── aim_trainer.py      # Main game loop and entry point
├── ui_manager.py       # Menus, HUD, cursor, transitions
├── target.py           # Target class (grow/shrink + collision)
├── particle.py         # Hit particle effects
├── button.py           # Reusable button with hover animation
└── README.md
```

---

## How to Play

### Starting the Game
1. Launch `aim_trainer.py`.
2. On the **Main Menu**:
   - **Start** → Begin with Medium difficulty.
   - **Options** → Choose Easy / Medium / Hard (starts immediately).
   - **Quit** → Exit the game.
3. Click anywhere when you see **"Click anywhere to begin!"** to start the 60-second round.

### Controls

| Input              | Action                          |
|--------------------|---------------------------------|
| **Left Mouse**     | Shoot / Click targets & buttons |
| **ESC**            | Pause / Resume                  |
| **Mouse Movement** | Aim with the crosshair          |

### Objective
Click as many targets as possible within **60 seconds** or before losing all **10 lives**.  
Build combos by hitting targets quickly to maximize your score multiplier.

---

## Gameplay Mechanics

### Targets
- Spawn at random positions (with padding from edges and the top HUD bar).
- Grow to a maximum radius of **25 px**, then shrink.
- Disappear if not clicked in time.
- Slight pulse animation for visual feedback.
- Spawn rate and growth speed depend on difficulty and increase over time.

### Scoring & Combos
- Each hit awards points equal to your current **multiplier**.
- Hitting targets within **0.5 seconds** of each other increases your combo and multiplier.
- Missing a target resets the multiplier to **×1** and costs one life.

### Lives
- You start with **10 lives**.
- Every miss (clicking outside a target) reduces lives by 1 and triggers a brief screen shake.
- Losing all lives ends the game early (**Game Over**).

### End Screen
Shows:
- Time played
- Total hits
- Total clicks
- Accuracy (%)
- Final score

You can **Restart** the same difficulty or **Quit** to the main menu.

---

## Difficulty Levels

| Difficulty | Spawn Interval | Growth Speed | Recommended For     |
|------------|----------------|--------------|---------------------|
| **Easy**   | 500 ms         | 0.2          | Beginners / Warm-up |
| **Medium** | 400 ms         | 0.3          | Intermediate        |
| **Hard**   | 300 ms         | 0.4          | Advanced players    |

> **Dynamic Scaling**: Target speed increases over the 60-second round:  
> `speed = base_speed × (1 + elapsed_time / 60)`

---

## Tips for High Scores

1. **Prioritize combos** – Quick successive hits give the biggest score boost.
2. **Click at peak size** – Targets are easiest to hit when fully grown (~25 px).
3. **Stay calm after misses** – A miss resets your multiplier; focus on precision to recover.
4. **Start on Easy** – Learn the rhythm before moving to Medium or Hard.
5. **Use a mouse** – A decent mouse (preferably with adjustable DPI) makes a big difference over a trackpad.

---

## Future Ideas

- High score saving / local leaderboard
- Sound effects and background music
- Additional game modes (unlimited time, moving targets, etc.)
- Custom crosshair settings
- More visual effects

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

## Credits

Built with ❤️ using [Pygame](https://www.pygame.org/).

Feel free to fork, improve, and share your high scores!  
If you enjoy the game, consider giving the repository a ⭐.
