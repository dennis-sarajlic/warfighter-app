import sqlite3

def init_db():
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ppg INTEGER,
            gsr INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def store_signal(signal_type, values):
    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    if signal_type == "PPG":
        for value in values:
            cursor.execute("INSERT INTO signals (ppg, gsr) VALUES (?, NULL)", (value,))
    elif signal_type == "GSR":
        for value in values:
            cursor.execute("INSERT INTO signals (ppg, gsr) VALUES (NULL, ?)", (value,))
    
    conn.commit()
    conn.close()

def enough_data(min_samples=25 * 120):
    min_samples = 25 * 120  # Sampling rate * seconds

    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    # Count the number of non-null PPG and GSR entries
    cursor.execute("SELECT COUNT(ppg) FROM signals WHERE ppg IS NOT NULL")
    ppg_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(gsr) FROM signals WHERE gsr IS NOT NULL")
    gsr_count = cursor.fetchone()[0]

    conn.close()

    # Return True only if both counts are equal and at least min_samples
    return ppg_count >= min_samples and gsr_count >= min_samples

def get_signals(samples=25 * 120):
    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    # Get the PPG and GSR values separately
    cursor.execute("""
        SELECT id, ppg FROM signals 
        WHERE ppg IS NOT NULL 
        ORDER BY id DESC 
        LIMIT ?
    """, (samples,))
    ppg_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, gsr FROM signals 
        WHERE gsr IS NOT NULL 
        ORDER BY id DESC 
        LIMIT ?
    """, (samples,))
    gsr_data = cursor.fetchall()
    
    conn.close()
    
    # Extract the values (ignoring IDs)
    ppg = [row[1] for row in ppg_data]
    gsr = [row[1] for row in gsr_data]
    
    # Reverse to return in chronological order
    ppg.reverse()
    gsr.reverse()
    
    return ppg, gsr