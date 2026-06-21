<div align="center">
  <h1>🧠 Wumpus World AI: The Dynamic Edition 🎮</h1>
  <p>A comprehensive, highly dynamic, and visually stunning implementation of the classic Artificial Intelligence problem <b>"Wumpus World"</b>, powered by an advanced Knowledge-Based Autonomous Agent.</p>

  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
  [![Flask](https://img.shields.io/badge/Flask-Backend-lightgrey.svg)](https://flask.palletsprojects.com/)
  [![UI/UX](https://img.shields.io/badge/UI/UX-Glassmorphism-purple.svg)]()
</div>

<hr>

## 📖 What is Wumpus World?
Wumpus World is a classic AI problem where an agent must navigate a dark cave represented by a grid. The cave contains a deadly monster (the **Wumpus**), bottomless **Pits**, and a hidden bar of **Gold**. The agent cannot "see" the grid; it can only sense its immediate surroundings (Percepts). The goal is to find the gold, grab it, and safely climb out of the cave without dying.

### 🕵️‍♂️ Percepts (The Agent's Senses)
*   💨 **Stench:** The Wumpus is in an adjacent square (up, down, left, or right).
*   🌬️ **Breeze:** A deadly Pit is in an adjacent square.
*   ✨ **Glitter:** The Gold is in the current square.
*   🧱 **Bump:** The Agent tried to walk into a wall.
*   😱 **Scream:** The Agent successfully shot and killed the Wumpus.

---

## ✨ Unique Features of This Project

This project takes the classic Wumpus World and elevates it into a modern, dynamic web game:

*   **🌍 Dynamic Hazards (The Earthquake Mechanic):** In classic Wumpus World, hazards are static. In our *Hero* and *Nightmare* difficulty levels, the world is alive! Periodically, an **Earthquake** occurs, randomizing the locations of the Wumpus, Pits, and Gold. The AI must instantly discard its old knowledge and recalculate everything on the fly!
*   **🤖 Advanced Autonomous AI:** The agent does not move randomly. It uses a Knowledge Base to make logical deductions, **Breadth-First Search (BFS)** for 100% safe pathfinding, and memory buffers to detect and break out of infinite loops.
*   **🎨 Stunning Visuals & Animations:** A premium, fully responsive UI built with vanilla CSS3 and JS. Features glassmorphism, dynamic particle effects, screen shakes during earthquakes, confetti celebrations, and smooth cell-reveal transitions.
*   **📈 4 Difficulty Levels:** From "Explorer" (4x4 grid, static) to "Nightmare" (6x6 grid, up to 5 pits, constantly moving hazards, heavily penalized actions).
*   **👁️ Analytics Dashboard:** Real-time visibility into the Agent's "brain" (Knowledge Base), current Percepts, Action History, and Score tracking.

---

## 🧠 The Agent's Brain (Architecture)

The AI is built on a strictly decoupled architecture, mimicking a real AI system:

### 1. Knowledge Base (KB)
The KB stores everything the agent *knows for sure*. It tracks visited cells, safe cells, possible Wumpus locations, and possible Pit locations. When an Earthquake happens, the KB is wiped clean, leaving only the agent's current cell as a known safe spot.

### 2. Inference Engine
The "Thinker". Whenever the agent receives percepts, the Inference Engine updates the KB using propositional logic. 
* *Example:* If I feel a Breeze, then the 4 adjacent cells are added to "Possible Pits". If I visit one of those cells later and feel NO Breeze, the Inference Engine deduces that cell is safe, updating the KB.

### 3. Action Priority Logic
When evaluating its next move, the Agent follows a strict hierarchy of priorities:
1.  **Grab Gold:** If standing on the gold, grab it immediately.
2.  **Escape:** If holding the gold and at `(0,0)`, climb out and win.
3.  **Navigate Home:** If holding the gold but not at `(0,0)`, use BFS to find the shortest *guaranteed safe* path back to the start.
4.  **Tactical Shooting:** If the Wumpus's exact location is deduced and the agent is aligned with it, shoot the arrow.
5.  **Safe Exploration:** Use BFS to navigate to the nearest unvisited, 100% safe cell. (Uses a rolling buffer to avoid looping between the same safe cells).
6.  **Hunting:** If the Wumpus location is known but not in line of sight, navigate to a safe cell that aligns with the Wumpus.
7.  **Calculated Risk:** If there are NO guaranteed safe cells left (or the agent is trapped), it evaluates adjacent unknown cells. It calculates a `danger_score` (e.g., a possible pit is less dangerous than a known Wumpus) and steps into the least dangerous cell.

---

## 🏆 Scoring System
The AI is penalized for inefficiency to encourage optimal pathfinding:
*   **Action Cost:** -1 point per move/turn (increases to -2 in Nightmare mode).
*   **Shoot Arrow:** -10 points.
*   **Death (Pit/Wumpus):** -1000 points (Game Over).
*   **Find Gold:** +1000 to +2000 points (depending on difficulty).
*   **Win Bonus (Climbing out with Gold):** +300 to +1000 points.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python installed (3.8+ recommended). The only backend dependency is `Flask`.

```bash
pip install flask
```

### Running the Game
1. Clone the repository:
```bash
git clone https://github.com/YourUsername/wumpus-world-ai.git
cd wumpus-world-ai
```
2. Start the backend server:
```bash
python server.py
```
3. Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

## 🎮 How to Play
*   **Auto Play Mode:** Click the `🤖 Auto Play` button to let the AI take the wheel. Watch the game log and the KB monitor to see how it thinks!
*   **Manual Mode:** Use the keyboard (`W, A, S, D` or `Arrow Keys`) to move manually. Press `G` to Grab, `F` to Shoot, and `C` to Climb.
*   **Toggle Map:** Click `👁️ Reveal Map` to see all hidden hazards and watch the AI navigate blindly!

<hr>
<div align="center">
  <i>Developed to showcase Advanced Agentic AI and Full-Stack Engineering.</i>
</div>
