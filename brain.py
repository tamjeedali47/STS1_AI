import torch
import torch.nn as nn
import torch.nn.functional as F

class IroncladBrain(nn.Module):
    def __init__(self, input_size, num_actions):
        super(IroncladBrain, self).__init__()
        
        # --- THE ARCHITECTURE ---
        # Think of these layers as the AI's "thought process".
        # 1. The Input Layer: Takes the raw game state (HP, Cards, Enemies)
        self.fc1 = nn.Linear(input_size, 256)
        
        # 2. The Hidden Layers: This is where it learns strategy (e.g., "If I have low HP AND Pen Nib is 9...")
        self.fc2 = nn.Linear(256, 128)
        self.fc3 = nn.Linear(128, 64)
        
        # 3. The Output Layer: A score for every possible action it could take.
        self.fc_out = nn.Linear(64, num_actions)
        
        # Dropout helps prevent the AI from "memorizing" specific runs
        self.dropout = nn.Dropout(p=0.2)

    def forward(self, state_vector):
        """This function defines how the data flows through the brain."""
        
        # Pass the state through the first layer and apply ReLU (an activation function)
        x = F.relu(self.fc1(state_vector))
        x = self.dropout(x)
        
        # Pass through second layer
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        
        # Pass through third layer
        x = F.relu(self.fc3(x))
        
        # The final output (Raw scores for each action)
        action_scores = self.fc_out(x)
        
        return action_scores

# --- TESTING THE PLUMBING ---
if __name__ == "__main__":
    print("Initializing the Ironclad AI...")
    
    # In a real implementation, you would import your vectorizer and action definitions
    # to get these sizes dynamically.
    # from vectorize import VECTOR_SIZE, ACTION_SPACE_SIZE

    # 1. Define our sizes based on our vectorizer
    # This number should be the length of the vector produced by create_state_vector()
    VECTOR_SIZE = 500 # Example size, should be calculated from vectorize.py
    
    # How many things can the bot do? 
    # E.g., Play Card 1-10, End Turn, Drink Potion 1-3, etc.
    # This should match the number of possible commands you want the AI to choose from.
    ACTION_SPACE_SIZE = 14 # e.g., 10 cards + 3 potions + 1 end turn

    # 2. Create the brain
    model = IroncladBrain(input_size=VECTOR_SIZE, num_actions=ACTION_SPACE_SIZE)
    print(f"Brain Created! Total parameters: {sum(p.numel() for p in model.parameters())}")
    
    # 3. Test it with "Fake Data" (A random tensor)
    # The shape should be [batch_size, vector_size]. Here, batch_size is 1.
    fake_game_state = torch.rand(1, VECTOR_SIZE) 
    
    # 4. Ask the brain what to do
    predictions = model(fake_game_state)
    
    print("\nThe Brain's initial, untrained output (Raw Scores):")
    print(predictions)
    
    # Find the action with the highest score
    best_action_index = torch.argmax(predictions).item()
    print(f"\nThe AI chose Action Index: {best_action_index}")