from flask import Flask, render_template, jsonify, request
import asyncio
import threading
from ble_scan import scan_ble_devices
from ble_subscribe import connect_and_subscribe, disconnect
from database import init_db

app = Flask(__name__)

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
        #asyncio.create_task(connect_and_subscribe(address))
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
    
@app.route('/plot_signals', methods=['GET'])
def latest_data(): 
    

if __name__ == '__main__':
    init_db()
    app.run(debug=True)