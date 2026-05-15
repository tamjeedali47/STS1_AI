import torch
import torch.optim as optim
import torch.nn as nn
import pandas as pd
import psycopg2
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset, DataLoader

# From the project
from brain import IroncladBrain
from vectorize import create_state_vector, VECTOR_SIZE
from rl_agent import ACTION_SPACE

# --- Hyperparameters ---
LEARNING_RATE = 0.001
BATCH_SIZE = 64
EPOCHS = 10
MODEL_SAVE_PATH = "ironclad_brain_bc.pth"

def fetch_training_data():
    """Connects to Postgres and fetches all telemetry data."""
    print("Fetching training data from database...")
    try:
        conn = psycopg2.connect(
            user="postgres",
            password="Bangladesh-2020", # Make sure this is correct
            host="127.0.0.1",
            port="5432",
            database="slay_the_spire_ai"
        )
        df = pd.read_sql_query("SELECT game_state, action_taken FROM sts_telemetry WHERE action_taken = ANY(%s)", conn, params=(ACTION_SPACE,))
        print(f"Successfully fetched {len(df)} relevant records.")
        return df
    except Exception as e:
        print(f"Database Error: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def process_data(df):
    """Converts the DataFrame into tensors for training."""
    print("Processing data and creating vectors...")
    
    # Convert game state JSONs to numerical vectors
    state_vectors = [create_state_vector(row['game_state'])[0] for _, row in df.iterrows()]
    
    # Convert action command strings to numerical labels (their index in ACTION_SPACE)
    action_labels = [ACTION_SPACE.index(row['action_taken']) for _, row in df.iterrows()]

    X = torch.FloatTensor(state_vectors)
    y = torch.LongTensor(action_labels)
    
    return X, y

def train():
    df = fetch_training_data()
    if df.empty:
        print("No data to train on. Run the bot in data collection mode first.")
        return

    X, y = process_data(df)

    # Split data into training and validation sets
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    # Initialize model, loss function, and optimizer
    model = IroncladBrain(input_size=VECTOR_SIZE, num_actions=len(ACTION_SPACE))
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.CrossEntropyLoss() # CrossEntropyLoss is ideal for classification tasks

    print("\n--- Starting Training ---")
    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            predictions = model(batch_X)
            loss = loss_fn(predictions, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        # Validation phase
        model.eval()
        correct = 0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                predictions = model(batch_X)
                predicted_labels = torch.argmax(predictions, dim=1)
                correct += (predicted_labels == batch_y).sum().item()
        
        avg_loss = total_loss / len(train_loader)
        accuracy = 100 * correct / len(val_dataset)
        print(f"Epoch {epoch+1}/{EPOCHS} | Avg Loss: {avg_loss:.4f} | Validation Accuracy: {accuracy:.2f}%")

    # Save the trained model
    torch.save(model.state_dict(), MODEL_SAVE_PATH)
    print(f"\nTraining complete. Model saved to '{MODEL_SAVE_PATH}'")

if __name__ == "__main__":
    train()