"""
Percepts Module for Wumpus World Game
======================================
Responsible for:
- Generating percepts based on the agent's current position
- Implementing all five senses: Stench, Breeze, Glitter, Bump, Scream
- Providing the agent with environmental information
"""

from typing import Set, Tuple
from knowledge_base import KnowledgeBase


class PerceptManager:
    """
    Manages the generation of percepts in the Wumpus World.
    
    Percepts:
    - Stench: Adjacent to Wumpus (up, down, left, right)
    - Breeze: Adjacent to a pit
    - Glitter: In the same cell as the gold
    - Bump: Agent tried to move outside the grid
    - Scream: Wumpus was just killed by an arrow
    """

    def __init__(self, kb: KnowledgeBase):
        self.kb = kb

    def get_percepts(self, agent_row: int, agent_col: int,
                     bump: bool = False, scream: bool = False) -> Set[str]:
        """
        Generate the set of percepts for the agent at the given position.
        
        Args:
            agent_row: Current row of the agent
            agent_col: Current column of the agent
            bump: Whether the agent bumped into a wall
            scream: Whether the Wumpus was just killed
            
        Returns:
            Set of percept strings
        """
        percepts = set()

        # Check for Stench (adjacent to living Wumpus)
        if self.sense_stench(agent_row, agent_col):
            percepts.add("Stench")

        # Check for Breeze (adjacent to pit)
        if self.sense_breeze(agent_row, agent_col):
            percepts.add("Breeze")

        # Check for Glitter (same cell as gold)
        if self.sense_glitter(agent_row, agent_col):
            percepts.add("Glitter")

        # Check for Bump (tried to move outside grid)
        if bump:
            percepts.add("Bump")

        # Check for Scream (Wumpus just killed)
        if scream:
            percepts.add("Scream")

        return percepts

    def sense_stench(self, row: int, col: int) -> bool:
        """
        Check if the agent senses a stench at position (row, col).
        Stench is perceived when adjacent to the Wumpus (alive).
        """
        if not self.kb.wumpus_alive:
            return False

        wumpus_row, wumpus_col = self.kb.wumpus_pos
        neighbors = self.kb.get_adjacent_cells(wumpus_row, wumpus_col)

        return (row, col) in neighbors or (row, col) == self.kb.wumpus_pos

    def sense_breeze(self, row: int, col: int) -> bool:
        """
        Check if the agent senses a breeze at position (row, col).
        Breeze is perceived when adjacent to a pit.
        """
        for pit_row, pit_col in self.kb.pit_positions:
            neighbors = self.kb.get_adjacent_cells(pit_row, pit_col)
            if (row, col) in neighbors or (row, col) == (pit_row, pit_col):
                return True
        return False

    def sense_glitter(self, row: int, col: int) -> bool:
        """
        Check if the agent senses glitter at position (row, col).
        Glitter is perceived when on the same cell as the gold.
        """
        if self.kb.gold_picked:
            return False
        return (row, col) == self.kb.gold_pos

    def sense_bump(self, row: int, col: int, direction: str) -> bool:
        """
        Check if the agent would bump into a wall.
        
        Args:
            row: Current row
            col: Current column
            direction: Direction of attempted movement
            
        Returns:
            True if moving in that direction would cause a bump
        """
        if direction == "up" and row >= self.kb.size - 1:
            return True
        if direction == "down" and row <= 0:
            return True
        if direction == "right" and col >= self.kb.size - 1:
            return True
        if direction == "left" and col <= 0:
            return True
        return False

    def check_death(self, row: int, col: int) -> str:
        """
        Check if the agent dies at the given position.
        
        Returns:
            "wumpus" if killed by Wumpus,
            "pit" if fell into pit,
            "" if safe
        """
        # Check for Wumpus
        if self.kb.wumpus_alive and (row, col) == self.kb.wumpus_pos:
            return "wumpus"

        # Check for Pit
        if (row, col) in self.kb.pit_positions:
            return "pit"

        return ""

    def get_percept_symbols(self, percepts: Set[str]) -> dict:
        """
        Return emoji/symbol representations of percepts for visualization.
        """
        symbols = {
            "Stench": "💨",
            "Breeze": "🌬️",
            "Glitter": "✨",
            "Bump": "🧱",
            "Scream": "😱",
        }
        return {p: symbols.get(p, "?") for p in percepts}

    def describe_percepts(self, percepts: Set[str]) -> str:
        """Return a human-readable description of the percepts."""
        if not percepts:
            return "You perceive nothing unusual. The cell seems safe."

        descriptions = {
            "Stench": "You smell a terrible stench! The Wumpus is nearby...",
            "Breeze": "You feel a light breeze. There might be a pit nearby!",
            "Glitter": "Something is glittering on the ground! It's GOLD!",
            "Bump": "Ouch! You bumped into a wall!",
            "Scream": "You hear a blood-curdling scream! The Wumpus is dead!",
        }
        return " | ".join(descriptions.get(p, p) for p in sorted(percepts))
