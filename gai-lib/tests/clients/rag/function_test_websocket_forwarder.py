# prettier-ignore
import asyncio
import os, sys
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from gai.common.StatusListener import StatusListener
from gai.common.StatusUpdater import StatusUpdater

'''
This can work as a web socket reverse proxy service for RAG status updates.
Clients are connected to this via a websocket at ws://localhost:12032/ws.
The service listens to the RAG status at the remote host wss://gaigaio.ai/api/gen/v1/rag/ws and forwards updates to the client.
'''

status_updater = StatusUpdater()

# Part 1 - Start listener

listener = StatusListener("wss://gaiaio.ai/api/gen/v1/rag/ws")

# This callback is used by the listener to broadcast
# the status to the client
def callback(status): 
    global status_updater
    if status_updater is not None:
        asyncio.create_task(status_updater.websocket.send_json({"status":status}))

# Part 2 - Start server

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    global status_updater
    await ws.accept()
    await status_updater.connect(ws)
    listener_task = asyncio.create_task(listener.listen(callback=callback))
    receiver_task = asyncio.create_task(receive_text(ws))
    done, pending = await asyncio.wait(
        [receiver_task], return_when=asyncio.FIRST_COMPLETED
    )
    if receiver_task in done:
        listener_task.cancel()
    for task in pending:
        task.cancel()


async def receive_text(websocket: WebSocket):
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("Client disconnected normally.")
        # Handle any cleanup or post-disconnect actions here
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Handle other exceptions that could occur


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=12032)
