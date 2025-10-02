import asyncio
import json
import nats

async def test_consumer():
    try:
        nc = await nats.connect('nats://localhost:4222')
        print('Connected to NATS, listening for BGP updates...')
        
        async def handle_message(msg):
            data = json.loads(msg.data.decode())
            print(f'Received: {data["type"]} from {data["peer"]}')
        
        await nc.subscribe('bgp.updates', cb=handle_message)
        
        # Keep running for 30 seconds
        await asyncio.sleep(30)
        await nc.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_consumer())
