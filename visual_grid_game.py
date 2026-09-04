import random
import tkinter as tk
from agent import SearchAgent


class VisualGridHuntGame:

    def __init__(self, width=10, height=10, num_food=10,
                 num_opponents=2, num_traps=3, custom_walls=None):

        self.width = width
        self.height = height

        self.agent_pos = [0, 0]
        self.direction = "UP"

        if custom_walls:
            self.walls = set(custom_walls)
        else:
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        self.food_positions = set()
        while len(self.food_positions) < num_food:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            if (x, y) != (0, 0) and (x, y) not in self.walls:
                self.food_positions.add((x, y))

        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            if (
                (x, y) != (0, 0)
                and (x, y) not in self.walls
                and (x, y) not in self.food_positions
            ):
                self.toxic_traps.add((x, y))

        self.opponents = []

        while len(self.opponents) < num_opponents:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)

            if (
                (x, y) != (0, 0)
                and (x, y) not in self.walls
                and (x, y) not in self.food_positions
                and (x, y) not in self.toxic_traps
            ):
                self.opponents.append([x, y])

        self.score = 0
        self.steps = 0
        self.collision = False

    # PARTIAL OBSERVABILITY
    def get_percept(self):

        x, y = self.agent_pos

        if self.direction == "UP":
            next_x, next_y = x, y + 1

        elif self.direction == "DOWN":
            next_x, next_y = x, y - 1

        elif self.direction == "LEFT":
            next_x, next_y = x - 1, y

        else:  # RIGHT
            next_x, next_y = x + 1, y

        wall_ahead = (
            next_x < 0
            or next_x >= self.width
            or next_y < 0
            or next_y >= self.height
            or (next_x, next_y) in self.walls
        )

        food_here = tuple(self.agent_pos) in self.food_positions

        return {
    "wall_ahead": wall_ahead,
    "food_here": food_here,
    "agent_pos": tuple(self.agent_pos),
    "grid_size": (self.width, self.height),
    "walls": list(self.walls),
    "all_food": list(self.food_positions),
    # Tiles where the Bloodseeker escort is missing (toxic traps double
    # as the "unsafe tile" percept fed to the Knowledge Base per-tile).
    "danger_tiles": list(self.toxic_traps)
}

    def execute_action(self, action):

        self.steps += 1

        if action == "Up":
            self.direction = "UP"

        elif action == "Down":
            self.direction = "DOWN"

        elif action == "Left":
            self.direction = "LEFT"

        elif action == "Right":
            self.direction = "RIGHT"

        new_pos = list(self.agent_pos)

        if action == "Up":
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)

        elif action == "Down":
            new_pos[1] = max(0, new_pos[1] - 1)

        elif action == "Left":
            new_pos[0] = max(0, new_pos[0] - 1)

        elif action == "Right":
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5

        else:
            self.agent_pos = new_pos

        pos = tuple(self.agent_pos)

        if pos in self.food_positions:
            self.food_positions.remove(pos)
            self.score += 20

        if pos in self.toxic_traps:
            self.score -= 15

    def is_done(self):
        return len(self.food_positions) == 0 or self.steps >= 60


class ModelBasedAgent:

    def __init__(self):

        # Internal memory
        self.visited_states = {}
        self.last_action = None

    def sense_and_act(self, percept):

        # -------------------------
        # Update Internal State
        # (Sensor + Transition Model)
        # -------------------------

        state = (
            percept["wall_ahead"],
            percept["food_here"]
        )

        self.visited_states[state] = (
            self.visited_states.get(state, 0) + 1
        )

        # -------------------------
        # Condition-Action Rules
        # -------------------------

        # IF food_here THEN suck
        if percept["food_here"]:

            action = "SUCK"

        # IF same state repeated many times
        # assume agent is looping
        elif self.visited_states[state] > 3:

            if self.last_action == "Left":
                action = "Right"
            else:
                action = "Left"

        # IF wall ahead THEN turn left
        elif percept["wall_ahead"]:

            action = "Left"

        # ELSE move forward
        else:

            action = "Up"

        # Save last action
        self.last_action = action

        return action


class GridGameGUI:

    def __init__(self, root):

        self.root = root

        self.env = VisualGridHuntGame(
            width=12,
            height=12,
            num_food=15,
            num_opponents=0,
            num_traps=4
        )

        self.agent = SearchAgent()

        self.cell_size = 40

        self.canvas = tk.Canvas(
            root,
            width=self.env.width * self.cell_size,
            height=self.env.height * self.cell_size,
            bg="white"
        )

        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0")
        self.label.pack()

        self.btn = tk.Button(
            root,
            text="Start Simulation",
            command=self.run_loop
        )

        self.btn.pack()

        self.draw_grid()

    def draw_grid(self):

        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):

                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size

                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "lightgray" if (x, y) in self.env.walls else "white"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline="black"
                )

        for fx, fy in self.env.food_positions:

            self.canvas.create_oval(
                fx * self.cell_size + 10,
                (self.env.height - 1 - fy) * self.cell_size + 10,
                fx * self.cell_size + 30,
                (self.env.height - 1 - fy) * self.cell_size + 30,
                fill="yellow"
            )

        ax, ay = self.env.agent_pos

        self.canvas.create_oval(
            ax * self.cell_size + 5,
            (self.env.height - 1 - ay) * self.cell_size + 5,
            ax * self.cell_size + 35,
            (self.env.height - 1 - ay) * self.cell_size + 35,
            fill="blue"
        )

    def run_loop(self):

        self.btn.config(state="disabled")

        def step():

            if not self.env.is_done():

                percept = self.env.get_percept()

                print("Percept:", percept)

                action = self.agent.sense_and_act(percept)

                print("Action:", action)

                if action == "SUCK":

                    pos = tuple(self.env.agent_pos)

                    if pos in self.env.food_positions:
                        self.env.food_positions.remove(pos)
                        self.env.score += 20

                else:
                    self.env.execute_action(action)

                self.draw_grid()

                self.label.config(
                    text=f"Score: {self.env.score} | Steps: {self.env.steps}"
                )

                self.root.after(250, step)

            else:

                self.label.config(
                    text=f"Finished! Final Score: {self.env.score}"
                )

                self.btn.config(state="normal")

        step()


if __name__ == "__main__":

    root = tk.Tk()
    root.title("IT3012 Practical 02")

    app = GridGameGUI(root)

    root.mainloop()