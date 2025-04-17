import asyncio
from bleak import BleakClient
from database import store_signal

# Replace with your characteristic UUIDs
GSR_UUID = "abcdef01-2345-6789-abcd-ef0123456789"
PPG_UUID = "87654321-4321-4321-4321-cba987654321"

# Global storage for device connections
clients = dict()
disconnect_events = dict()

def handle_gsr(sender, data):
    gsr_values = [int.from_bytes(data[i:i+2], byteorder='little') for i in range(0, len(data), 2)]
    print(f"GSR Data from {sender}: {gsr_values}")
    store_signal("GSR", gsr_values)

def handle_ppg(sender, data):
    ppg_values = [int.from_bytes(data[i:i+2], byteorder='little') for i in range(0, len(data), 2)]
    print(f"PPG Data from {sender}: {ppg_values}")
    store_signal("PPG", ppg_values)

async def connect_and_subscribe(address):
    if address in clients:
        print(f"Already connected to {address}")
        return

    print(address)
    client = BleakClient(address)
    print('yes1')
    await client.connect()
    print('yes')

    if client.is_connected:
        print(f"Connected to {address}")
        await client.start_notify(GSR_UUID, handle_gsr)
        await client.start_notify(PPG_UUID, handle_ppg)
        clients[address] = client

        # Create and wait on an Event
        disconnect_event = asyncio.Event()
        disconnect_events[address] = disconnect_event
        print(f"Waiting for disconnect signal for {address}...")
        await disconnect_event.wait()

        # Clean up once disconnect is triggered
        await disconnect(address)
    else:
        print(f"Failed to connect to {address}")

async def disconnect(address):
    client = clients.get(address)
    if not client:
        print(f"No active connection to {address}")
        return

    try:
        await client.stop_notify(GSR_UUID)
        await client.stop_notify(PPG_UUID)
        await client.disconnect()
        print(f"Disconnected from {address}")
    except Exception as e:
        print(f"Error disconnecting from {address}: {e}")
    finally:
        clients.pop(address, None)
        event = disconnect_events.pop(address, None)
        if event:
            event.set()  # Ensure it doesn't block if disconnect called first

# Example manual trigger
if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) != 2:
            print("Usage: python script.py <BLE_DEVICE_ADDRESS>")
            return
        address = sys.argv[1]
        # Start connection
        connect_task = asyncio.create_task(connect_and_subscribe(address))

        # Optional: simulate disconnect after 60 seconds
        await asyncio.sleep(60)
        await disconnect(address)

        await connect_task  # Wait for cleanup

    asyncio.run(main())