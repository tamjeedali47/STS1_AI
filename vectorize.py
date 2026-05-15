import psycopg2
import json

# --- Use the game's actual enums to create a full vocabulary ---
from rs.calculator.enums.card_id import CardId
from rs.calculator.enums.power_id import PowerId
from rs.calculator.enums.relic_id import RelicId

# --- EXPANDED VOCABULARIES ---
CARD_VOCAB = [c.value for c in CardId]
POWER_VOCAB = [p.value for p in PowerId]
RELIC_VOCAB = [r.value for r in RelicId]

# Common Ironclad Potions
POTION_VOCAB = ["Blood Potion", "Strength Potion", "Attack Potion", "Block Potion", "Fire Potion"]

MAX_MONSTERS = 5 

def encode_relics(relics_list):
    """
    Returns two vectors:
    1. Presence (0 or 1)
    2. Counter (The numerical value, normalized)
    """
    presence = [0.0] * len(RELIC_VOCAB)
    counters = [0.0] * len(RELIC_VOCAB)
    
    for r in relics_list:
        r_id = r.get('id')
        if r_id in RELIC_VOCAB:
            idx = RELIC_VOCAB.index(r_id)
            presence[idx] = 1.0
            # Normalize counters. Pen Nib maxes at 10, Incense at 6, etc.
            # We'll use a generic /10.0 for now.
            count = r.get('counter', -1)
            if count > 0:
                counters[idx] = count / 10.0
                
    return presence + counters

def encode_potions(potions_list):
    """Returns a multi-hot of currently held potions."""
    encoded = [0.0] * len(POTION_VOCAB)
    for p in potions_list:
        p_id = p.get('id')
        if p_id in POTION_VOCAB:
            encoded[POTION_VOCAB.index(p_id)] += 1.0
    return encoded

# [previous encode_card_list, encode_powers, and encode_monsters functions remain the same]
# ... (Keeping logic from previous step for brevity) ...

def create_state_vector(game_state):
    vector = []
    labels = [] 
    
    # 1. PLAYER CORE & RELICS
    vector.append(game_state.get('current_hp', 0) / game_state.get('max_hp', 1))
    labels.append("Plr_HP%")
    
    # RELICS (Global state)
    relics = game_state.get('relics', [])
    vector.extend(encode_relics(relics))
    labels.extend([f"R_{r}" for r in RELIC_VOCAB])
    labels.extend([f"Rc_{r}" for r in RELIC_VOCAB]) # Counters
    
    # POTIONS
    potions = game_state.get('potions', [])
    vector.extend(encode_potions(potions))
    labels.extend([f"Pot_{p[:4]}" for p in POTION_VOCAB])

    # 2. COMBAT SPECIFICS
    combat_state = game_state.get('combat_state', {})
    player = combat_state.get('player', {})
    
    vector.append(player.get('energy', 0) / 3.0) 
    labels.append("Plr_NRG")
    
    # ... (Add Powers, Monsters, and Hand/Draw/Discard vectors as defined before) ...
    # This now creates a very comprehensive "snapshot" of the player's power level.
    
    return vector, labels

if __name__ == "__main__":
    # Test block to verify the new Relic/Potion fields
    print("Testing expanded vectorization...")
    # (Existing Postgres fetch logic)