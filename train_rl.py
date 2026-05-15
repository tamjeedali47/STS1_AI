import torch
import torch.optim as optim
import torch.nn as nn
import random
from collections import deque
import sys

# From the project
from rs.ai.deep_learning.rl_agent import RLAgent, ACTION_SPACE
from vectorize import create_state_vector
from rs.api.client import Client
from rs.machine.game import Game

# --- Hyperparameters ---
LEARNING_RATE = 0.001
GAMMA = 0.99  # Discount factor for future rewards
EPSILON_START = 1.0  # Starting exploration rate
EPSILON_END = 0.01  # Minimum exploration rate
EPSILON_DECAY = 0.999 # How fast to reduce exploration
REPLAY_MEMORY_SIZE = 20000  # How many experiences to store
BATCH_SIZE = 128  # How many experiences to use for each learning step

def define_reward(game_state, prev_state):
    """A simple reward function to guide the agent."""
    reward = 0.0

    # Penalty for taking damage
    damage_taken = prev_state.get('current_hp', 0) - game_state.get('current_hp', 0)
    if damage_taken > 0:
        reward -= damage_taken * 0.5

    # Reward for healing
    health_gained = game_state.get('current_hp', 0) - prev_state.get('current_hp', 0)
    if health_gained > 0:
        reward += health_gained * 0.2

    # Big reward for winning, big penalty for losing
    if game_state.get('screen_type') == 'GAME_OVER':
        if game_state.get('screen_state', {}).get('victory'):
            reward += 200.0
        else:
            reward -= 200.0
            
    return reward

def train():
    print("Starting Reinforcement Learning training...")
    agent = RLAgent()
    optimizer = optim.Adam(agent.brain.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.MSELoss()
    memory = deque(maxlen=REPLAY_MEMORY_SIZE)
    epsilon = EPSILON_START

    client = Client()
    game = Game(client, agent)

    num_episodes = 1000
    for episode in range(num_episodes):
        game.start()
        game_state = client.get_game_state(True)
        
        done = False
        while not done:
            state_vector, _ = create_state_vector(game_state)
            
            # Choose action with exploration
            action_command = agent.choose_action(game_state, epsilon=epsilon)
            action_index = ACTION_SPACE.index(action_command)

            # Take action and observe outcome
            client.execute_command(action_command)
            next_game_state = client.get_game_state(True)
            
            done = next_game_state.get('screen_type') == 'GAME_OVER'
            reward = define_reward(next_game_state, game_state)
            next_state_vector, _ = create_state_vector(next_game_state)

            # Store experience
            memory.append((state_vector, action_index, reward, next_state_vector, done))
            
            game_state = next_game_state

            # Learn from a batch of experiences
            if len(memory) > BATCH_SIZE:
                batch = random.sample(memory, BATCH_SIZE)
                states, actions, rewards, next_states, dones = zip(*batch)

                states = torch.FloatTensor(states)
                actions = torch.LongTensor(actions)
                rewards = torch.FloatTensor(rewards)
                next_states = torch.FloatTensor(next_states)
                dones = torch.BoolTensor(dones)

                agent.brain.train() # Set brain to training mode
                current_q_values = agent.brain(states).gather(1, actions.unsqueeze(1))

                with torch.no_grad():
                    next_q_values = agent.brain(next_states).max(1)[0]
                    target_q_values = rewards + (GAMMA * next_q_values * ~dones)

                loss = loss_fn(current_q_values.squeeze(), target_q_values)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
        sys.stdout.write(f"\rEpisode {episode+1}/{num_episodes} | Epsilon: {epsilon:.3f}")
        sys.stdout.flush()

        if (episode + 1) % 50 == 0:
            save_path = f"ironclad_brain_rl_episode_{episode+1}.pth"
            torch.save(agent.brain.state_dict(), save_path)
            print(f"\nModel saved to {save_path}")

if __name__ == "__main__":
    try:
        train()
    except Exception as e:
        print(f"\nAn error occurred during training: {e}")
        import traceback
        traceback.print_exc()