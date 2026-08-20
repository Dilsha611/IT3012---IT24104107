import tkinter as tk
from tkinter import ttk
import random


class VisualGridHuntGame:

    def __init__(self, width=12, height=12, num_food=15,
                 num_opponents=0, custom_walls=None):

        self.width = width
        self.height = height

        self.agent_pos = [0, 0]
        self.direction = "Right"

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            self.walls = {
                (2, 2),
                (2, 3),
                (5, 5),
                (6, 5),
                (3, 7)
            }

        self.food_positions = set()

        while len(self.food_positions) < num_food:
            pos = (
                random.randint(0, width - 1),
                random.randint(0, height - 1)
            )

            if pos != (0, 0) and pos not in self.walls:
                self.food_positions.add(pos)

        self.opponents = []

        self.score = 0
        self.steps = 0

    # Lab 03: Expose the world model
    def get_percept(self):

        x, y = self.agent_pos

        if self.direction == "Up":
            ahead = (x, y + 1)

        elif self.direction == "Down":
            ahead = (x, y - 1)

        elif self.direction == "Left":
            ahead = (x - 1, y)

        else:
            ahead = (x + 1, y)

        return {
            "wall_ahead": (
                ahead in self.walls or
                not (
                    0 <= ahead[0] < self.width and
                    0 <= ahead[1] < self.height
                )
            ),

            "food_here": tuple(self.agent_pos)
            in self.food_positions,

            # Lab Sheet 03
            "grid_size": (self.width, self.height),
            "walls": list(self.walls),
            "all_food": list(self.food_positions)
        }

    def execute_action(self, action):

        self.steps += 1

        directions = [
            "Up",
            "Right",
            "Down",
            "Left"
        ]

        if action == "turn_left":

            i = directions.index(self.direction)

            self.direction = directions[
                (i - 1) % 4
            ]

        elif action == "turn_right":

            i = directions.index(self.direction)

            self.direction = directions[
                (i + 1) % 4
            ]

        elif action == "move_forward":

            x, y = self.agent_pos

            if self.direction == "Up":
                new_pos = (x, y + 1)

            elif self.direction == "Down":
                new_pos = (x, y - 1)

            elif self.direction == "Left":
                new_pos = (x - 1, y)

            else:
                new_pos = (x + 1, y)

            if (
                new_pos in self.walls or
                not (
                    0 <= new_pos[0] < self.width and
                    0 <= new_pos[1] < self.height
                )
            ):
                self.score -= 5

            else:
                self.agent_pos = list(new_pos)

        elif action == "suck":

            current = tuple(self.agent_pos)

            if current in self.food_positions:

                self.food_positions.remove(current)

                self.score += 20

    def is_done(self):

        return (
            len(self.food_positions) == 0
            or self.steps >= 100
        )


