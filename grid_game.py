import random


class GridHuntGame:
    """A small Pacman-style grid environment (4x4) where an agent collects food."""

    def __init__(self, width=4, height=4):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)

        # Place food pellets and obstacles using tuple coordinates
        self.food_positions = {(1, 2), (2, 3), (3, 0), (2, 1)}
        self.walls = {(1, 1), (2, 2)}

        # Step 2.1: Declare toxic traps (avoiding (0,0), walls, and food)
        self.toxic_traps = {(0, 3), (3, 2)}

        self.score = 0
        self.steps = 0

    def get_percept(self, agent=None) -> dict:
        return {
            'agent_pos': list(self.agent_pos),
            'smells_food': tuple(self.agent_pos) in self.food_positions,
            'hit_wall': tuple(self.agent_pos) in self.walls,
            'score': self.score,
            'remaining_food': len(self.food_positions),
            # Step 2.2: Add toxin sensor
            'smells_toxin': tuple(self.agent_pos) in self.toxic_traps
        }

    def execute_action(self, agent, action: str):
        self.steps += 1
        new_pos = list(self.agent_pos)

        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        # Check collision with walls
        if tuple(new_pos) in self.walls:
            self.score -= 5  # Penalty for hitting a wall
        else:
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)

        # Check if eating food
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20  # Reward for eating food pellet

        # Step 2.3: Check if stepped on a toxic trap
        if tuple_pos in self.toxic_traps:
            self.score -= 15  # 15 points penalty for toxic trap

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 20