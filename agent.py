from collections import deque
import heapq


class SearchAgent:

    def __init__(self):
        self.plan = []
        self.active_algo = "BFS"

        self.position = (0, 0)
        self.direction = "Right"

    def get_neighbors(self, position, grid_size, walls):

        x, y = position
        width, height = grid_size

        moves = [
            ((x + 1, y), "Right"),
            ((x - 1, y), "Left"),
            ((x, y + 1), "Up"),
            ((x, y - 1), "Down")
        ]

        return [
            (pos, action)
            for pos, action in moves
            if 0 <= pos[0] < width
            and 0 <= pos[1] < height
            and pos not in walls
        ]

    def bfs_search(self, start, goal, grid_size, walls):

        frontier = deque([(start, [])])
        reached = {start}

        while frontier:

            current, path = frontier.popleft()

            if current == goal:
                return path

            for next_pos, action in self.get_neighbors(
                current, grid_size, walls
            ):

                if next_pos not in reached:
                    reached.add(next_pos)
                    frontier.append(
                        (next_pos, path + [action])
                    )

        return []

    def dfs_search(self, start, goal, grid_size, walls):

        frontier = [(start, [])]
        reached = {start}

        while frontier:

            current, path = frontier.pop()

            if current == goal:
                return path

            for next_pos, action in self.get_neighbors(
                current, grid_size, walls
            ):

                if next_pos not in reached:
                    reached.add(next_pos)
                    frontier.append(
                        (next_pos, path + [action])
                    )

        return []

    def ucs_search(self, start, goal, grid_size, walls):

        frontier = [(0, start, [])]
        reached = {start: 0}

        while frontier:

            cost, current, path = heapq.heappop(frontier)

            if current == goal:
                return path

            for next_pos, action in self.get_neighbors(
                current, grid_size, walls
            ):

                new_cost = cost + 1

                if (
                    next_pos not in reached
                    or new_cost < reached[next_pos]
                ):
                    reached[next_pos] = new_cost

                    heapq.heappush(
                        frontier,
                        (
                            new_cost,
                            next_pos,
                            path + [action]
                        )
                    )

        return []

    def search(self, start, goal, grid_size, walls):

        if self.active_algo == "BFS":
            return self.bfs_search(
                start, goal, grid_size, walls
            )

        if self.active_algo == "DFS":
            return self.dfs_search(
                start, goal, grid_size, walls
            )

        return self.ucs_search(
            start, goal, grid_size, walls
        )

    def turn_actions(self, target_direction):

        directions = [
            "Up",
            "Right",
            "Down",
            "Left"
        ]

        current = directions.index(self.direction)
        target = directions.index(target_direction)

        right_turns = (target - current) % 4
        left_turns = (current - target) % 4

        if right_turns <= left_turns:
            return ["turn_right"] * right_turns

        return ["turn_left"] * left_turns

    def update_state(self, action):

        directions = [
            "Up",
            "Right",
            "Down",
            "Left"
        ]

        if action == "turn_right":

            i = directions.index(self.direction)
            self.direction = directions[
                (i + 1) % 4
            ]

        elif action == "turn_left":

            i = directions.index(self.direction)
            self.direction = directions[
                (i - 1) % 4
            ]

        elif action == "move_forward":

            x, y = self.position

            if self.direction == "Up":
                self.position = (x, y + 1)

            elif self.direction == "Down":
                self.position = (x, y - 1)

            elif self.direction == "Left":
                self.position = (x - 1, y)

            else:
                self.position = (x + 1, y)

    def create_plan(self, movement_path):

        actions = []
        planned_direction = self.direction

        directions = [
            "Up",
            "Right",
            "Down",
            "Left"
        ]

        for target_direction in movement_path:

            current = directions.index(planned_direction)
            target = directions.index(target_direction)

            right_turns = (target - current) % 4
            left_turns = (current - target) % 4

            if right_turns <= left_turns:
                actions.extend(["turn_right"] * right_turns)
            else:
                actions.extend(["turn_left"] * left_turns)

            actions.append("move_forward")
            planned_direction = target_direction

        actions.append("suck")

        return actions

    def sense_and_act(self, percept):

        if not self.plan:

            if percept["food_here"]:
                return "suck"

            foods = percept["all_food"]

            if not foods:
                return "turn_right"

            grid_size = percept["grid_size"]
            walls = set(percept["walls"])

            # Find the closest food
            goal = min(
                foods,
                key=lambda food:
                abs(food[0] - self.position[0])
                + abs(food[1] - self.position[1])
            )

            if tuple(goal) == self.position:
                self.plan = ["suck"]
            else:
                movement_path = self.search(
                    self.position,
                    tuple(goal),
                    grid_size,
                    walls
                )

                if not movement_path:
                    return "turn_right"

                self.plan = self.create_plan(
                    movement_path
                )

        if self.plan:

            action = self.plan.pop(0)

            # Keep internal state synchronized
            self.update_state(action)

            return action

        return "turn_right"