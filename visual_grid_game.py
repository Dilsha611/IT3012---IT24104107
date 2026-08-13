# visual_grid_game.py
import random
import tkinter as tk
from collections import deque
from tkinter import ttk


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    # Directional helpers: the agent has a facing direction, and "ahead" is
    # always relative to that facing (this is what makes wall_ahead/food_here
    # meaningful sensor readings instead of leaked global coordinates).
    FACING_OFFSETS = {'Up': (0, 1), 'Down': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}
    TURN_LEFT = {'Up': 'Left', 'Left': 'Down', 'Down': 'Right', 'Right': 'Up'}
    TURN_RIGHT = {'Up': 'Right', 'Right': 'Down', 'Down': 'Left', 'Left': 'Up'}

    def __init__(
        self,
        width=10,
        height=10,
        num_food=10,
        num_opponents=2,
        num_traps=5,
        custom_walls=None,
    ):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)
        self.facing = 'Up'  # Agent's own heading (proprioception, not a global-position leak)

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Generate some default scattered walls for a larger grid
            self.walls = {(2, 2), (2, 3), (5, 5), (6, 5), (3, 7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        # Toxic traps are part of the external environment. Keep them away from
        # the starting cell, walls, food, and opponents so every object has an
        # unambiguous initial location.
        blocked_positions = (
            {(0, 0)}
            | self.walls
            | self.food_positions
            | {tuple(opponent) for opponent in self.opponents}
        )
        available_positions = [
            (x, y)
            for x in range(self.width)
            for y in range(self.height)
            if (x, y) not in blocked_positions
        ]
        if num_traps > len(available_positions):
            raise ValueError(
                f"Cannot place {num_traps} traps: only "
                f"{len(available_positions)} safe cells are available."
            )
        self.toxic_traps = set(random.sample(available_positions, num_traps))

        self.score = 0
        self.steps = 0
        self.max_steps = max(60, self.width * self.height * 4)
        self.collision = False

    def get_percept(self) -> dict:
        """Partially observable sensor reading: local booleans relative to the
        agent's current facing direction only. No global coordinates are
        exposed (agent_pos / opponent_positions are gone) so the agent cannot
        cheat its way around blind spots."""
        dx, dy = self.FACING_OFFSETS[self.facing]
        ahead = (self.agent_pos[0] + dx, self.agent_pos[1] + dy)
        ahead_in_bounds = 0 <= ahead[0] < self.width and 0 <= ahead[1] < self.height
        wall_ahead = (not ahead_in_bounds) or (ahead in self.walls)

        return {
            'wall_ahead': wall_ahead,
            'food_here': tuple(self.agent_pos) in self.food_positions,
            'smells_toxin': tuple(self.agent_pos) in self.toxic_traps,
            'facing': self.facing,
            'collision': self.collision,
            'score': self.score,
            'remaining_food': len(self.food_positions),
            # Goal- and utility-based programs need a state representation in
            # order to project future states.  Reflex agents deliberately
            # ignore these fields and use only the local sensors above.
            'position': tuple(self.agent_pos),
            'food_positions': frozenset(self.food_positions),
            'walls': frozenset(self.walls),
            'grid_size': (self.width, self.height),
            'opponent_positions': tuple(map(tuple, self.opponents)),
        }

    def execute_action(self, action: str):
        """Actions are relative to the agent's facing: turn_left, turn_right,
        move_forward, suck. This mirrors a real robot, which only ever knows
        'turn' and 'go forward', never absolute compass moves."""
        self.steps += 1

        if action == 'turn_left':
            self.facing = self.TURN_LEFT[self.facing]
        elif action == 'turn_right':
            self.facing = self.TURN_RIGHT[self.facing]
        elif action == 'suck':
            tuple_pos = tuple(self.agent_pos)
            if tuple_pos in self.food_positions:
                self.food_positions.remove(tuple_pos)
                self.score += 20
        elif action == 'move_forward':
            dx, dy = self.FACING_OFFSETS[self.facing]
            new_pos = [self.agent_pos[0] + dx, self.agent_pos[1] + dy]
            in_bounds = 0 <= new_pos[0] < self.width and 0 <= new_pos[1] < self.height

            if not in_bounds or tuple(new_pos) in self.walls:
                self.score -= 5  # bumped into a wall/edge, stayed put
            else:
                self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.toxic_traps:
            self.score -= 15

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return (len(self.food_positions) == 0
                or self.steps >= self.max_steps
                or self.collision)


class SimpleReflexAgent:
    """Step 1.2: pure condition-action rules, no memory of past percepts.
    This is expected to get trapped in corners/U-shaped walls because it has
    no way to remember it already tried turning left here before."""

    def sense_and_act(self, percept: dict) -> str:
        if percept['food_here']:
            return 'suck'
        if percept['wall_ahead']:
            return 'turn_left'
        return 'move_forward'

    # The tutorial calls the agent entry point ``evaluate``.  Keep the GUI's
    # ``sense_and_act`` name too so the same class works in both contexts.
    def evaluate(self, percept: dict) -> str:
        return self.sense_and_act(percept)


class ModelBasedAgent:
    """A reflex agent with an internal model of percept and action history."""

    def __init__(self):
        self.internal_state = {
            "percept_history": [],
            "action_history": [],
            "last_action": None,
            "repeated_blockages": 0,
            "visited": {(0, 0)},
            "position": (0, 0),
            "facing": "Up",
        }

    def _process_percept(self, percept: dict):
        history = self.internal_state["percept_history"]
        history.append(dict(percept))
        if len(history) > 20:
            del history[0]

        if percept["wall_ahead"]:
            self.internal_state["repeated_blockages"] += 1
        else:
            self.internal_state["repeated_blockages"] = 0

    def _record_action_effect(self, action):
        if action is None:
            return
        facing = self.internal_state["facing"]
        if action == "turn_left":
            facing = VisualGridHuntGame.TURN_LEFT[facing]
        elif action == "turn_right":
            facing = VisualGridHuntGame.TURN_RIGHT[facing]
        elif action == "move_forward":
            dx, dy = VisualGridHuntGame.FACING_OFFSETS[facing]
            x, y = self.internal_state["position"]
            self.internal_state["position"] = (x + dx, y + dy)
            self.internal_state["visited"].add((x + dx, y + dy))
        self.internal_state["facing"] = facing

    def _find_action(self, percept: dict) -> str:
        if percept["food_here"]:
            return "suck"
        if not percept["wall_ahead"]:
            return "move_forward"

        # Use remembered action history to avoid repeating the stateless
        # agent's identical response when the same blocked percept recurs.
        return (
            "turn_right"
            if self.internal_state["last_action"] == "turn_left"
            else "turn_left"
        )

    def evaluate(self, percept: dict, last_action=None) -> str:
        # Tutorial 02 order: observe the current percept, apply the effect of
        # the PREVIOUS action, then match a rule against the updated model.
        previous_action = (
            last_action
            if last_action is not None
            else self.internal_state["last_action"]
        )
        self._process_percept(percept)
        self._record_action_effect(previous_action)
        action = self._find_action(percept)
        self.internal_state["last_action"] = action
        self.internal_state["action_history"].append(action)
        return action

    def sense_and_act(self, percept: dict) -> str:
        return self.evaluate(percept)


class GoalBasedAgent:
    """Uses breadth-first search to plan toward the nearest remaining food."""

    def __init__(self, target_goal=0):
        self.target_goal = target_goal

    def _goal_reached(self, percept: dict) -> bool:
        return percept["remaining_food"] == self.target_goal

    @staticmethod
    def _absolute_to_relative(direction: str, facing: str) -> str:
        if direction == facing:
            return "move_forward"
        if direction == VisualGridHuntGame.TURN_LEFT[facing]:
            return "turn_left"
        if direction == VisualGridHuntGame.TURN_RIGHT[facing]:
            return "turn_right"
        return "turn_right"  # turn twice on successive planning cycles

    def _project_path(self, percept: dict) -> str:
        if percept["food_here"]:
            return "suck"

        start = percept["position"]
        goals = set(percept["food_positions"])
        walls = set(percept["walls"])
        width, height = percept["grid_size"]
        queue = deque([(start, [])])
        visited = {start}
        directions = (
            ("Up", 0, 1), ("Down", 0, -1),
            ("Left", -1, 0), ("Right", 1, 0),
        )

        while queue:
            position, path = queue.popleft()
            if position in goals and path:
                return self._absolute_to_relative(path[0], percept["facing"])
            for direction, dx, dy in directions:
                neighbour = (position[0] + dx, position[1] + dy)
                if (0 <= neighbour[0] < width and 0 <= neighbour[1] < height
                        and neighbour not in walls and neighbour not in visited):
                    visited.add(neighbour)
                    queue.append((neighbour, path + [direction]))

        return "halt"

    def evaluate(self, percept: dict) -> str:
        if self._goal_reached(percept):
            return "halt"
        return self._project_path(percept)

    def sense_and_act(self, percept):
        return self.evaluate(percept)


class UtilityBasedAgent:
    """Chooses the action whose simulated outcome has greatest utility."""

    POSSIBLE_ACTIONS = ("suck", "move_forward", "turn_left", "turn_right")

    def __init__(self):
        self.action_utilities = {
            "suck": 100.0,
            "move_forward": 10.0,
            "turn_left": 4.0,
            "turn_right": 4.0,
        }

    def simulate_action(self, percept: dict, action: str) -> dict:
        outcome = dict(percept)
        outcome["action"] = action
        outcome["valid"] = not (
            (action == "suck" and not percept["food_here"])
            or (action == "move_forward" and percept["wall_ahead"])
        )
        if action == "move_forward" and outcome["valid"]:
            dx, dy = VisualGridHuntGame.FACING_OFFSETS[percept["facing"]]
            x, y = percept["position"]
            outcome["position"] = (x + dx, y + dy)
        return outcome

    def compute_utility(self, outcome: dict) -> float:
        if not outcome["valid"]:
            return float("-inf")

        action = outcome["action"]
        utility = self.action_utilities[action]
        if action == "suck" and outcome["food_here"]:
            utility += 20
        foods = outcome.get("food_positions", ())
        if action == "move_forward" and foods:
            x, y = outcome["position"]
            distance = min(abs(x - fx) + abs(y - fy) for fx, fy in foods)
            utility += max(0, 12 - distance)
        if outcome.get("position") in outcome.get("opponent_positions", ()):
            utility -= 100
        if outcome.get("smells_toxin", False) and action == "move_forward":
            utility += 20  # Leaving a toxic cell is preferable to lingering.
        return utility

    def evaluate(self, percept: dict, possible_actions=None) -> str:
        actions = possible_actions or self.POSSIBLE_ACTIONS
        optimal_action = None
        max_utility = float("-inf")
        for action in actions:
            score = self.compute_utility(self.simulate_action(percept, action))
            if score > max_utility:
                max_utility = score
                optimal_action = action
        return optimal_action

    def sense_and_act(self, percept):
        return self.evaluate(percept)


class LearningAgent:
    def __init__(self):
        self.performance_controller = UtilityBasedAgent()
        self.environment_critic = self._score_outcome
        self.adaptive_learner = self._adjust_parameters
        self.previous_score = None
        self.previous_action = None
        self.feedback_history = []
        self.learning_rate = 0.1

    def _score_outcome(self, percept: dict) -> float:
        current_score = percept.get("score", 0)
        feedback = 0 if self.previous_score is None else current_score - self.previous_score
        self.previous_score = current_score
        return feedback

    def _adjust_parameters(self, feedback: float):
        self.feedback_history.append(feedback)
        if len(self.feedback_history) > 50:
            del self.feedback_history[0]

        # The feedback describes the result of the previous action.  Adjust
        # that action's utility so future choices improve from experience.
        if self.previous_action is not None:
            old_utility = self.performance_controller.action_utilities[
                self.previous_action
            ]
            self.performance_controller.action_utilities[self.previous_action] = (
                old_utility + self.learning_rate * feedback
            )

    def execute_step(self, percept: dict) -> str:
        # Tutorial 02 order: performance controller selects an action, the
        # critic evaluates feedback, then the learner adapts future behaviour.
        action = self.performance_controller.evaluate(percept)
        feedback = self.environment_critic(percept)
        self.adaptive_learner(feedback)
        self.previous_action = action
        return action

    def sense_and_act(self, percept):
        return self.execute_step(percept)

    def evaluate(self, percept: dict) -> str:
        return self.execute_step(percept)


class GridGameGUI:
    """Visual comparison tool for the five Tutorial 02 agent programs."""

    AGENT_CLASSES = {
        "Simple Reflex": SimpleReflexAgent,
        "Model-Based Reflex": ModelBasedAgent,
        "Goal-Based": GoalBasedAgent,
        "Utility-Based": UtilityBasedAgent,
        "Learning": LearningAgent,
    }

    def __init__(self, root, width=10, height=10, num_food=12, num_opponents=2, num_traps=0, walls=None,
                 agent_class=SimpleReflexAgent):
        self.root = root
        self.root.title("IT3012 - Tutorial 02: Agent Architectures")
        self.config = dict(width=width, height=height, num_food=num_food,
                           num_opponents=num_opponents, num_traps=num_traps,
                           custom_walls=walls)
        self.running = False
        self.after_id = None

        self.env = VisualGridHuntGame(**self.config)
        self.agent = agent_class()
        default_name = next(
            name for name, cls in self.AGENT_CLASSES.items() if cls is agent_class
        )

        # Leave room below the canvas for the label, button, taskbar, and
        # window title bar so they never get pushed off the bottom of the
        # screen. winfo_screenheight() reports the FULL monitor height, it
        # does not subtract the taskbar, so we reserve extra margin for that.
        screen_h = root.winfo_screenheight()
        reserved_for_controls = 280
        max_canvas_dim = min(600, screen_h - reserved_for_controls)
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        header = tk.Frame(root, bg="#0f172a", padx=14, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Tutorial 02 • Agent Architecture Lab",
                 bg="#0f172a", fg="white", font=("Segoe UI", 15, "bold")).pack()

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h,
                                bg="white", highlightthickness=0)
        self.canvas.pack(padx=12, pady=(10, 4))

        self.status_label = tk.Label(
            root, text="Ready", font=("Segoe UI", 11, "bold"), fg="#0f172a"
        )
        self.status_label.pack(pady=(4, 2))
        self.detail_label = tk.Label(
            root, text="Score: 0  •  Steps: 0  •  Food remaining: 0",
            font=("Segoe UI", 10), fg="#475569"
        )
        self.detail_label.pack()

        controls = tk.Frame(root)
        controls.pack(pady=9)
        tk.Label(controls, text="Agent:", font=("Segoe UI", 10)).grid(
            row=0, column=0, padx=5
        )
        self.agent_choice = ttk.Combobox(
            controls, state="readonly", width=21,
            values=list(self.AGENT_CLASSES), font=("Segoe UI", 10)
        )
        self.agent_choice.set(default_name)
        self.agent_choice.grid(row=0, column=1, padx=5)

        self.start_btn = tk.Button(
            controls, text="Start", command=self.run_loop, width=10,
            bg="#1d4ed8", fg="white", font=("Segoe UI", 10, "bold")
        )
        self.start_btn.grid(row=0, column=2, padx=5)
        self.pause_btn = tk.Button(
            controls, text="Pause", command=self.pause, width=10,
            bg="#475569", fg="white", font=("Segoe UI", 10, "bold")
        )
        self.pause_btn.grid(row=0, column=3, padx=5)
        tk.Button(
            controls, text="Reset", command=self.reset, width=10,
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=4, padx=5)

        tk.Label(
            root, text="● Agent    ● Food    ■ Wall    ■ Opponent",
            font=("Segoe UI", 9), fg="#64748b"
        ).pack(pady=(0, 8))

        self.draw_grid()
        self._update_status("Ready", "No action")
        self._center_window(root)

    @staticmethod
    def _center_window(root):
        root.update_idletasks()
        width = root.winfo_reqwidth()
        height = root.winfo_reqheight()

        # Assume a ~60px taskbar and leave a safety margin so the button
        # can never end up hidden behind it.
        taskbar_estimate = 60
        usable_height = root.winfo_screenheight() - taskbar_estimate

        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = max(20, (usable_height // 2) - (height // 2))
        if y + height > usable_height:
            y = max(20, usable_height - height)

        root.geometry(f"{width}x{height}+{x}+{y}")
        root.resizable(False, False)

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#f1f5f9" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        # Draw each toxic trap as a purple diamond.
        for tx, ty in self.env.toxic_traps:
            center_x = (tx + 0.5) * self.cell_size
            center_y = (self.env.height - ty - 0.5) * self.cell_size
            radius = self.cell_size * 0.32
            self.canvas.create_polygon(
                center_x,
                center_y - radius,
                center_x + radius,
                center_y,
                center_x,
                center_y + radius,
                center_x - radius,
                center_y,
                fill="#9333ea",
                outline="#581c87",
                width=2,
            )

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        # Draw a directional agent so its internal heading is visible.
        ax, ay = self.env.agent_pos
        cx = (ax + 0.5) * self.cell_size
        cy = (self.env.height - ay - 0.5) * self.cell_size
        radius = self.cell_size * 0.32
        points = {
            "Up": (cx, cy - radius, cx - radius, cy + radius, cx + radius, cy + radius),
            "Down": (cx, cy + radius, cx - radius, cy - radius, cx + radius, cy - radius),
            "Left": (cx - radius, cy, cx + radius, cy - radius, cx + radius, cy + radius),
            "Right": (cx + radius, cy, cx - radius, cy - radius, cx - radius, cy + radius),
        }
        self.canvas.create_polygon(*points[self.env.facing], fill="#1d4ed8",
                                   outline="#1e3a8a", width=2)

    def _update_status(self, message, action):
        self.status_label.config(text=message)
        self.detail_label.config(
            text=(f"Score: {self.env.score}  •  Steps: {self.env.steps}  •  "
                  f"Food remaining: {len(self.env.food_positions)}  •  "
                  f"Facing: {self.env.facing}  •  Action: {action}")
        )

    def reset(self):
        self.pause()
        agent_class = self.AGENT_CLASSES[self.agent_choice.get()]
        self.env = VisualGridHuntGame(**self.config)
        self.agent = agent_class()
        self.draw_grid()
        self._update_status(f"Ready — {self.agent_choice.get()}", "None")
        self.start_btn.config(text="Start")

    def pause(self):
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.start_btn.config(text="Resume")

    def run_loop(self):
        if self.env.is_done():
            self.reset()
        self.running = True
        self.start_btn.config(text="Running", state="disabled")
        self.agent_choice.config(state="disabled")

        def step():
            if not self.running:
                self.start_btn.config(state="normal")
                self.agent_choice.config(state="readonly")
                return
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                if action == "halt":
                    self.running = False
                    self._update_status("Goal reached — agent halted", action)
                    self.start_btn.config(text="Start", state="normal")
                    self.agent_choice.config(state="readonly")
                    return
                self.env.execute_action(action)

                self.draw_grid()
                self._update_status(f"Running — {self.agent_choice.get()}", action)
                self.after_id = self.root.after(220, step)
            else:
                self.running = False
                if self.env.collision:
                    reason = "Stopped — collision"
                elif not self.env.food_positions:
                    reason = "Goal completed — all food collected"
                else:
                    reason = f"Stopped — {self.env.max_steps}-step limit reached"
                self._update_status(reason, "None")
                self.start_btn.config(text="Start", state="normal")
                self.agent_choice.config(state="readonly")

        step()


if __name__ == "__main__":
    root = tk.Tk()
    # Change only this line to compare the five Tutorial 02 architectures:
    # SimpleReflexAgent, ModelBasedAgent, GoalBasedAgent,
    # UtilityBasedAgent, or LearningAgent.
    ACTIVE_AGENT_CLASS = GoalBasedAgent
    app = GridGameGUI(root, width=12, height=12, num_food=15,
                       num_opponents=0, num_traps=0,
                       agent_class=ACTIVE_AGENT_CLASS)
    root.mainloop()
