import asyncio
from bleak import BleakScanner

async def scan_ble_devices():
    print("Scanning for BLE devices...")
    
    devices = await BleakScanner.discover(timeout=1.0)
    results = []

    for d in devices:
        if d.name:
            results.append({"name": d.name, "address": d.address})
    
    print(results)
    return results

if __name__ == "__main__":
    asyncio.run(scan_ble_devices())