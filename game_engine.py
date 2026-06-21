"""
Game Engine Module for Wumpus World Game
==========================================
Features:
- 4 difficulty levels (Explorer, Adventurer, Hero, Nightmare)
- Dynamic Wumpus movement on harder levels
- Clear goal system with win bonus
- Balanced scoring that rewards smart play
"""

import random
from typing import Dict, List
from knowledge_base import KnowledgeBase
from inference_engine import InferenceEngine
from percepts import PerceptManager
from agent import Agent
from score_visualization import ScoreManager, ConsoleVisualizer

# === LEVEL DEFINITIONS ===
LEVELS = {
    1: {
        "name": "Explorer",
        "description": "Learn the ropes — fewer pits, Wumpus stays still",
        "grid_size": 4,
        "max_pits": 1,
        "wumpus_moves": False,
        "gold_reward": 1000,
        "win_bonus": 500,
        "action_cost": 0,
        "icon": "🌿",
    },
    2: {
        "name": "Adventurer",
        "description": "Standard challenge — classic Wumpus World rules",
        "grid_size": 4,
        "max_pits": 2,
        "wumpus_moves": False,
        "gold_reward": 1000,
        "win_bonus": 300,
        "action_cost": -1,
        "icon": "⚔️",
    },
    3: {
        "name": "Hero",
        "description": "The Wumpus moves! More pits, bigger grid",
        "grid_size": 5,
        "max_pits": 3,
        "wumpus_moves": True,
        "gold_reward": 1500,
        "win_bonus": 500,
        "action_cost": -1,
        "icon": "🛡️",
    },
    4: {
        "name": "Nightmare",
        "description": "Maximum danger — large grid, many pits, moving Wumpus",
        "grid_size": 6,
        "max_pits": 5,
        "wumpus_moves": True,
        "gold_reward": 2000,
        "win_bonus": 1000,
        "action_cost": -2,
        "icon": "💀",
    },
}


