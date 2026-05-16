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

def encode_card_list(card_list):
    """Returns a multi-hot vector of the cards in the list."""
    encoded = [0.0] * len(CARD_VOCAB)
    for card in card_list:
        c_id = card.get('id')
        if c_id in CARD_VOCAB:
            idx = CARD_VOCAB.index(c_id)
            encoded[idx] += 1.0
    return encoded

def encode_powers(power_list):
    """
    Returns two vectors for powers: presence and amount.
    """
    presence = [0.0] * len(POWER_VOCAB)
    amounts = [0.0] * len(POWER_VOCAB)
    for p in power_list:
        p_id = p.get('id')
        if p_id in POWER_VOCAB:
            idx = POWER_VOCAB.index(p_id)
            presence[idx] = 1.0
            amount = p.get('amount', 0)
            amounts[idx] = amount / 10.0 # Normalize
    return presence + amounts

def encode_monsters(monsters_list):
    """
    Encodes up to MAX_MONSTERS.
    """
    monster_vectors = []
    # 4 base stats + len of power vector (presence + amount)
    single_monster_vec_size = 4 + len(POWER_VOCAB) * 2
    
    for i in range(MAX_MONSTERS):
        if i < len(monsters_list):
            m = monsters_list[i]
            hp_percent = m.get('current_hp', 0) / m.get('max_hp', 1) if m.get('max_hp', 0) > 0 else 0.0
            block = m.get('block', 0) / 50.0
            is_attacking = 1.0 if m.get('move_id', -1) != -1 and not m.get('is_gone', True) else 0.0
            attack_damage = m.get('move_base_damage', 0) * m.get('move_hits', 1) / 100.0
            
            powers = encode_powers(m.get('powers', []))
            
            monster_vectors.extend([hp_percent, block, is_attacking, attack_damage] + powers)
        else:
            monster_vectors.extend([0.0] * single_monster_vec_size)
            
    return monster_vectors

def create_state_vector(game_state):
    vector = []
    labels = [] 
    
    # 1. PLAYER CORE & RELICS
    vector.append(game_state.get('current_hp', 0) / game_state.get('max_hp', 1) if game_state.get('max_hp', 0) > 0 else 0.0)
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
    # Note: if not in combat, these will be empty/default, creating a zero-vector for this section
    combat_state = game_state.get('combat_state', {})
    player = combat_state.get('player', {})
    monsters = combat_state.get('monsters', [])
    
    vector.append(player.get('energy', 0) / 3.0) 
    labels.append("Plr_NRG")
    
    vector.append(player.get('block', 0) / 50.0)
    labels.append("Plr_Block")
    
    vector.extend(encode_powers(player.get('powers', [])))
    labels.extend([f"P_{p}" for p in POWER_VOCAB])
    labels.extend([f"Pc_{p}" for p in POWER_VOCAB])
    
    vector.extend(encode_card_list(combat_state.get('hand', [])))
    labels.extend([f"H_{c}" for c in CARD_VOCAB])
    
    vector.append(len(combat_state.get('draw_pile', [])) / 50.0)
    labels.append("Draw_Size")
    
    vector.append(len(combat_state.get('discard_pile', [])) / 50.0)
    labels.append("Discard_Size")
    
    vector.extend(encode_monsters(monsters))
    
    return vector, labels


# --- CALCULATE VECTOR SIZE ---
# We create a dummy state and run it through the vectorizer to get the true size.
# This is robust to future changes in the vectorization logic.
_dummy_game_state = {
    "current_hp": 80, "max_hp": 80,
    "relics": [{"id": "Burning Blood", "counter": -1}],
    "potions": [{"id": "Blood Potion"}],
    "combat_state": {
        "player": {"energy": 3, "block": 5, "powers": [{"id": "Strength", "amount": 2}]},
        "hand": [{"id": "Strike_R", "upgrades": 0}],
        "draw_pile": [{} for _ in range(10)],
        "discard_pile": [],
        "monsters": [{"current_hp": 50, "max_hp": 50, "block": 0, "move_id": 1, "move_base_damage": 6, "move_hits": 1, "powers": []}]
    }
}
VECTOR_SIZE = len(create_state_vector(_dummy_game_state)[0])

if __name__ == "__main__":
    # Test block to verify the new Relic/Potion fields
    print("Testing expanded vectorization...")
    # (Existing Postgres fetch logic)
    print(f"Calculated vector size: {VECTOR_SIZE}")