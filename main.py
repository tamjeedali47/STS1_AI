import time
import traceback
import sys

from rs.ai.claw_is_law.claw_is_law import CLAW_IS_LAW
from rs.ai.peaceful_pummeling.peaceful_pummeling import PEACEFUL_PUMMELING
from rs.ai.pwnder_my_orbs.pwnder_my_orbs import PWNDER_MY_ORBS
from rs.ai.requested_strike.requested_strike import REQUESTED_STRIKE
from rs.ai.shivs_and_giggles.shivs_and_giggles import SHIVS_AND_GIGGLES
from rs.helper.seed import make_random_seed
from rs.api.client import Client
from rs.machine.game import Game
from rs.helper.logger import log, init_log, log_new_run_sequence
from rs.ai.mir_ironclad.ironclad_will import IRON_WILL


# --- SAFE IMPORT (No Prints allowed) ---
try:
    from logger import STSLogger
    DB_AVAILABLE = True
except Exception as e:
    log(f"WARNING: Database logger disabled. {e}")
    DB_AVAILABLE = False

run_seeds = []
run_amount = 1
strategy = IRON_WILL

if __name__ == "__main__":
    init_log()
    log("Starting up")
    log_new_run_sequence()
    
    try:
        client = Client()
        game = Game(client, strategy)
        
        # Attach logger if it successfully imported
        if DB_AVAILABLE:
            game.logger = STSLogger(strategy_name=strategy.name)

        if run_seeds:
            for seed in run_seeds:
                game.start(seed)
                game.run()
                time.sleep(1)
        else:
            for i in range(run_amount):
                game.start(make_random_seed())
                game.run()
                time.sleep(1)

    except Exception as e:
        log("Exception! " + str(e))
        log(traceback.format_exc())