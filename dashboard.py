import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

def fetch_data(query):
    """Safely connects to Postgres, runs a query, and returns a Pandas DataFrame."""
    try:
        conn = psycopg2.connect(
            user="postgres",
            password="Bangladesh-2020", # <-- UPDATE THIS
            host="127.0.0.1",
            port="5432",
            database="slay_the_spire_ai"
        )
        # Pandas has a built-in function to turn SQL straight into a DataFrame!
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Database Error: {e}")
        return pd.DataFrame()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def generate_report():
    print("Pulling live data from the Spire...")

    # --- QUERY 1: Card Preferences ---
    # We want to see what cards the Ironclad relies on the most.
    card_query = """
        SELECT action_taken as card_played, COUNT(*) as times_played
        FROM sts_telemetry
        WHERE action_taken LIKE 'play%'
        GROUP BY action_taken
        ORDER BY times_played DESC
        LIMIT 10;
    """
    df_cards = fetch_data(card_query)

    # --- QUERY 2: Health Over Time ---
    # We track the average HP the bot has at each floor to see where it struggles.
    hp_query = """
        SELECT floor, AVG(hp_at_state) as avg_hp
        FROM sts_telemetry
        WHERE floor > 0
        GROUP BY floor
        ORDER BY floor ASC;
    """
    df_hp = fetch_data(hp_query)

    if df_cards.empty or df_hp.empty:
        print("Not enough data yet! Let the bot play a few more floors.")
        return

    # --- BUILD THE VISUALS ---
    # Create a dashboard with 2 subplots (1 row, 2 columns)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('Ironclad AI Performance Dashboard', fontsize=16, fontweight='bold')

    # Chart 1: Top 10 Cards Played
    # We use a horizontal bar chart so the card commands are easy to read
    ax1.barh(df_cards['card_played'], df_cards['times_played'], color='crimson')
    ax1.invert_yaxis() # Put the most played card at the top
    ax1.set_title('Top 10 Most Played Commands')
    ax1.set_xlabel('Times Played')
    ax1.set_ylabel('Command')
    ax1.grid(axis='x', linestyle='--', alpha=0.7)

    # Chart 2: Average HP by Floor
    # A line chart showing the bot's health trajectory
    ax2.plot(df_hp['floor'], df_hp['avg_hp'], color='seagreen', marker='o', linewidth=2)
    ax2.set_title('Average Health per Floor')
    ax2.set_xlabel('Floor Number')
    ax2.set_ylabel('Average HP')
    ax2.set_ylim(0, 80) # Ironclad starts with 80 Max HP
    ax2.grid(True, linestyle='--', alpha=0.7)

    # Clean up the layout and show the UI!
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    generate_report()