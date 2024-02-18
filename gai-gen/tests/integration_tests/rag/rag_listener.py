# prettier-ignore
import asyncio
import os, sys
sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from gai.common.StatusListener import StatusListener

if __name__ == "__main__":
    server_uri = "ws://localhost:12031/ws"
    listener = StatusListener(server_uri)
    def callback(message): 
        return print(f"Callback: message={message}")
    asyncio.run(listener.listen(callback=callback))