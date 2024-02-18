import websockets
import json


class StatusListener:

    def __init__(self, uri):
        self.uri = uri
        self.cancellation_token = None

    async def listen(self, callback=None):
        async with websockets.connect(self.uri) as websocket:
            print(f"Connected to {self.uri}")
            try:
                while self.cancellation_token is None:
                    message = await websocket.recv()
                    if callback:
                        callback(message)
                    print(f"Received status update: {message}")

                    if message == "<stop>":
                        self.cancellation_token = message

            except websockets.exceptions.ConnectionClosed as e:
                print(f"Connection closed: {e}")

    def stop(self):
        self.cancellation_token = "<stop>"
        print("Stopping listener")
        return self.cancellation_token
    
        