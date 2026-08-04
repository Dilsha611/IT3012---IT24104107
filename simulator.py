from grid_game import GridHuntGame
from agent import GreedyGridAgent

def run_grid_hunt():
    env = GridHuntGame()
    agent = GreedyGridAgent()

    print("=== UC Berkeley Style Small Grid Hunt Started ===")
    
    while not env.is_done():
        # Get percept and let agent decide action
        percept = env.get_percept(agent)
        action = agent.sense_and_act(percept)
        
        # Execute the action in the environment
        env.execute_action(agent, action)
        
        # Fetch updated percepts after action execution
        post_action_percept = env.get_percept(agent)
        
        # Print status log
        print(f"Action: {action:<5} | Pos: {post_action_percept['agent_pos']} | "
              f"Toxin Sensor: {post_action_percept['smells_toxin']} | "
              f"Food Left: {post_action_percept['remaining_food']} | "
              f"Score: {post_action_percept['score']}")

    print(f"\nGame Over! Final Score: {env.score} after {env.steps} steps.")

if __name__ == "__main__":
    run_grid_hunt()