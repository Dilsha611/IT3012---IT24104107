import random
import tkinter as tk


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

    # PARTIAL OBSERVABILITY (Step 1.1)
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
            "food_here": food_here
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


# ---- Step 1.2: Simple Reflex Agent (no memory) ----
class SimpleReflexAgent:

    def sense_and_act(self, percept):

        # IF food_here THEN suck
        if percept["food_here"]:
            return "SUCK"

        # IF wall_ahead THEN turn right
        elif percept["wall_ahead"]:
            return "Right"

        # ELSE move forward
        else:
            return "Up"


# ---- Step 1.3: Model-Based Agent (has memory, escapes loops) ----
class ModelBasedAgent:

    def __init__(self):
        self.last_percept = None
        self.last_action = None
        self.visited_states = {}
        self._turn_cycle = ["Right", "Left", "Down", "Up"]
        self._turn_index = 0

    def sense_and_act(self, percept):

        # ---- Update internal state first ----
        state = (percept["wall_ahead"], percept["food_here"])
        self.visited_states[state] = self.visited_states.get(state, 0) + 1

        stuck_in_loop = (
            self.last_percept == percept and percept["wall_ahead"]
        )

        # ---- Condition-Action rules that query memory ----
        if percept["food_here"]:
            action = "SUCK"

        elif stuck_in_loop:
            self._turn_index = (self._turn_index + 1) % len(self._turn_cycle)
            action = self._turn_cycle[self._turn_index]

        elif percept["wall_ahead"]:
            action = self._turn_cycle[self._turn_index]

        else:
            action = "Up"

        self.last_percept = percept
        self.last_action = action
        return action


class GridGameGUI:

    # ---- Cosmetic-only colour palette (no logic here) ----
    BG_COLOR = "#1e1e2e"
    PANEL_COLOR = "#2a2a3d"
    GRID_BG = "#f4f4f9"
    WALL_COLOR = "#4b4b63"
    WALL_OUTLINE = "#33334a"
    CELL_OUTLINE = "#d8d8e6"
    FOOD_FILL = "#ffd23f"
    FOOD_OUTLINE = "#e0a800"
    AGENT_FILL = "#3f8efc"
    AGENT_OUTLINE = "#1b56c4"
    AGENT_HIGHLIGHT = "#a9c9ff"
    TEXT_LIGHT = "#f4f4f9"
    ACCENT = "#3f8efc"

    def __init__(self, root, agent_class=ModelBasedAgent):

        self.root = root
        self.root.configure(bg=self.BG_COLOR)

        self.env = VisualGridHuntGame(
            width=12,
            height=12,
            num_food=15,
            num_opponents=0,
            num_traps=4
        )

        # Step 1.2: pass agent_class=SimpleReflexAgent to watch it get
        # trapped in a corner. Step 1.3 (default): ModelBasedAgent escapes.
        self.agent = agent_class()

        self.cell_size = 40

        # ---- Header ----
        header = tk.Frame(root, bg=self.BG_COLOR)
        header.pack(fill="x", padx=16, pady=(16, 8))

        tk.Label(
            header,
            text="IT3012 · Practical 02",
            font=("Segoe UI", 16, "bold"),
            fg=self.TEXT_LIGHT,
            bg=self.BG_COLOR
        ).pack(side="left")

        tk.Label(
            header,
            text=f"Agent: {agent_class.__name__}",
            font=("Segoe UI", 10),
            fg="#9c9cb8",
            bg=self.BG_COLOR
        ).pack(side="right")

        # ---- Canvas card ----
        card = tk.Frame(root, bg=self.PANEL_COLOR, padx=10, pady=10)
        card.pack(padx=16, pady=8)

        self.canvas = tk.Canvas(
            card,
            width=self.env.width * self.cell_size,
            height=self.env.height * self.cell_size,
            bg=self.GRID_BG,
            highlightthickness=0
        )
        self.canvas.pack()

        # ---- Status panel ----
        status = tk.Frame(root, bg=self.BG_COLOR)
        status.pack(fill="x", padx=16, pady=(4, 4))

        self.label = tk.Label(
            status,
            text="Score: 0   |   Steps: 0",
            font=("Segoe UI", 12, "bold"),
            fg=self.TEXT_LIGHT,
            bg=self.BG_COLOR
        )
        self.label.pack(side="left")

        # ---- Button ----
        self.btn = tk.Button(
            root,
            text="▶  Start Simulation",
            command=self.run_loop,
            font=("Segoe UI", 11, "bold"),
            fg="white",
            bg=self.ACCENT,
            activebackground="#2f6fd6",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2"
        )
        self.btn.pack(padx=16, pady=(4, 16), fill="x")

        self.draw_grid()

    def draw_grid(self):

        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):

                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size

                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                is_wall = (x, y) in self.env.walls
                color = self.WALL_COLOR if is_wall else self.GRID_BG
                outline = self.WALL_OUTLINE if is_wall else self.CELL_OUTLINE

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color,
                    outline=outline,
                    width=1
                )

        for fx, fy in self.env.food_positions:

            fx1 = fx * self.cell_size + 9
            fy1 = (self.env.height - 1 - fy) * self.cell_size + 9
            fx2 = fx * self.cell_size + 31
            fy2 = (self.env.height - 1 - fy) * self.cell_size + 31

            self.canvas.create_oval(
                fx1, fy1, fx2, fy2,
                fill=self.FOOD_FILL,
                outline=self.FOOD_OUTLINE,
                width=2
            )

        ax, ay = self.env.agent_pos

        ax1 = ax * self.cell_size + 4
        ay1 = (self.env.height - 1 - ay) * self.cell_size + 4
        ax2 = ax * self.cell_size + 36
        ay2 = (self.env.height - 1 - ay) * self.cell_size + 36

        self.canvas.create_oval(
            ax1, ay1, ax2, ay2,
            fill=self.AGENT_FILL,
            outline=self.AGENT_OUTLINE,
            width=2
        )
        # small highlight dot for a subtle "glossy" look
        self.canvas.create_oval(
            ax1 + 6, ay1 + 5, ax1 + 14, ay1 + 13,
            fill=self.AGENT_HIGHLIGHT,
            outline=""
        )

    def run_loop(self):

        # If the previous run already finished, this click is a "Restart":
        # build a brand-new environment and a brand-new agent (fresh
        # memory) instead of reusing the finished ones.
        if self.env.is_done():
            self.env = VisualGridHuntGame(
                width=12,
                height=12,
                num_food=15,
                num_opponents=0,
                num_traps=4
            )
            self.agent = self.agent.__class__()
            self.draw_grid()
            self.label.config(
                text="Score: 0   |   Steps: 0",
                fg=self.TEXT_LIGHT
            )

        self.btn.config(state="disabled", bg="#5c5c78", cursor="arrow")

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

                score_color = "#4ade80" if self.env.score >= 0 else "#f87171"
                self.label.config(
                    text=f"Score: {self.env.score}   |   Steps: {self.env.steps}",
                    fg=score_color
                )

                self.root.after(250, step)

            else:

                score_color = "#4ade80" if self.env.score >= 0 else "#f87171"
                self.label.config(
                    text=f"Finished!  Final Score: {self.env.score}",
                    fg=score_color
                )

                self.btn.config(
                    state="normal",
                    bg=self.ACCENT,
                    text="▶  Restart",
                    cursor="hand2"
                )

        step()


if __name__ == "__main__":

    root = tk.Tk()
    root.title("IT3012 Practical 02")

    app = GridGameGUI(root)

    root.mainloop()