import asyncio
import cv2
from aiortc import (
    MediaStreamTrack,
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription
)
from av import VideoFrame
from aiortc.contrib.signaling import TcpSocketSignaling
import numpy as np


class BouncingBallTrack(MediaStreamTrack):
    """
    MediaStreamTrack class to generate continuous 2D frames of a bouncing ball
    """
    
    kind = "video"

    def __init__(self, frame_count):
        super().__init__()
        self.screen_width = 400
        self.screen_height = 300
        self.screen = np.zeros((self.screen_height, self.screen_width, 3), dtype=np.uint8)

        # Ball properties
        self.ball_radius = 20
        self.ball_color = (0, 0, 255)  # Blue in BGR color space
        self.x = self.screen_width // 2
        self.y = self.screen_height // 2  # Initial position
        self.ball_velocity = [20, 12]  # Initial velocity

        # Simulation parameters
        self.num_frames = 200
        self.fps = 30
        self.timestamp = 0

    def generateBallLocation(self):

        """
        Method: Generate the frame with the next ball position
        :return: frame, x_coordinate, y_coordinate
        """

        self.x += self.ball_velocity[0]
        self.y += self.ball_velocity[1]

        # Check for collisions with screen boundaries
        if self.x - self.ball_radius <= 0 or self.x + self.ball_radius >= self.screen_width:
            self.ball_velocity[0] *= -1
        if self.y - self.ball_radius <= 0 or self.y + self.ball_radius >= self.screen_height:
            self.ball_velocity[1] *= -1

        # Clear the screen
        self.screen.fill(0)

        # Draw the ball on the screen
        cv2.circle(self.screen, (self.x, self.y), self.ball_radius, self.ball_color, -1)

        return self.screen, int(self.x), int(self.y)

    async def recv(self):
        """
        Method: Async method to get and add frames to the MediaStreamTrack object
        :return: VideoFrame
        """
        image, self.x, self.y = self.generateBallLocation()
        frame = VideoFrame.from_ndarray(image, format='bgr24')
        frame.pts = self.timestamp
        frame.time_base = f'1/{self.fps}'
        self.timestamp += 1
        return frame


class Server:
    """
    The server class:
    1. Generates continuous 2D frames and sends it to client
    2. Received parsed coordinates from the client and computes the error in ball location
    """
    def __init__(self, timeout=False):
        self.pc = RTCPeerConnection()
        self.signaling = TcpSocketSignaling('localhost', 9000)
        self.timeout = timeout

    async def consume_signaling(self, pc, signaling):
        """
        Method: To consume signals from client
        :param pc: server RTCPeerConnection object
        :param signaling: client TcpSocketSignaling object
        """

        while True:
            obj = await signaling.receive()

            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)

                if obj.type == "offer":
                    await pc.setLocalDescription(await pc.createAnswer())
                    await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is None:
                break

    async def run_server(self, pc, signaling):
        """
        Method: The driver function for the server
        :param pc: server RTCPeerConnection object
        :param signaling: server TcpSocketSignaling object
        :return:
        """

        await signaling.connect()
        channel = pc.createDataChannel('channel')
        track = BouncingBallTrack(0)
        pc.addTrack(track)

        @channel.on("open")
        def on_open():
            pass

        @channel.on("message")
        def on_message(message):
            x, y = eval(message)
            error = np.sqrt(np.square(x - track.x) + np.square(y - track.y))
            print(f'Received client coordinate:{(x,y)}')
            print(f'Associated Error:{error}')
            print()

        # Creating and sending offer to client
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        await signaling.send(pc.localDescription)

        # Receiving answer from client
        answer = await signaling.receive()
        await pc.setRemoteDescription(RTCSessionDescription(sdp=answer.sdp, type=answer.type))
        print('ANSWER RECEIVED')

        if not self.timeout:
            await self.consume_signaling(pc, signaling)

    def server_main(self):
        """
        Method: Entry-point of server
        :return:
        """
        print("starting server")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.run_server(self.pc, self.signaling))
        except KeyboardInterrupt:
            pass
        finally:
            print('Exiting server')
            loop.run_until_complete(self.signaling.close())
            loop.run_until_complete(self.pc.close())


if __name__ == "__main__":
    server = Server()
    server.server_main()
