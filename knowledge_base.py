"""
Knowledge Base Module for Wumpus World Game
============================================
Responsible for:
- Storing all rules and facts about the game world
- Randomizing positions of pits, gold, and Wumpus every game
- Maintaining the agent's knowledge about visited cells and inferred dangers
- Providing query interface for the inference engine
"""

import random
from typing import Dict, List, Set, Tuple, Optional


class KnowledgeBase:
    """
    The Knowledge Base stores all known facts about the Wumpus World.
    
    Facts include:
    - World layout (size)
    - Known positions of hazards (pits, Wumpus)
    - Known safe cells
    - Percepts received at each cell
    - Inferred knowledge (possible dangers, safe cells)
    """

    def __init__(self, size: int = 4, max_pits: int = 3):
        self.size = size
        self.grid_size = size
        self._max_pits = max_pits

        # === World State (Hidden from Agent) ===
        self.wumpus_pos: Tuple[int, int] = (0, 0)
        self.gold_pos: Tuple[int, int] = (0, 0)
        self.pit_positions: Set[Tuple[int, int]] = set()
        self.wumpus_alive: bool = True
        self.gold_picked: bool = False

        # === Agent Knowledge ===
        self.visited: Set[Tuple[int, int]] = set()
        self.safe_cells: Set[Tuple[int, int]] = set()
        self.possible_wumpus: Set[Tuple[int, int]] = set()
        self.possible_pits: Set[Tuple[int, int]] = set()
        self.no_wumpus: Set[Tuple[int, int]] = set()
        self.no_pit: Set[Tuple[int, int]] = set()
        self.known_wumpus: Optional[Tuple[int, int]] = None
        self.known_pits: Set[Tuple[int, int]] = set()

        # Percept history: maps (row, col) -> set of percept strings
        self.percept_history: Dict[Tuple[int, int], Set[str]] = {}

        # Stench and breeze locations
        self.stench_cells: Set[Tuple[int, int]] = set()
        self.breeze_cells: Set[Tuple[int, int]] = set()
        self.no_stench_cells: Set[Tuple[int, int]] = set()
        self.no_breeze_cells: Set[Tuple[int, int]] = set()

        # Initialize the world
        self._initialize_world()

    def _initialize_world(self):
        """
        Randomly place the Wumpus, Gold, and Pits on the grid.
        Rules:
        - Agent always starts at (0, 0)
        - No hazards at (0, 0)
        - Exactly 1 Wumpus
        - Exactly 1 Gold
        - Pits with probability ~0.2 per cell (excluding start)
        """
        all_cells = [
            (r, c) for r in range(self.size) for c in range(self.size)
            if (r, c) not in [(0, 0), (0, 1), (1, 0)]
        ]
        random.shuffle(all_cells)

        # Place Wumpus
        self.wumpus_pos = all_cells[0]

        # Place Gold (can be on same cell as Wumpus for classic rules)
        self.gold_pos = all_cells[1]

        # Place Pits with ~20% probability (excluding start, Wumpus, and Gold cells)
        self.pit_positions = set()
        for cell in all_cells[2:]:
            if random.random() < 0.2:
                self.pit_positions.add(cell)

        # Ensure at least 1 pit and at most 3 pits for balanced gameplay
        if len(self.pit_positions) == 0:
            # Add one pit
            remaining = [c for c in all_cells[2:]]
            if remaining:
                self.pit_positions.add(random.choice(remaining))

        while len(self.pit_positions) > self._max_pits:
            self.pit_positions.pop()

        # Mark starting position as safe and visited
        self.safe_cells.add((0, 0))
        self.no_wumpus.add((0, 0))
        self.no_pit.add((0, 0))

    def reset(self):
        """Reset the knowledge base for a new game."""
        self.wumpus_alive = True
        self.gold_picked = False
        self.visited.clear()
        self.safe_cells.clear()
        self.possible_wumpus.clear()
        self.possible_pits.clear()
        self.no_wumpus.clear()
        self.no_pit.clear()
        self.known_wumpus = None
        self.known_pits.clear()
        self.percept_history.clear()
        self.stench_cells.clear()
        self.breeze_cells.clear()
        self.no_stench_cells.clear()
        self.no_breeze_cells.clear()
        self._initialize_world()

    def get_adjacent_cells(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Return list of valid adjacent cells (up, down, left, right)."""
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                neighbors.append((nr, nc))
        return neighbors

    def mark_visited(self, row: int, col: int):
        """Mark a cell as visited."""
        self.visited.add((row, col))
        self.safe_cells.add((row, col))
        self.no_wumpus.add((row, col))
        self.no_pit.add((row, col))
        # Remove from possible dangers
        self.possible_wumpus.discard((row, col))
        self.possible_pits.discard((row, col))

    def record_percepts(self, row: int, col: int, percepts: Set[str]):
        """Record percepts received at a specific cell."""
        self.percept_history[(row, col)] = percepts

        if "Stench" in percepts:
            self.stench_cells.add((row, col))
        else:
            self.no_stench_cells.add((row, col))

        if "Breeze" in percepts:
            self.breeze_cells.add((row, col))
        else:
            self.no_breeze_cells.add((row, col))

    def mark_safe(self, row: int, col: int):
        """Mark a cell as definitely safe."""
        self.safe_cells.add((row, col))
        self.no_wumpus.add((row, col))
        self.no_pit.add((row, col))
        self.possible_wumpus.discard((row, col))
        self.possible_pits.discard((row, col))

    def mark_possible_wumpus(self, row: int, col: int):
        """Mark a cell as possibly containing the Wumpus."""
        if (row, col) not in self.no_wumpus and (row, col) not in self.visited:
            self.possible_wumpus.add((row, col))

    def mark_possible_pit(self, row: int, col: int):
        """Mark a cell as possibly containing a pit."""
        if (row, col) not in self.no_pit and (row, col) not in self.visited:
            self.possible_pits.add((row, col))

    def mark_no_wumpus(self, row: int, col: int):
        """Mark a cell as definitely NOT containing the Wumpus."""
        self.no_wumpus.add((row, col))
        self.possible_wumpus.discard((row, col))

    def mark_no_pit(self, row: int, col: int):
        """Mark a cell as definitely NOT containing a pit."""
        self.no_pit.add((row, col))
        self.possible_pits.discard((row, col))

    def mark_wumpus_dead(self):
        """Mark the Wumpus as dead."""
        self.wumpus_alive = False
        # All possible wumpus cells are now safe from wumpus
        if self.known_wumpus:
            self.no_wumpus.add(self.known_wumpus)
        for cell in list(self.possible_wumpus):
            self.no_wumpus.add(cell)
        self.possible_wumpus.clear()

    def mark_gold_picked(self):
        """Mark the gold as picked up."""
        self.gold_picked = True

    def is_cell_safe(self, row: int, col: int) -> bool:
        """Check if a cell is known to be safe."""
        return (row, col) in self.safe_cells

    def is_cell_dangerous(self, row: int, col: int) -> bool:
        """Check if a cell is known or suspected to be dangerous."""
        return (
            (row, col) in self.possible_wumpus or
            (row, col) in self.possible_pits or
            (row, col) in self.known_pits or
            (row, col) == self.known_wumpus
        )

    def get_unvisited_safe_cells(self) -> List[Tuple[int, int]]:
        """Get all cells that are known safe but not yet visited."""
        return [
            cell for cell in self.safe_cells
            if cell not in self.visited
        ]

    def get_world_state(self) -> Dict:
        """
        Return the complete world state (for visualization).
        This reveals hidden information — used only for rendering.
        """
        return {
            "size": self.size,
            "wumpus": self.wumpus_pos,
            "wumpus_alive": self.wumpus_alive,
            "gold": self.gold_pos,
            "gold_picked": self.gold_picked,
            "pits": list(self.pit_positions),
            "visited": list(self.visited),
            "safe_cells": list(self.safe_cells),
            "possible_wumpus": list(self.possible_wumpus),
            "possible_pits": list(self.possible_pits),
            "known_wumpus": self.known_wumpus,
            "known_pits": list(self.known_pits),
            "stench_cells": list(self.stench_cells),
            "breeze_cells": list(self.breeze_cells),
        }

    def get_agent_knowledge(self) -> Dict:
        """Return what the agent currently knows (no hidden info)."""
        return {
            "visited": list(self.visited),
            "safe_cells": list(self.safe_cells),
            "possible_wumpus": list(self.possible_wumpus),
            "possible_pits": list(self.possible_pits),
            "no_wumpus": list(self.no_wumpus),
            "no_pit": list(self.no_pit),
            "known_wumpus": self.known_wumpus,
            "known_pits": list(self.known_pits),
            "percept_history": {
                f"{r},{c}": list(p) for (r, c), p in self.percept_history.items()
            },
        }

    def __str__(self) -> str:
        """String representation of the knowledge base state."""
        lines = [
            f"=== Knowledge Base (Grid: {self.size}x{self.size}) ===",
            f"Wumpus at: {self.wumpus_pos} (Alive: {self.wumpus_alive})",
            f"Gold at: {self.gold_pos} (Picked: {self.gold_picked})",
            f"Pits at: {self.pit_positions}",
            f"Visited: {self.visited}",
            f"Safe cells: {self.safe_cells}",
            f"Possible Wumpus: {self.possible_wumpus}",
            f"Possible Pits: {self.possible_pits}",
        ]
        return "\n".join(lines)
