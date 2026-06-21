"""
Agent Function Module for Wumpus World Game
=============================================
Responsible for:
- Implementing all agent actions (Move, Turn, Shoot, Grab, Climb)
- Managing agent state (position, direction, arrow, gold)
- Providing both manual (player-controlled) and AI (auto) modes
- Smart BFS-based pathfinding to avoid loops
"""

from typing import Tuple, Optional, List, Dict, Set
from collections import deque
from knowledge_base import KnowledgeBase
from inference_engine import InferenceEngine
from percepts import PerceptManager


class Agent:
    """
    The Agent navigates the Wumpus World, using percepts and inference
    to make decisions about movement, shooting, and grabbing gold.
    """

    DIR_DELTA = {
        "up": (1, 0),
        "down": (-1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    def __init__(self, kb: KnowledgeBase, inference: InferenceEngine,
                 percept_mgr: PerceptManager):
        self.kb = kb
        self.inference = inference
        self.percept_mgr = percept_mgr

        # Agent state
        self.row: int = 0
        self.col: int = 0
        self.direction: str = "right"
        self.has_arrow: bool = True
        self.has_gold: bool = False
        self.is_alive: bool = True
        self.has_climbed: bool = False

        # Path tracking
        self.path: List[Tuple[int, int]] = [(0, 0)]
        self.action_history: List[Dict] = []
        # Loop detection: track recent positions to break cycles
        self._recent_positions: List[Tuple[int, int]] = []
        self._max_recent = 12

    def reset(self):
        """Reset agent to initial state."""
        self.row = 0
        self.col = 0
        self.direction = "right"
        self.has_arrow = True
        self.has_gold = False
        self.is_alive = True
        self.has_climbed = False
        self.path = [(0, 0)]
        self.action_history = []
        self._recent_positions = []

    def get_position(self) -> Tuple[int, int]:
        return (self.row, self.col)

    def move_forward(self) -> Dict:
        """Move the agent one step in the current direction."""
        dr, dc = self.DIR_DELTA[self.direction]
        new_row = self.row + dr
        new_col = self.col + dc
        bump = False

        if not (0 <= new_row < self.kb.size and 0 <= new_col < self.kb.size):
            bump = True
            new_row, new_col = self.row, self.col
        else:
            self.row = new_row
            self.col = new_col
            self.path.append((self.row, self.col))

        percepts = self.percept_mgr.get_percepts(self.row, self.col, bump=bump)
        death_cause = self.percept_mgr.check_death(self.row, self.col)
        if death_cause:
            self.is_alive = False

        if self.is_alive:
            self.inference.update_knowledge(self.row, self.col, percepts)

        # Track for loop detection
        self._recent_positions.append((self.row, self.col))
        if len(self._recent_positions) > self._max_recent:
            self._recent_positions.pop(0)

        result = {
            "action": "Move Forward",
            "direction": self.direction,
            "position": (self.row, self.col),
            "percepts": percepts,
            "bump": bump,
            "death": death_cause,
            "alive": self.is_alive,
        }
        self.action_history.append(result)
        return result

    def move_to(self, target_row: int, target_col: int) -> Dict:
        """Move the agent to an adjacent cell directly."""
        dr = target_row - self.row
        dc = target_col - self.col
        if dr == 1: self.direction = "up"
        elif dr == -1: self.direction = "down"
        elif dc == 1: self.direction = "right"
        elif dc == -1: self.direction = "left"
        return self.move_forward()

    def turn_left(self) -> Dict:
        dirs = ["up", "right", "down", "left"]
        idx = dirs.index(self.direction)
        self.direction = dirs[(idx - 1) % 4]
        result = {"action": "Turn Left", "direction": self.direction,
                  "position": (self.row, self.col), "percepts": set()}
        self.action_history.append(result)
        return result

    def turn_right(self) -> Dict:
        dirs = ["up", "right", "down", "left"]
        idx = dirs.index(self.direction)
        self.direction = dirs[(idx + 1) % 4]
        result = {"action": "Turn Right", "direction": self.direction,
                  "position": (self.row, self.col), "percepts": set()}
        self.action_history.append(result)
        return result

    def shoot_arrow(self) -> Dict:
        """Shoot an arrow in the current direction."""
        scream = False
        if not self.has_arrow:
            result = {"action": "Shoot (No Arrow)", "direction": self.direction,
                      "position": (self.row, self.col), "percepts": set(),
                      "hit": False, "message": "No arrow left!"}
            self.action_history.append(result)
            return result

        self.has_arrow = False
        dr, dc = self.DIR_DELTA[self.direction]
        ar, ac = self.row + dr, self.col + dc
        while 0 <= ar < self.kb.size and 0 <= ac < self.kb.size:
            if self.kb.wumpus_alive and (ar, ac) == self.kb.wumpus_pos:
                scream = True
                self.kb.mark_wumpus_dead()
                break
            ar += dr
            ac += dc

        percepts = self.percept_mgr.get_percepts(self.row, self.col, scream=scream)
        if scream:
            percepts.add("Scream")
        self.inference.update_knowledge(self.row, self.col, percepts)

        result = {"action": "Shoot Arrow", "direction": self.direction,
                  "position": (self.row, self.col), "percepts": percepts,
                  "hit": scream,
                  "message": "You killed the Wumpus!" if scream else "Arrow missed..."}
        self.action_history.append(result)
        return result

    def shoot_direction(self, direction: str) -> Dict:
        self.direction = direction
        return self.shoot_arrow()

    def grab_gold(self) -> Dict:
        success = ((self.row, self.col) == self.kb.gold_pos and not self.kb.gold_picked)
        if success:
            self.has_gold = True
            self.kb.mark_gold_picked()
        result = {"action": "Grab Gold", "position": (self.row, self.col),
                  "percepts": set(), "success": success,
                  "message": "You picked up the gold! 🏆" if success else "No gold here."}
        self.action_history.append(result)
        return result

    def climb_out(self) -> Dict:
        success = (self.row == 0 and self.col == 0)
        if success:
            self.has_climbed = True
        result = {"action": "Climb Out", "position": (self.row, self.col),
                  "percepts": set(), "success": success,
                  "message": "You escaped the cave!" if success else "You can only climb at (0,0)!"}
        self.action_history.append(result)
        return result

    # ===== SMART AI AGENT LOGIC =====

    def _is_looping(self) -> bool:
        """Detect if agent is stuck in a loop (same 2-3 cells repeating)."""
        if len(self._recent_positions) < 6:
            return False
        last6 = self._recent_positions[-6:]
        unique = set(last6)
        return len(unique) <= 2

    def _bfs_path(self, start: Tuple[int, int], goal: Tuple[int, int],
                  safe_only: bool = True) -> List[Tuple[int, int]]:
        """BFS to find shortest path through safe (or all) cells."""
        if start == goal:
            return [start]
        queue = deque([(start, [start])])
        visited = {start}
        while queue:
            (r, c), path = queue.popleft()
            for nr, nc in self.kb.get_adjacent_cells(r, c):
                if (nr, nc) in visited:
                    continue
                if safe_only and not self.kb.is_cell_safe(nr, nc):
                    continue
                if not safe_only:
                    if (nr, nc) in self.kb.known_pits or (nr, nc) == self.kb.known_wumpus:
                        continue
                new_path = path + [(nr, nc)]
                if (nr, nc) == goal:
                    return new_path
                visited.add((nr, nc))
                queue.append(((nr, nc), new_path))
        return []

    def _bfs_to_nearest(self, start: Tuple[int, int],
                        targets: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """BFS to find shortest safe path to any of the target cells."""
        if start in targets:
            return [start]
        queue = deque([(start, [start])])
        visited = {start}
        while queue:
            (r, c), path = queue.popleft()
            for nr, nc in self.kb.get_adjacent_cells(r, c):
                if (nr, nc) in visited:
                    continue
                if not self.kb.is_cell_safe(nr, nc):
                    continue
                new_path = path + [(nr, nc)]
                if (nr, nc) in targets:
                    return new_path
                visited.add((nr, nc))
                queue.append(((nr, nc), new_path))
        return []

    def get_best_action(self) -> Dict:
        """
        AI Agent: Smart decision making with BFS pathfinding.
        Priority:
        1. Grab gold if standing on it
        2. Climb out if has gold and at (0,0)
        3. Navigate home if has gold
        4. Shoot if Wumpus location is known and in line of sight
        5. BFS to nearest safe unvisited cell
        6. Navigate to shoot Wumpus if known but not in line of sight
        7. Take calculated risk on unknown cells
        8. Give up and climb out
        """
        pos = (self.row, self.col)

        # 1. Grab gold if here
        if pos == self.kb.gold_pos and not self.kb.gold_picked:
            return {"type": "grab"}

        # 2. Climb out with gold at start
        if self.has_gold and pos == (0, 0):
            return {"type": "climb"}

        # 3. Navigate home with gold
        if self.has_gold:
            path = self._bfs_path(pos, (0, 0))
            if path and len(path) > 1:
                return {"type": "move", "target": path[1]}
            # fallback direct navigation
            return self._step_toward(0, 0)

        # 4. Shoot if Wumpus known and in line of sight
        if self.has_arrow and self.kb.known_wumpus and self.kb.wumpus_alive:
            wr, wc = self.kb.known_wumpus
            shot_dir = self._get_shot_direction(wr, wc)
            if shot_dir:
                return {"type": "shoot", "direction": shot_dir}

        # 5. BFS to nearest safe unvisited cell
        safe_unvisited = set(self.kb.get_unvisited_safe_cells())
        if safe_unvisited:
            # If looping, exclude recently visited cells from preference
            if self._is_looping():
                recent_set = set(self._recent_positions[-6:])
                better = safe_unvisited - recent_set
                targets = better if better else safe_unvisited
            else:
                targets = safe_unvisited

            path = self._bfs_to_nearest(pos, targets)
            if path and len(path) > 1:
                return {"type": "move", "target": path[1]}

            # Fallback: try any safe unvisited
            if safe_unvisited != targets:
                path = self._bfs_to_nearest(pos, safe_unvisited)
                if path and len(path) > 1:
                    return {"type": "move", "target": path[1]}

        # 6. Navigate to shoot Wumpus if known
        if self.has_arrow and self.kb.known_wumpus and self.kb.wumpus_alive:
            wr, wc = self.kb.known_wumpus
            shoot_positions = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                sr, sc = wr, wc
                while True:
                    sr += dr
                    sc += dc
                    if not (0 <= sr < self.kb.size and 0 <= sc < self.kb.size):
                        break
                    if self.kb.is_cell_safe(sr, sc):
                        shoot_positions.append((sr, sc))
            if shoot_positions:
                path = self._bfs_to_nearest(pos, set(shoot_positions))
                if path and len(path) > 1:
                    return {"type": "move", "target": path[1]}

        # 7. Take calculated risk on unknown cells
        neighbors = self.kb.get_adjacent_cells(self.row, self.col)
        unvisited_neighbors = [
            (nr, nc) for nr, nc in neighbors
            if (nr, nc) not in self.kb.visited
        ]
        if unvisited_neighbors:
            # Score each by danger level
            def danger_score(cell):
                s = 0
                if cell in self.kb.possible_wumpus: s += 2
                if cell in self.kb.possible_pits: s += 2
                if cell in self.kb.known_pits: s += 100
                if cell == self.kb.known_wumpus: s += 100
                return s

            best = min(unvisited_neighbors, key=danger_score)
            if danger_score(best) < 10:
                return {"type": "move", "target": best}

        # 8. If stuck, try shooting in a suspected direction
        if self.has_arrow and self.kb.possible_wumpus and self.kb.wumpus_alive:
            for candidate in self.kb.possible_wumpus:
                shot_dir = self._get_shot_direction(candidate[0], candidate[1])
                if shot_dir:
                    return {"type": "shoot", "direction": shot_dir}

        # 9. Go home and climb out
        if pos == (0, 0):
            return {"type": "climb"}
        path = self._bfs_path(pos, (0, 0), safe_only=True)
        if path and len(path) > 1:
            return {"type": "move", "target": path[1]}
            
        # If no 100% safe path home, take a risk but avoid known hazards
        path_risky = self._bfs_path(pos, (0, 0), safe_only=False)
        if path_risky and len(path_risky) > 1:
            return {"type": "move", "target": path_risky[1]}
            
        return self._step_toward(0, 0)

    def _get_shot_direction(self, target_row: int, target_col: int) -> Optional[str]:
        if target_row == self.row:
            return "right" if target_col > self.col else "left" if target_col < self.col else None
        if target_col == self.col:
            return "up" if target_row > self.row else "down" if target_row < self.row else None
        return None

    def _step_toward(self, target_row: int, target_col: int) -> Dict:
        """Take one step toward target, preferring safe cells, avoiding known hazards."""
        neighbors = self.kb.get_adjacent_cells(self.row, self.col)
        safe_n = [(nr, nc) for nr, nc in neighbors if self.kb.is_cell_safe(nr, nc)]
        
        if not safe_n:
            viable = [n for n in neighbors if n not in self.kb.known_pits and n != self.kb.known_wumpus]
            pool = viable if viable else neighbors
        else:
            pool = safe_n
            
        best = min(pool, key=lambda c: abs(c[0] - target_row) + abs(c[1] - target_col))
        return {"type": "move", "target": best}

    def get_state(self) -> Dict:
        return {
            "position": (self.row, self.col),
            "direction": self.direction,
            "has_arrow": self.has_arrow,
            "has_gold": self.has_gold,
            "is_alive": self.is_alive,
            "has_climbed": self.has_climbed,
            "path": self.path,
            "action_count": len(self.action_history),
        }
