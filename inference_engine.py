"""
Inference Engine Module for Wumpus World Game
===============================================
Responsible for:
- Inferring new facts from percepts and existing knowledge
- Updating the Knowledge Base with derived information
- Implementing logical reasoning rules for the Wumpus World
- Determining safe vs dangerous cells based on evidence
"""

from typing import Set, Tuple, List
from knowledge_base import KnowledgeBase


class InferenceEngine:
    """
    The Inference Engine applies logical rules to derive new knowledge
    from percepts and existing facts in the Knowledge Base.
    
    Key inference rules:
    1. If no stench at a cell -> all adjacent cells have no Wumpus
    2. If no breeze at a cell -> all adjacent cells have no pit
    3. If stench at a cell -> at least one adjacent cell may have Wumpus
    4. If breeze at a cell -> at least one adjacent cell may have a pit
    5. Model checking for definitive conclusions
    """

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def update_knowledge(self, agent_row: int, agent_col: int, percepts: Set[str]):
        """
        Main inference method. Called after agent moves to a new cell.
        Updates the knowledge base based on received percepts.
        
        Args:
            agent_row: Current agent row
            agent_col: Current agent column
            percepts: Set of percept strings received at this cell
        """
        # Mark current cell as visited and safe
        self.kb.mark_visited(agent_row, agent_col)

        # Record percepts
        self.kb.record_percepts(agent_row, agent_col, percepts)

        # Get adjacent cells
        neighbors = self.kb.get_adjacent_cells(agent_row, agent_col)

        # === Rule 1: No Stench -> All neighbors are safe from Wumpus ===
        if "Stench" not in percepts:
            for nr, nc in neighbors:
                self.kb.mark_no_wumpus(nr, nc)

        # === Rule 2: No Breeze -> All neighbors are safe from pits ===
        if "Breeze" not in percepts:
            for nr, nc in neighbors:
                self.kb.mark_no_pit(nr, nc)

        # === Rule 3: Stench -> Adjacent unvisited cells might have Wumpus ===
        if "Stench" in percepts and self.kb.wumpus_alive:
            for nr, nc in neighbors:
                if (nr, nc) not in self.kb.visited:
                    self.kb.mark_possible_wumpus(nr, nc)

        # === Rule 4: Breeze -> Adjacent unvisited cells might have pits ===
        if "Breeze" in percepts:
            for nr, nc in neighbors:
                if (nr, nc) not in self.kb.visited:
                    self.kb.mark_possible_pit(nr, nc)

        # === Apply advanced inference ===
        self._infer_definite_wumpus()
        self._infer_definite_pits()
        self._update_safe_cells()

        # === Handle Scream ===
        if "Scream" in percepts:
            self.kb.mark_wumpus_dead()

    def _infer_definite_wumpus(self):
        """
        If there's only one possible cell left for the Wumpus,
        it must be there (definitive inference).
        """
        if self.kb.known_wumpus is not None:
            return

        # Remove cells that are now known to be safe
        self.kb.possible_wumpus -= self.kb.no_wumpus
        self.kb.possible_wumpus -= self.kb.visited

        # If only one possibility remains, it's definitely the Wumpus
        if len(self.kb.possible_wumpus) == 1:
            wumpus_cell = next(iter(self.kb.possible_wumpus))
            self.kb.known_wumpus = wumpus_cell

            # All other cells are safe from Wumpus
            for r in range(self.kb.size):
                for c in range(self.kb.size):
                    if (r, c) != wumpus_cell:
                        self.kb.mark_no_wumpus(r, c)

        # Cross-referencing: if stench cells share only one common neighbor
        if self.kb.known_wumpus is None and len(self.kb.stench_cells) >= 2:
            common_neighbors = None
            for sr, sc in self.kb.stench_cells:
                adj = set(self.kb.get_adjacent_cells(sr, sc))
                # Only consider unvisited cells
                adj = adj - self.kb.visited - self.kb.no_wumpus
                if common_neighbors is None:
                    common_neighbors = adj
                else:
                    common_neighbors = common_neighbors & adj

            if common_neighbors and len(common_neighbors) == 1:
                wumpus_cell = next(iter(common_neighbors))
                self.kb.known_wumpus = wumpus_cell
                self.kb.possible_wumpus = {wumpus_cell}
                for r in range(self.kb.size):
                    for c in range(self.kb.size):
                        if (r, c) != wumpus_cell:
                            self.kb.mark_no_wumpus(r, c)

    def _infer_definite_pits(self):
        """
        For each breeze cell, if all but one neighbor is known safe,
        the remaining neighbor must be a pit.
        """
        for br, bc in list(self.kb.breeze_cells):
            neighbors = self.kb.get_adjacent_cells(br, bc)
            unknown = [
                (nr, nc) for nr, nc in neighbors
                if (nr, nc) not in self.kb.no_pit and (nr, nc) not in self.kb.visited
            ]

            # If exactly one unknown neighbor, it must be a pit
            if len(unknown) == 1:
                pit_cell = unknown[0]
                self.kb.known_pits.add(pit_cell)
                self.kb.possible_pits.discard(pit_cell)

        # Remove known-safe cells from possible pits
        self.kb.possible_pits -= self.kb.no_pit
        self.kb.possible_pits -= self.kb.visited

    def _update_safe_cells(self):
        """
        Mark cells as safe if they're known to have neither Wumpus nor pit.
        """
        for r in range(self.kb.size):
            for c in range(self.kb.size):
                if (r, c) in self.kb.no_wumpus and (r, c) in self.kb.no_pit:
                    self.kb.mark_safe(r, c)

    def is_safe_to_move(self, row: int, col: int) -> bool:
        """Check if a cell is safe to move to based on current knowledge."""
        return self.kb.is_cell_safe(row, col)

    def get_safe_moves(self, agent_row: int, agent_col: int) -> List[Tuple[int, int]]:
        """Get list of adjacent cells that are known to be safe."""
        neighbors = self.kb.get_adjacent_cells(agent_row, agent_col)
        return [
            (nr, nc) for nr, nc in neighbors
            if self.kb.is_cell_safe(nr, nc)
        ]

    def get_risky_moves(self, agent_row: int, agent_col: int) -> List[Tuple[int, int]]:
        """Get list of adjacent cells that are risky (possible danger)."""
        neighbors = self.kb.get_adjacent_cells(agent_row, agent_col)
        return [
            (nr, nc) for nr, nc in neighbors
            if not self.kb.is_cell_safe(nr, nc) and (nr, nc) not in self.kb.visited
        ]

    def should_shoot(self, agent_row: int, agent_col: int, direction: str) -> bool:
        """
        Determine if the agent should shoot an arrow in a given direction.
        Returns True if the target cell is known or highly suspected to have the Wumpus.
        """
        dr, dc = {
            "up": (1, 0), "down": (-1, 0),
            "left": (0, -1), "right": (0, 1)
        }.get(direction, (0, 0))

        target_row, target_col = agent_row + dr, agent_col + dc

        if not (0 <= target_row < self.kb.size and 0 <= target_col < self.kb.size):
            return False

        # Shoot if we know the Wumpus is there
        if self.kb.known_wumpus == (target_row, target_col):
            return True

        # Shoot if it's a strong suspect and we have the arrow
        if (target_row, target_col) in self.kb.possible_wumpus:
            if len(self.kb.possible_wumpus) <= 2:
                return True

        return False

    def get_inference_log(self) -> List[str]:
        """Return a human-readable log of current inferences."""
        log = []
        if self.kb.known_wumpus:
            log.append(f"🎯 Wumpus definitively located at {self.kb.known_wumpus}")
        elif self.kb.possible_wumpus:
            log.append(f"🔍 Possible Wumpus locations: {self.kb.possible_wumpus}")

        if self.kb.known_pits:
            log.append(f"⚠️ Confirmed pits at: {self.kb.known_pits}")
        if self.kb.possible_pits:
            log.append(f"🔍 Possible pit locations: {self.kb.possible_pits}")

        safe_unvisited = self.kb.get_unvisited_safe_cells()
        if safe_unvisited:
            log.append(f"✅ Safe unvisited cells: {safe_unvisited}")

        return log