class WumpusGame:
    """Main game controller that orchestrates all components."""

    def __init__(self, level: int = 1):
        self.level = max(1, min(level, 4))
        self.level_config = LEVELS[self.level]
        self.size = self.level_config["grid_size"]

        self.kb = KnowledgeBase(self.size, max_pits=self.level_config["max_pits"])
        self.percept_mgr = PerceptManager(self.kb)
        self.inference = InferenceEngine(self.kb)
        self.agent = Agent(self.kb, self.inference, self.percept_mgr)
        self.score_mgr = ScoreManager(
            action_cost=self.level_config["action_cost"],
            gold_reward=self.level_config["gold_reward"],
        )
        self.visualizer = ConsoleVisualizer(self.kb, self.agent, self.score_mgr)

        self.game_log: List[Dict] = []
        self.move_count = 0  # for Wumpus movement timing

        # Goal text
        self.goal = "Find the gold 💰, grab it, and escape from (0,0)!"

        self._process_starting_cell()

    def _process_starting_cell(self):
        percepts = self.percept_mgr.get_percepts(0, 0)
        self.inference.update_knowledge(0, 0, percepts)
        self._log_event("Game Started", {
            "position": (0, 0),
            "percepts": list(percepts),
            "message": f"Level {self.level}: {self.level_config['name']} — {self.goal}",
        })

    def reset(self):
        self.kb.reset()
        self.agent.reset()
        self.score_mgr.reset()
        self.game_log = []
        self.move_count = 0
        self._process_starting_cell()

    def _maybe_move_hazards(self):
        """Move the Wumpus, Gold, and Pits if the level allows it."""
        if not self.level_config["wumpus_moves"]:
            return
        # Earthquakes happen every 4 turns
        if self.move_count % 4 != 0 or self.move_count == 0:
            return

        all_valid_cells = [
            (r, c) for r in range(self.size) for c in range(self.size)
            if (r, c) != (self.agent.row, self.agent.col) and (r, c) not in [(0, 0), (0, 1), (1, 0)]
        ]
        
        if not all_valid_cells:
            return

        random.shuffle(all_valid_cells)
        
        # 1. Move Wumpus
        if self.kb.wumpus_alive:
            self.kb.wumpus_pos = all_valid_cells.pop()
        
        # 2. Move Gold
        if not self.kb.gold_picked and all_valid_cells:
            self.kb.gold_pos = all_valid_cells.pop()
            
        # 3. Move Pits
        num_pits = len(self.kb.pit_positions)
        self.kb.pit_positions.clear()
        for _ in range(min(num_pits, len(all_valid_cells))):
            self.kb.pit_positions.add(all_valid_cells.pop())

        # Reset agent's knowledge about the world since everything changed!
        self.kb.stench_cells.clear()
        self.kb.no_stench_cells.clear()
        self.kb.breeze_cells.clear()
        self.kb.no_breeze_cells.clear()
        self.kb.possible_wumpus.clear()
        self.kb.possible_pits.clear()
        self.kb.known_wumpus = None
        self.kb.known_pits.clear()
        
        # Keep visited safe cells, but anything dangerous might have moved there!
        # Actually, if a pit moves to a visited cell, the visited cell is no longer safe.
        # So we must clear visited cells that are not the current cell.
        curr_pos = (self.agent.row, self.agent.col)
        self.kb.visited = {curr_pos, (0, 0)}
        self.kb.safe_cells = {curr_pos, (0, 0)}
        self.kb.no_wumpus = {curr_pos, (0, 0)}
        self.kb.no_pit = {curr_pos, (0, 0)}

        # Re-check percepts at agent's current position
        self._log_event("World Shift", {
            "message": "🌍 EARTHQUAKE! The Wumpus, Gold, and Pits have all changed locations!!",
        })

    def move(self, direction: str) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}

        self.agent.direction = direction
        result = self.agent.move_forward()
        self.score_mgr.action_penalty("Move " + direction.capitalize())
        self.move_count += 1

        if result.get("death"):
            self.score_mgr.death_penalty(result["death"])
        else:
            self._maybe_move_hazards()
            # Re-check if Wumpus walked onto agent
            if self.kb.wumpus_alive and (self.agent.row, self.agent.col) == self.kb.wumpus_pos:
                self.agent.is_alive = False
                result["death"] = "wumpus"
                self.score_mgr.death_penalty("wumpus")
            # Re-check if agent is suddenly on a pit due to earthquake
            elif (self.agent.row, self.agent.col) in self.kb.pit_positions:
                self.agent.is_alive = False
                result["death"] = "pit"
                self.score_mgr.death_penalty("pit")

        self._log_event("Move", result)
        return self._build_response(result)

    def shoot(self, direction: str) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}
        result = self.agent.shoot_direction(direction)
        self.score_mgr.action_penalty("Shoot " + direction.capitalize())
        self.score_mgr.shoot_penalty()
        self._log_event("Shoot", result)
        return self._build_response(result)

    def grab(self) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}
        result = self.agent.grab_gold()
        self.score_mgr.action_penalty("Grab")
        if result.get("success"):
            self.score_mgr.gold_reward()
        self._log_event("Grab", result)
        return self._build_response(result)

    def climb(self) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}
        result = self.agent.climb_out()
        self.score_mgr.action_penalty("Climb")
        if result.get("success"):
            has_gold = self.agent.has_gold
            if has_gold:
                self.score_mgr.win_bonus(self.level_config["win_bonus"])
            self.score_mgr.climb_out(has_gold)
        self._log_event("Climb", result)
        return self._build_response(result)

    def auto_step(self) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}
        decision = self.agent.get_best_action()
        if decision["type"] == "move":
            t = decision["target"]
            return self.move_to(t[0], t[1])
        elif decision["type"] == "shoot":
            return self.shoot(decision["direction"])
        elif decision["type"] == "grab":
            return self.grab()
        elif decision["type"] == "climb":
            return self.climb()
        return {"error": "No action available"}

    def move_to(self, target_row: int, target_col: int) -> Dict:
        if self.score_mgr.game_over or not self.agent.is_alive:
            return {"error": "Game is over!", "game_over": True}
        dr = target_row - self.agent.row
        dc = target_col - self.agent.col
        if dr == 1: return self.move("up")
        elif dr == -1: return self.move("down")
        elif dc == 1: return self.move("right")
        elif dc == -1: return self.move("left")
        return {"error": "Invalid move target"}

    def get_state(self) -> Dict:
        current_percepts = list(
            self.percept_mgr.get_percepts(self.agent.row, self.agent.col)
        ) if self.agent.is_alive else []

        return {
            "grid_size": self.size,
            "level": self.level,
            "level_config": self.level_config,
            "goal": self.goal,
            "agent": self.agent.get_state(),
            "score": self.score_mgr.get_state(),
            "world": self.kb.get_world_state(),
            "knowledge": self.kb.get_agent_knowledge(),
            "current_percepts": current_percepts,
            "inference_log": self.inference.get_inference_log(),
            "game_log": self.game_log[-20:],
        }

    def _build_response(self, action_result: Dict) -> Dict:
        return {
            "action_result": {
                k: (list(v) if isinstance(v, set) else v)
                for k, v in action_result.items()
            },
            "state": self.get_state(),
        }

    def _log_event(self, event_type: str, data: Dict):
        safe_data = {}
        for k, v in data.items():
            safe_data[k] = list(v) if isinstance(v, set) else v
        self.game_log.append({
            "type": event_type,
            "step": self.score_mgr.actions_taken,
            "data": safe_data,
        })

    def console_play(self):
        print("Welcome to the Wumpus World!")
        print(f"Level: {self.level_config['name']} — {self.goal}")
        print("Commands: w/a/s/d, shoot <dir>, grab, climb, auto, quit")
        self.visualizer.print_world(reveal=False)
        while not self.score_mgr.game_over and self.agent.is_alive:
            cmd = input("\n> ").strip().lower()
            if cmd in ('q', 'quit'): break
            elif cmd == 'w': result = self.move("up")
            elif cmd == 's': result = self.move("down")
            elif cmd == 'a': result = self.move("left")
            elif cmd == 'd': result = self.move("right")
            elif cmd.startswith("shoot"):
                parts = cmd.split()
                result = self.shoot(parts[1] if len(parts) > 1 else self.agent.direction)
            elif cmd == 'grab': result = self.grab()
            elif cmd == 'climb': result = self.climb()
            elif cmd == 'auto': result = self.auto_step()
            elif cmd == 'reveal':
                self.visualizer.print_world(reveal=True)
                continue
            else:
                print("Unknown command!")
                continue
            if "error" in result:
                print(result["error"])
            else:
                ar = result.get("action_result", {})
                self.visualizer.print_action(ar)
                self.visualizer.print_world(reveal=False)
        print(f"\n{'='*40}")
        if self.score_mgr.won:
            print("🎉 YOU WIN!")
        elif not self.agent.is_alive:
            print(f"💀 YOU DIED! Cause: {self.score_mgr.death_cause}")
        print(f"Final Score: {self.score_mgr.score}")
        print("=" * 40)


if __name__ == "__main__":
    game = WumpusGame(level=1)
    game.console_play()
