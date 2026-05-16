import time
import traceback
import sys

# --- CHOOSE YOUR MODE ---
# Set to True for continuous overnight runs, False to run 'run_amount' of games and then stop.
CONTINUOUS_RUN_MODE = False
DATA_COLLECTION_MODE = False # Set to False to use your newly trained AI!

# If not in data collection mode, specify the trained model to use.
MODEL_PATH = "ironclad_brain_bc.pth" # This is the model you just trained.

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
run_amount = 1 # Let's watch one full game.

if __name__ == "__main__":
    init_log()
    log_new_run_sequence()

    # Set up client and strategy once
    client = Client()
    if DATA_COLLECTION_MODE:
        strategy = IRON_WILL
    else:
        from rl_agent import RLAgent
        strategy = RLAgent(model_path=MODEL_PATH)

    game = Game(client, strategy)
    if DB_AVAILABLE:
        game.logger = STSLogger(strategy_name=strategy.name)

    if CONTINUOUS_RUN_MODE:
        log("Starting up in continuous run mode.")
        # Infinite loop for continuous runs. This will run games back-to-back until the script is manually stopped.
        while True:
            try:
                log("Starting a new run...")
                game.start(make_random_seed())
                game.run()
                log("Run finished successfully.")

            except Exception as e:
                log(f"An error occurred during the run: {e}")
                log(traceback.format_exc())
                log("Attempting to recover and start a new run.")

            log("Waiting for 5 seconds before the next run.")
            time.sleep(5)
    else:
        log(f"Starting up for {run_amount} run(s).")
        try:
            for i in range(run_amount):
                log(f"Starting run {i + 1} of {run_amount}...")
                game.start(make_random_seed())
                game.run()
                log(f"Run {i + 1} finished.")
                time.sleep(1)
            log("All specified runs completed.")

        except Exception as e:
            log("Exception! " + str(e))
            log(traceback.format_exc())