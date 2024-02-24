# prettier-ignore
import asyncio
import os, sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from gai.common.StatusListener import StatusListener

if __name__ == "__main__":
    server_uri = "wss://gaiaio.ai/api/gen/v1/rag/ws"
    listener = StatusListener(server_uri)
    def callback(message): 
        return print(f"Callback: message={message}")
    asyncio.run(listener.listen(callback=callback))