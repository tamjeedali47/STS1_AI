import psycopg2
from psycopg2.extras import Json
import uuid
import sys

class STSLogger:
    def __init__(self, strategy_name):
        self.run_id = str(uuid.uuid4())
        self.strategy_name = strategy_name
        self.conn = None
        self.cur = None
        try:
            self.conn = psycopg2.connect(
                user="postgres",
                password="Bangladesh-2020", # <-- UPDATE THIS
                host="127.0.0.1",
                port="5432",
                database="slay_the_spire_ai"
            )
            self.cur = self.conn.cursor()
            # Send to error stream so it doesn't crash Slay the Spire's data pipe
            sys.stderr.write("\n[DB CONNECTED] Successfully hooked into Postgres!\n")
        except Exception as e:
            sys.stderr.write(f"\n[DB WARNING] Could not connect to Postgres. Error: {e}\n")

    def log_action(self, state_dict, action_command):
        if not self.cur:
            return 

        try:
            floor = state_dict.get('floor', 0)
            hp = state_dict.get('current_hp', 0)
            
            query = """
            INSERT INTO sts_telemetry (run_id, floor, game_state, action_taken, hp_at_state)
            VALUES (%s, %s, %s, %s, %s)
            """
            self.cur.execute(query, (self.run_id, floor, Json(state_dict), action_command, hp))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            sys.stderr.write(f"DB Log Error: {e}\n")