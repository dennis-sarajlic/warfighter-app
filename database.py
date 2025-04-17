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
