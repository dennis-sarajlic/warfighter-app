from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO
import asyncio
import threading


from ble_scan import scan_ble_devices
from ble_subscribe import connect_and_subscribe, disconnect, set_socketio
from database import init_db, export_signals_to_csv, reset_db

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins=["http://127.0.0.1:5000"])

# Make socketio available to ble_subscribe
set_socketio(socketio)

# Create a persistent background event loop
event_loop = asyncio.new_event_loop()

def run_event_loop():
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()

# Start the thread when app starts
loop_thread = threading.Thread(target=run_event_loop, daemon=True)
loop_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan', methods=['GET'])
async def scan():
    devices = await scan_ble_devices()
    return jsonify(devices)

@app.route('/connect', methods=['GET'])
async def connect():
    address = request.args.get('device_id')
    if not address:
        return jsonify({'message': 'Missing device address'}), 400

    try:
        asyncio.run_coroutine_threadsafe(connect_and_subscribe(address), event_loop)
        return jsonify({'message': f'Connecting to {address}...'})
    except Exception as e:
        return jsonify({'message': f'Failed to connect: {e}'}), 500


@app.route('/disconnect', methods=['GET'])
async def disconnect_route():
    address = request.args.get('device_id')
    if not address:
        return jsonify({'message': 'Missing device address'}), 400

    try:
        await disconnect(address)
        return jsonify({'message': f'Disconnected from {address}'})
    except Exception as e:
        return jsonify({'message': f'Failed to disconnect: {e}'}), 500
    

# Add these routes to your Flask app

@app.route('/reset_db', methods=['POST'])
def handle_reset_db():
    """API endpoint to reset the database"""
    try:
        result = reset_db()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@app.route('/export_csv', methods=['GET'])
def handle_export_csv():
    """API endpoint to export signals data as CSV"""
    try:
        result = export_signals_to_csv()
        
        # Send file for download
        return send_file(
            result["filepath"],
            mimetype='text/csv',
            as_attachment=True,
            download_name=result["filename"]
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
    

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True)
