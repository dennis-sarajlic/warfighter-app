import sqlite3
import csv
import os
from datetime import datetime

def init_db():
    conn = sqlite3.connect('signals.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gsr_signal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gsr INTEGER
        );
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ppg_signal (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ppg INTEGER      
        );
    ''')
    conn.commit()
    conn.close()

def store_signal(signal_type, values):
    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    if signal_type == "PPG":
        for value in values:
            cursor.execute("INSERT INTO ppg_signal (ppg) VALUES (?)", (value,))
    elif signal_type == "GSR":
        for value in values:
            cursor.execute("INSERT INTO gsr_signal (gsr) VALUES (?)", (value,))
    
    conn.commit()
    conn.close()

def enough_data(min_samples=25 * 120):
    min_samples = 25 * 120  # Sampling rate * seconds

    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    # Count the number of non-null PPG and GSR entries
    cursor.execute("SELECT COUNT(ppg) FROM ppg_signal WHERE ppg IS NOT NULL")
    ppg_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(gsr) FROM gsr_signal WHERE gsr IS NOT NULL")
    gsr_count = cursor.fetchone()[0]

    conn.close()

    # Return True only if both counts are equal and at least min_samples
    return ppg_count >= min_samples and gsr_count >= min_samples

def get_signals(samples=25 * 120):
    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()

    # Get the PPG and GSR values separately
    cursor.execute("""
        SELECT id, ppg FROM ppg_signal  
        LIMIT ?
    """, (samples,))
    ppg_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT id, gsr FROM gsr_signal
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

def reset_db():
    """Deletes the database file and reinitializes the schema."""
    db_path = "signals.db"
    
    # Delete the file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Recreate the database schema
    init_db()

    return {"success": True, "message": "Database file deleted and reset successfully"}


def export_signals_to_csv():
    """Export all signal data to a CSV file"""
    
    conn = sqlite3.connect("signals.db")
    cursor = conn.cursor()
    
    # Get all signals
    cursor.execute("""
    SELECT ppg_signal.id, ppg_signal.ppg, gsr_signal.gsr
    FROM ppg_signal
    INNER JOIN gsr_signal ON ppg_signal.id = gsr_signal.id
    """)
    all_signals = cursor.fetchall()
    
    conn.close()
    
    # Create a timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"signals_export_{timestamp}.csv"
    
    # Ensure the exports directory exists
    if not os.path.exists("exports"):
        os.makedirs("exports")
        
    filepath = os.path.join("exports", filename)
    
  # Write data to CSV
    with open(filepath, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header
        csv_writer.writerow(['id', 'ppg', 'gsr'])
        # Write data
        csv_writer.writerows(all_signals)
    
    return {
        "success": True, 
        "message": "Data exported successfully",
        "filename": filename,
        "filepath": filepath
    }