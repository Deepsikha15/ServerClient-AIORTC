import asyncio
import cv2
from aiortc import (
    MediaStreamTrack,
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription
)
from aiortc.contrib.signaling import TcpSocketSignaling
import numpy as np
import matplotlib.pyplot as plt
import multiprocessing


class DisplayTrack(MediaStreamTrack):
    """
    MediaStreamTrack class to consume and display continuous 2D frames of a bouncing ball received from the server
    """
    kind = "video"

    def __init__(self, track, datachannel=None):
        super().__init__()
        self.track = track
        self.queue = multiprocessing.Queue()
        self.coordinates = multiprocessing.Array('d', 2)
        self.coordinates[0], self.coordinates[1] = 0.0, 0.0
        self.datachannel = datachannel

    async def recv(self):
        """
        Method: Display Frames received from server
        """

        for i in range(30):
            frame = await self.track.recv()
            if frame is not None:
                self.queue.put(frame.to_ndarray(format='rgb24'))
                with self.coordinates.get_lock():
                    x, y = self.coordinates[0], self.coordinates[1]
                    channel_send(self.datachannel, str((x,y)))

                # displaying the frame
                image = frame.to_ndarray(format="bgr24")
                plt.title('Bouncing Ball')
                plt.axis("off")
                plt.imshow(image)
                plt.show(block=False)
                plt.pause(0.5)
                await asyncio.sleep(0.5)

            else:
                self.queue.put(None)
        plt.close()


def process_a(queue, coordinates):
    """
    Process: The target of the process spawned by the client main thread
    :param queue: multiprocessing.Queue to get frames
    :param coordinates:  multiprocessing.Array to get coordinates of the ball
    :return:
    """

    while True:
        frame = queue.get()
        if frame is None:
            break
        x, y = parse_frame(frame)
        with coordinates.get_lock():
            coordinates[0], coordinates[1] = x, y


def parse_frame(frame):
    """
    Method: To parse a frame and get the coordinates of the ball
    :param frame: Numpy frame
    :return: (x,y) Coordinates of the center of the ball
    """

    # The lower and upper threshold for blue color in HSV space
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])

    # Convert the image to the HSV color space
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create a mask for the blue color range
    mask = cv2.inRange(hsv_image, lower_blue, upper_blue)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find the contour with the largest area (the circle)
    largest_contour = max(contours, key=cv2.contourArea)

    # Find the minimum enclosing circle for the largest contour
    ((center_x, center_y), radius) = cv2.minEnclosingCircle(largest_contour)

    # The coordinates of the center of the circle
    return int(center_x), int(center_y)


def channel_log(sender, recipient, message):
    """
    Method: Logging data to be sent to server
    :param sender: string client
    :param recipient: string server
    :param message: string coordinates
    :return:
    """
    print("%s -> %s: %s" % (sender, recipient, message))


def channel_send(channel, message):
    """
    Method: To send message to the server across a data channel
    :param channel: RTCDataChannel object
    :param message: string message
    :return:
    """
    send_coordinates = "Coordinates are " + message
    channel_log("CLIENT", "SERVER", send_coordinates)
    channel.send(message)


class Client:
    """
    The client class
    1. Displays frames received from server
    2. Spawns a separate process to parse the frames to compute ball coordinates
    3. Sends the coordinates to the server across a datachannel
    """

    def __init__(self, timeout=False):
        self.pc = RTCPeerConnection()
        self.signaling = TcpSocketSignaling('localhost', 9000)
        self.timeout = timeout

    async def consume_signaling(self, pc, signaling):
        """
        Method: To consume signals from server
        :param pc: client RTCPeerConnection object
        :param signaling: server TcpSocketSignaling object
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

    async def run_client(self, pc, signaling):
        """
        Method: The driver function for the client
        :param pc: client RTCPeerConnection object
        :param signaling: client TcpSocketSignaling object
        :return:
        """
        await self.signaling.connect()

        @pc.on("track")
        async def on_track(track):
            print("Track received %s" % track.kind)

            @pc.on("datachannel")
            async def on_channel(channel):
                local_track = DisplayTrack(track, channel)

                # spawning a process to parse frames
                process_a_instance = multiprocessing.Process(target=process_a, args=(local_track.queue, local_track.coordinates))
                process_a_instance.start()
                await local_track.recv()
                local_track.queue.put(None)
                process_a_instance.join()

        # Receiving server offer
        server_offer = await signaling.receive()
        await pc.setRemoteDescription(RTCSessionDescription(sdp=server_offer.sdp, type=server_offer.type))
        print('OFFER RECEIVED')

        # Sending client answer
        client_answer = await pc.createAnswer()
        await pc.setLocalDescription(client_answer)
        await signaling.send(pc.localDescription)

        if not self.timeout:
            await self.consume_signaling(pc, signaling)

    def client_main(self):
        """
        Method: Entry-point of client
        :return:
        """
        print("Starting client")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self.run_client(self.pc, self.signaling))
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(self.signaling.close())
            loop.run_until_complete(self.pc.close())
            print('Exiting client')


if __name__ == "__main__":
    client = Client()
    client.client_main()
