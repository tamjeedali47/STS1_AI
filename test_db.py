import psycopg2

print("Setting up database schema...")
try:
    conn = psycopg2.connect(
        user="postgres",
        password="Bangladesh-2020", # <-- UPDATE THIS
        host="127.0.0.1",
        port="5432",
        database="slay_the_spire_ai"
    )
    cur = conn.cursor()

    # The schema we designed for the ML data
    create_table_query = """
    CREATE TABLE IF NOT EXISTS sts_telemetry (
        id SERIAL PRIMARY KEY,
        run_id UUID,
        floor INT,
        game_state JSONB,
        action_taken TEXT,
        hp_at_state INT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    cur.execute(create_table_query)
    conn.commit()
    print("✅ Table 'sts_telemetry' created successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if 'conn' in locals() and conn:
        cur.close()
        conn.close()