class GridGameGUI:

    def __init__(self, root, agent):

        self.root = root
        self.agent = agent

        self.root.title(
            "IT3012 | Practical 03 | Search Agent"
        )
        self.root.resizable(False, False)
        self.root.configure(bg="#111827")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Lab.TFrame",
            background="#111827"
        )
        style.configure(
            "Lab.TLabel",
            background="#111827",
            foreground="#e5e7eb",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Title.TLabel",
            background="#111827",
            foreground="#f8fafc",
            font=("Segoe UI", 16, "bold")
        )
        style.configure(
            "Muted.TLabel",
            background="#111827",
            foreground="#94a3b8",
            font=("Segoe UI", 9)
        )
        style.configure(
            "Lab.TButton",
            background="#2563eb",
            foreground="#ffffff",
            padding=(12, 6),
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Lab.TButton",
            background=[("active", "#3b82f6"), ("disabled", "#334155")],
            foreground=[("disabled", "#94a3b8")]
        )
        style.configure(
            "Lab.TCombobox",
            fieldbackground="#1f2937",
            background="#1f2937",
            foreground="#f8fafc",
            padding=4
        )
        style.map(
            "Lab.TCombobox",
            fieldbackground=[("readonly", "#1f2937")],
            foreground=[("readonly", "#f8fafc")]
        )

        self.env = VisualGridHuntGame(
            width=12,
            height=12,
            num_food=15,
            num_opponents=0
        )

        self.cell_size = 45

        self.algorithm = tk.StringVar(value=self.agent.active_algo)

        header = ttk.Frame(
            root,
            padding=(16, 14, 16, 8),
            style="Lab.TFrame"
        )
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Goal-Based Search Agent",
            style="Title.TLabel"
        ).pack(side="left")

        ttk.Label(
            header,
            text="IT3012 | Practical 03",
            style="Muted.TLabel"
        ).pack(side="right")

        controls = ttk.Frame(
            root,
            padding=(16, 0, 16, 10),
            style="Lab.TFrame"
        )
        controls.pack(fill="x")

        ttk.Label(
            controls,
            text="Search algorithm:",
            style="Lab.TLabel"
        ).pack(side="left")

        self.algorithm_box = ttk.Combobox(
            controls,
            textvariable=self.algorithm,
            values=("BFS", "DFS", "UCS"),
            state="readonly",
            width=8,
            style="Lab.TCombobox"
        )
        self.algorithm_box.pack(side="left", padx=(6, 14))
        self.algorithm_box.bind(
            "<<ComboboxSelected>>",
            self.change_algorithm
        )

        self.start_button = ttk.Button(
            controls,
            text="Start simulation",
            command=self.start_simulation,
            style="Lab.TButton"
        )
        self.start_button.pack(side="left")

        self.reset_button = ttk.Button(
            controls,
            text="Reset",
            command=self.reset_game,
            style="Lab.TButton"
        )
        self.reset_button.pack(side="left", padx=(6, 0))

        self.canvas = tk.Canvas(
            root,
            width=12 * self.cell_size,
            height=12 * self.cell_size,
            background="#07111f",
            highlightthickness=0
        )

        self.canvas.pack()

        self.label = ttk.Label(
            root,
            text="Ready | Score: 0 | Steps: 0 | Food: 15",
            padding=(8, 8),
            anchor="center",
            style="Lab.TLabel"
        )

        self.label.pack()

        ttk.Label(
            root,
            text="Cyan: agent    Gold: food    Coral: wall",
            padding=(8, 0, 8, 12),
            style="Muted.TLabel"
        ).pack()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.root.destroy
        )

        self.draw_grid()

    def change_algorithm(self, _event=None):

        self.agent.active_algo = self.algorithm.get()

        if self.env.steps == 0:
            self.label.config(
                text=(
                    f"Ready | Algorithm: {self.agent.active_algo} | "
                    "Score: 0 | Steps: 0 | Food: "
                    f"{len(self.env.food_positions)}"
                )
            )

    def start_simulation(self):

        self.agent.active_algo = self.algorithm.get()
        self.start_button.config(state="disabled")
        self.reset_button.config(state="disabled")
        self.algorithm_box.config(state="disabled")
        self.run_loop()

    def reset_game(self):

        self.agent.active_algo = self.algorithm.get()
        self.agent.plan = []
        self.agent.position = (0, 0)
        self.agent.direction = "Right"

        self.env = VisualGridHuntGame(
            width=12,
            height=12,
            num_food=15,
            num_opponents=0
        )

        self.start_button.config(
            state="normal",
            text="Start simulation"
        )
        self.reset_button.config(state="normal")
        self.algorithm_box.config(state="readonly")
        self.label.config(
            text=(
                f"Ready | Algorithm: {self.agent.active_algo} | "
                "Score: 0 | Steps: 0 | Food: "
                f"{len(self.env.food_positions)}"
            )
        )
        self.draw_grid()

    def draw_grid(self):

        self.canvas.delete("all")

        for x in range(self.env.width):

            for y in range(self.env.height):

                x1 = x * self.cell_size

                y1 = (
                    self.env.height - 1 - y
                ) * self.cell_size

                self.canvas.create_rectangle(
                    x1,
                    y1,
                    x1 + self.cell_size,
                    y1 + self.cell_size,

                    fill="#ff4d6d"
                    if (x, y) in self.env.walls
                    else "#0f1b2d",
                    outline="#243b53"
                )

        for fx, fy in self.env.food_positions:

            x1 = (
                fx * self.cell_size
                + self.cell_size * 0.25
            )

            y1 = (
                (self.env.height - 1 - fy)
                * self.cell_size
                + self.cell_size * 0.25
            )

            self.canvas.create_oval(
                x1,
                y1,
                x1 + self.cell_size * 0.5,
                y1 + self.cell_size * 0.5,
                fill="#ffd166",
                outline="#fff3b0",
                width=2
            )

        ax, ay = self.env.agent_pos

        x1 = (
            ax * self.cell_size
            + self.cell_size * 0.15
        )

        y1 = (
            (self.env.height - 1 - ay)
            * self.cell_size
            + self.cell_size * 0.15
        )

        self.canvas.create_oval(
            x1,
            y1,
            x1 + self.cell_size * 0.7,
            y1 + self.cell_size * 0.7,
            fill="#00e5ff",
            outline="#b8f7ff",
            width=2
        )

    def run_loop(self):

        if not self.env.is_done():

            # Get complete percept
            percept = self.env.get_percept()

            # SearchAgent decides next action
            action = self.agent.sense_and_act(
                percept
            )

            # Environment executes action
            self.env.execute_action(
                action
            )

            self.draw_grid()

            self.label.config(
                text=(
                    f"{self.agent.active_algo} | "
                    f"Score: {self.env.score} | "
                    f"Steps: {self.env.steps} | "
                    f"Food: {len(self.env.food_positions)} | "
                    f"Action: {action}"
                )
            )

            self.root.after(
                300,
                self.run_loop
            )

        else:

            self.label.config(
                text=(
                    f"Finished | Algorithm: {self.agent.active_algo} | "
                    f"Final Score: {self.env.score} | "
                    f"Steps: {self.env.steps} | "
                    f"Food left: {len(self.env.food_positions)}"
                )
            )

            self.start_button.config(state="disabled")
            self.reset_button.config(state="normal")
            self.algorithm_box.config(state="readonly")


if __name__ == "__main__":

    from agent import SearchAgent

    root = tk.Tk()

    agent = SearchAgent()

    GridGameGUI(
        root,
        agent
    )

    root.mainloop()