import unittest
from collections import deque

# =====================================================================
# AGENT IMPLEMENTATIONS (Practicals 1, 2, and 3)
# =====================================================================

class SimpleReflexAgent:
    """Practical 1: Acts purely based on immediate condition-action rules."""

    def __init__(self):
        self.actions = ['Up', 'Right', 'Down', 'Left']

    def sense_and_act(self, percept: dict) -> str:
        if percept.get('food_here'):
            return 'Stay'
        if percept.get('wall_ahead'):
            return 'Right'
        return 'Up'


class ModelBasedAgent:
    """Practical 2: Maintains internal memory/state to escape loops."""

    def __init__(self):
        self.actions = ['Up', 'Right', 'Down', 'Left']
        self.last_action = None
        self.action_index = 0

    def sense_and_act(self, percept: dict) -> str:
        if percept.get('wall_ahead'):
            # Cycle through alternative directions when hitting a wall consecutively
            self.action_index = (self.action_index + 1) % len(self.actions)
            action = self.actions[self.action_index]
        else:
            action = 'Up'

        self.last_action = action
        return action


class SearchAgent:
    """Practical 3: Uses Breadth-First Search (BFS) to find optimal paths."""

    def __init__(self):
        pass

    def bfs_search(self, start: tuple, goal: tuple, walls: list, grid_size: tuple):
        """
        Performs BFS to find the shortest path from start to goal.
        Returns a list of action strings or None if unreachable.
        """
        cols, rows = grid_size
        wall_set = set(walls)

        # Movement mapping: (dx, dy) -> Action Name
        moves = [
            (0, 1, 'Up'),
            (1, 0, 'Right'),
            (0, -1, 'Down'),
            (-1, 0, 'Left')
        ]

        # Queue stores tuples of: (current_position, path_taken)
        queue = deque([(start, [])])
        visited = {start}

        while queue:
            (curr_x, curr_y), path = queue.popleft()

            if (curr_x, curr_y) == goal:
                return path

            for dx, dy, action in moves:
                next_x, next_y = curr_x + dx, curr_y + dy
                next_pos = (next_x, next_y)

                # Validate grid boundaries and obstacles
                if 0 <= next_x < cols and 0 <= next_y < rows:
                    if next_pos not in wall_set and next_pos not in visited:
                        visited.add(next_pos)
                        queue.append((next_pos, path + [action]))

        return None  # Unreachable goal


# =====================================================================
# UNIT TEST SUITE
# =====================================================================

class TestPractical1And2_ReflexAgents(unittest.TestCase):
    """
    Tests for Practicals 1 & 2: Simple Reflex and Model-Based Agents.
    Focuses on Condition-Action rules, partial observability, and memory.
    """

    def setUp(self):
        try:
            self.simple_agent = SimpleReflexAgent()
            self.model_agent = ModelBasedAgent()
        except NameError:
            self.fail("Agent classes not found. Ensure SimpleReflexAgent and ModelBasedAgent are defined.")

    def test_simple_reflex_logic(self):
        """Test 1: Simple Reflex Agent should react purely to immediate percepts."""
        percept_food = {'wall_ahead': False, 'food_here': True}
        action = self.simple_agent.sense_and_act(percept_food)
        self.assertIsNotNone(action, "SimpleReflexAgent returned None instead of an action.")

        percept_wall = {'wall_ahead': True, 'food_here': False}
        action_wall = self.simple_agent.sense_and_act(percept_wall)
        self.assertIn(action_wall, ['Left', 'Right', 'Down', 'Up'],
                      "Agent did not output a valid movement action when facing a wall.")

    def test_model_based_memory(self):
        """Test 2: Model-Based Agent should maintain internal state to escape loops."""
        percept = {'wall_ahead': True, 'food_here': False}

        action_1 = self.model_agent.sense_and_act(percept)
        action_2 = self.model_agent.sense_and_act(percept)

        self.assertNotEqual(
            action_1,
            action_2,
            "ModelBasedAgent returned the exact same action twice in a row for the same percept. Internal state/memory is not working correctly."
        )


class TestPractical3_SearchAgent(unittest.TestCase):
    """
    Tests for Practical 3: Problem-Solving Agents.
    Focuses on offline planning and Breadth-First Search (BFS) implementation.
    """

    def setUp(self):
        try:
            self.search_agent = SearchAgent()
        except NameError:
            self.fail("SearchAgent class not found.")

    def test_bfs_shortest_path(self):
        """Test 3: BFS must find the optimal (shortest) path in a static maze."""
        grid_size = (4, 4)
        start_pos = (0, 0)
        goal_pos = (3, 3)
        walls = [(1, 0), (2, 0), (0, 2), (1, 2), (2, 2)]

        try:
            path = self.search_agent.bfs_search(start_pos, goal_pos, walls, grid_size)
        except AttributeError:
            self.fail("bfs_search method not implemented in SearchAgent.")

        self.assertIsNotNone(path, "BFS returned None. No path found.")
        self.assertIsInstance(path, list, "BFS should return a list of actions (strings).")
        self.assertEqual(len(path), 6, f"BFS did not find the optimal path. Expected 6 steps, got {len(path)}.")

    def test_bfs_unreachable_goal(self):
        """Test 4: BFS must correctly return failure (None/Empty) if goal is blocked."""
        grid_size = (3, 3)
        start_pos = (0, 0)
        goal_pos = (2, 2)
        walls = [(1, 2), (2, 1), (1, 1)]

        path = self.search_agent.bfs_search(start_pos, goal_pos, walls, grid_size)
        is_empty_or_none = (path is None) or (len(path) == 0)
        self.assertTrue(is_empty_or_none, "BFS should return None or [] when the goal is unreachable.")


if __name__ == '__main__':
    print("=== IT3012: Intelligent Agents - Autograder Test Suite ===\n")
    unittest.main(verbosity=2)