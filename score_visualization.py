"""
Score Updates Module for Wumpus World Game
============================================
Responsible for:
- Tracking and updating the game score
- Implementing scoring rules (configurable per level)
- Managing game state (win/lose/ongoing)
- Console visualization of the world
"""

from typing import Dict, List, Tuple
from knowledge_base import KnowledgeBase
from agent import Agent


class ScoreManager:
    """
    Manages the game score and state.
    
    Scoring Rules:
    - Each action: configurable (default -1 for medium, 0 for easy)
    - Shooting an arrow: -10 points
    - Dying (Wumpus or Pit): -1000 points
    - Picking up gold: configurable (1000-2000 depending on level)
    - Climbing out with gold: Win bonus!
    """

    SHOOT_COST = -10
    DEATH_PENALTY = -1000

    def __init__(self, action_cost: int = -1, gold_reward: int = 1000):
        self.ACTION_COST = action_cost
        self.GOLD_REWARD = gold_reward
        self.score: int = 0
        self.actions_taken: int = 0
        self.game_over: bool = False
        self.won: bool = False
        self.death_cause: str = ""
        self.score_history: List[Dict] = []

    def reset(self):
        """Reset score for a new game."""
        self.score = 0
        self.actions_taken = 0
        self.game_over = False
        self.won = False
        self.death_cause = ""
        self.score_history = []

    def action_penalty(self, action: str):
        """Apply penalty for taking an action."""
        self.score += self.ACTION_COST
        self.actions_taken += 1
        self._record(action, self.ACTION_COST)

    def shoot_penalty(self):
        """Apply penalty for shooting an arrow."""
        self.score += self.SHOOT_COST
        self._record("Shoot Arrow", self.SHOOT_COST)

    def death_penalty(self, cause: str):
        """Apply penalty for dying."""
        self.score += self.DEATH_PENALTY
        self.game_over = True
        self.won = False
        self.death_cause = cause
        self._record(f"Death ({cause})", self.DEATH_PENALTY)

    def gold_reward(self):
        """Apply reward for picking up gold."""
        self.score += self.GOLD_REWARD
        self._record("Pick Up Gold", self.GOLD_REWARD)

    def win_bonus(self, bonus: int):
        """Apply bonus for winning (escaping with gold)."""
        self.score += bonus
        self._record("Victory Bonus! 🎉", bonus)

    def climb_out(self, has_gold: bool):
        """Handle climbing out of the cave."""
        self.game_over = True
        self.won = has_gold
        self._record("Climb Out", 0)

    def _record(self, action: str, points: int):
        self.score_history.append({
            "action": action,
            "points": points,
            "total": self.score,
            "step": self.actions_taken,
        })

    def get_score(self) -> int:
        return self.score

    def get_state(self) -> Dict:
        return {
            "score": self.score,
            "actions_taken": self.actions_taken,
            "game_over": self.game_over,
            "won": self.won,
            "death_cause": self.death_cause,
            "history": self.score_history,
        }


class ConsoleVisualizer:
    """Console-based visualization of the Wumpus World."""

    def __init__(self, kb: KnowledgeBase, agent: Agent, score_mgr: ScoreManager):
        self.kb = kb
        self.agent = agent
        self.score_mgr = score_mgr

    def render(self, reveal: bool = False) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("    W U M P U S    W O R L D")
        lines.append("=" * 60)
        size = self.kb.size
        for row in range(size - 1, -1, -1):
            lines.append("+" + "--------+" * size)
            cell_lines = [[] for _ in range(3)]
            for col in range(size):
                content = self._get_cell_content(row, col, reveal)
                for i in range(3):
                    if i < len(content):
                        cell_lines[i].append(f" {content[i]:^6} ")
                    else:
                        cell_lines[i].append("        ")
            for cl in cell_lines:
                lines.append("|" + "|".join(cl) + "|")
        lines.append("+" + "--------+" * size)
        lines.append("")
        lines.append(f"Agent: ({self.agent.row}, {self.agent.col}) | Dir: {self.agent.direction}")
        lines.append(f"Arrow: {self.agent.has_arrow} | Gold: {self.agent.has_gold}")
        lines.append(f"Score: {self.score_mgr.score} | Actions: {self.score_mgr.actions_taken}")
        return "\n".join(lines)

    def _get_cell_content(self, row: int, col: int, reveal: bool) -> List[str]:
        content = []
        if (row, col) == (self.agent.row, self.agent.col):
            arrows = {"up": "↑", "down": "↓", "left": "←", "right": "→"}
            content.append(f"🤖{arrows[self.agent.direction]}")
        elif (row, col) in self.kb.visited:
            content.append("·····")
        else:
            content.append("     ")

        if reveal or (row, col) in self.kb.visited:
            items = []
            if (row, col) == self.kb.wumpus_pos and self.kb.wumpus_alive: items.append("W")
            if (row, col) == self.kb.gold_pos and not self.kb.gold_picked: items.append("G")
            if (row, col) in self.kb.pit_positions: items.append("P")
            content.append("".join(items) if items else "")
        else:
            content.append("???")

        if (row, col) in self.kb.percept_history:
            percepts = self.kb.percept_history[(row, col)]
            syms = []
            if "Stench" in percepts: syms.append("S")
            if "Breeze" in percepts: syms.append("B")
            if "Glitter" in percepts: syms.append("G")
            content.append("".join(syms) if syms else "")
        else:
            content.append("")
        return content

    def print_world(self, reveal=False):
        print(self.render(reveal))

    def print_percepts(self, percepts: set):
        if not percepts: print("Percepts: [None]")
        else: print(f"Percepts: [{', '.join(sorted(percepts))}]")

    def print_action(self, result: dict):
        print(f"Action: {result.get('action', 'Unknown')}")
        if 'direction' in result: print(f"Direction: {result['direction']}")
        print(f"Position: ({self.agent.row}, {self.agent.col})")
        if result.get('percepts'): self.print_percepts(result['percepts'])
        if result.get('message'): print(f">> {result['message']}")
        print(f"Score: {self.score_mgr.score}")
        print("-" * 40)
