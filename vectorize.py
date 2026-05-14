import psycopg2
import json

def create_state_vector(game_state):
    """
    Translates a JSON game state into a flat numerical vector for a Neural Network.
    """
    vector = []
    
    # 1. Normalize Player Stats
    current_hp = game_state.get('current_hp', 0)
    max_hp = game_state.get('max_hp', 1) # Prevent divide by zero
    hp_percent = current_hp / max_hp
    vector.append(hp_percent)
    
    # 2. Normalize Energy
    # The combat_state might be missing if we are on a map screen
    combat_state = game_state.get('combat_state', {})
    player_combat = combat_state.get('player', {})
    energy = player_combat.get('energy', 0)
    vector.append(energy / 3.0) # Assuming 3 is base energy
    
    # 3. Hand Size (Simple metric)
    hand = combat_state.get('hand', [])
    vector.append(len(hand) / 10.0) # Normalizing against a max hand size of 10
    
    return vector

print("Pulling a sample state from Postgres...")
try:
    conn = psycopg2.connect(
        user="postgres",
        password="Bangladesh-2020", # <-- UPDATE THIS
        host="127.0.0.1",
        port="5432",
        database="slay_the_spire_ai"
    )
    cur = conn.cursor()
    
    # Grab one combat action to test
    cur.execute("SELECT action_taken, game_state FROM sts_telemetry WHERE action_taken LIKE 'play%' LIMIT 1;")
    row = cur.fetchone()
    
    if row:
        action = row[0]
        raw_json = row[1]
        
        # In psycopg2, JSONB columns are sometimes returned as dicts automatically.
        # If it's a string, we parse it.
        state_dict = raw_json if isinstance(raw_json, dict) else json.loads(raw_json)
        
        state_vector = create_state_vector(state_dict)
        
        print(f"\nAction Taken: {action}")
        print(f"Neural Network Input Vector: {state_vector}")
        print("\n[ HP%, Energy%, Hand_Size% ]")
    else:
        print("No combat actions found in the database yet!")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals() and conn:
        cur.close()
        conn.close()