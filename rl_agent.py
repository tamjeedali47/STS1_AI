import torch
import random

from brain import IroncladBrain
from vectorize import create_state_vector, VECTOR_SIZE
from rl_agent_handler import RLAgentHandler

# This defines what the AI can do. The index corresponds to the output of the neural network.
ACTION_SPACE = [
    "play 1", "play 2", "play 3", "play 4", "play 5",
    "play 6", "play 7", "play 8", "play 9", "play 10",
    "potion use 0", "potion use 1", "potion use 2",
    "end"
]

class RLAgent:
    def __init__(self, model_path=None):
        self.name = "DeepLearningAgent"

        self.brain = IroncladBrain(input_size=VECTOR_SIZE, num_actions=len(ACTION_SPACE))
        # This handler acts as the bridge between the game loop and the AI's brain.
        self.handlers = [RLAgentHandler(self)]
        if model_path:
            self.load_model(model_path)
        self.brain.eval() # Default to evaluation mode for inference

    def choose_action(self, game_state: dict, epsilon: float = 0.0) -> str:
        """
        Vectorize the state, ask the brain for a decision, and return the command.
        Includes epsilon-greedy exploration for training.
        """
        # Exploration: Choose a random action with probability epsilon
        if random.random() < epsilon:
            return random.choice(ACTION_SPACE)

        # Exploitation: Choose the best action the model knows
        # 1. Vectorize the game state
        state_vector, _ = create_state_vector(game_state)
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0) # Add batch dimension

        # 2. Get action scores from the brain
        with torch.no_grad():
            self.brain.eval() # Ensure we're in eval mode for inference
            action_scores = self.brain(state_tensor)

        # 3. Choose the action with the highest score
        best_action_index = torch.argmax(action_scores).item()
        return ACTION_SPACE[best_action_index]

    def load_model(self, path: str):
        """Loads a trained model's weights from a file."""
        try:
            self.brain.load_state_dict(torch.load(path))
            print(f"Successfully loaded model from {path}")
        except Exception as e:
            print(f"Error loading model: {e}")