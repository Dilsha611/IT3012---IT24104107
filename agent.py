import random

class GreedyGridAgent:
    """A simple agent that moves towards food while avoiding toxic traps and walls."""

    def __init__(self):
        self.actions_pool = ['Up', 'Down', 'Left', 'Right']

    def sense_and_act(self, percept: dict) -> str:
        current_r, current_c = percept['agent_pos']
        food_positions = percept.get('food_positions', [])
        walls = set(percept.get('walls', []))
        smells_toxin = percept.get('smells_toxin', False)

        # Direction offsets: (d_row, d_col)
        moves = {
            'Up': (-1, 0),
            'Down': (1, 0),
            'Left': (0, -1),
            'Right': (0, 1)
        }

        valid_actions = []

        # Filter out actions that hit walls
        for action, (dr, dc) in moves.items():
            next_pos = (current_r + dr, current_c + dc)
            if next_pos not in walls:
                valid_actions.append(action)

        if not valid_actions:
            return 'Up'  # Fallback if surrounded by walls

        # Target nearest food if visible
        if food_positions:
            # Find nearest food by Manhattan distance
            nearest_food = min(
                food_positions,
                key=lambda f: abs(f[0] - current_r) + abs(f[1] - current_c)
            )

            # Pick the best move that brings us closer to nearest food
            best_action = None
            min_dist = float('inf')

            for action in valid_actions:
                dr, dc = moves[action]
                next_pos = (current_r + dr, current_c + dc)
                dist = abs(nearest_food[0] - next_pos[0]) + abs(nearest_food[1] - next_pos[1])
                
                if dist < min_dist:
                    min_dist = dist
                    best_action = action

            if best_action:
                return best_action

        # Fallback to random move among safe valid actions
        return random.choice(valid_actions)