from fastapi import WebSocketDisconnect, WebSocket
from fastapi.websockets import WebSocketState
import asyncio
from gai.common.logging import getLogger
logger = getLogger(__name__)
import json

'''
This class carries the websocket that bridges the RAG's output
to the API server.

On one end, it is connected to the output from RAG.index_async() 
which publishes the number of chunks processed via update_progress().

On the other end, it is connected to status_update_router API which 
broadcasts the status to clients connected to '/ws'.
'''

class StatusUpdater:

    def __init__(self):
        self.status = None
        self.websocket = None

    async def connect(self, websocket: WebSocket):
        self.websocket = websocket

    async def disconnect(self, websocket: WebSocket):
        await websocket.close()
        self.websocket = None

    # update_progress is the same as update_status,
    # but it returns an integer between 0 to 100
    async def update_progress(self, i, max):
        self.status = int(i*100/max)
        if self.websocket is not None:
            if self.websocket.client_state == WebSocketState.DISCONNECTED:
                logger.info("StatusUpdater: websocket is disconnected.")
                return
            logger.info(f"StatusUpdater: sending progress {self.status}")
            await asyncio.create_task(self.websocket.send_json({'progress': self.status}))

    async def update_stop(self):
        if self.websocket is not None:
            if self.websocket.client_state == WebSocketState.DISCONNECTED:
                logger.info("StatusUpdater: websocket is disconnected.")
                return
            logger.info(f"StatusUpdater: sending <stop>")
            await asyncio.create_task(self.websocket.send_text('<stop>'))

    def get_status(self):
        return self.status
