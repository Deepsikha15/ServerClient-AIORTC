import asyncio
from unittest.mock import MagicMock
from server import BouncingBallTrack, Server
from client import DisplayTrack, process_a, Client
from av import VideoFrame
import numpy as np
import cv2
from asynctest import CoroutineMock, patch
from aiortc import RTCSessionDescription, RTCPeerConnection, RTCDataChannel


def generate_frame(ts, fps):
    """
    Method: Helper method to generate and test server methods
    """

    image = np.zeros((300, 400, 3), dtype=np.uint8)
    cv2.circle(image, (20, 12), 20, (0, 0, 255), -1)
    frame = VideoFrame.from_ndarray(image, format='bgr24')
    frame.pts = ts
    frame.time_base = f'1/{fps}'
    return frame.to_ndarray(format='rgb24')


def test_generateBallLocation():
    """
    Test: test BouncingBallTrack.generateBallLocation()
    """

    track = BouncingBallTrack(0)
    track.x = 200
    track.y = 150
    track.ball_velocity = [10, 5]
    canvas, x, y = track.generateBallLocation()
    assert x == 210  # New x-coordinate
    assert y == 155  # New y-coordinate


def test_process_a():
    """
    Test: Test the target process for the Process:process_a
    """

    queue = MagicMock()
    coordinates = MagicMock()
    frame1 = generate_frame(0, 20)
    frame2 = generate_frame(1, 30)
    queue.get.side_effect = [frame1, frame2, None]
    process_a(queue, coordinates)
    assert coordinates[0] != 0.0  # correct parsing will not give default coordinate value
    assert coordinates[1] != 0.0
    assert queue.get.call_count == 3
    queue.get.assert_called_with()


def test_recv():
    """
    Test: Test DisplayTrack.recv()
    :return:
    """

    track = BouncingBallTrack(0)
    image, x, y = generate_frame(0, 30), 200, 150
    track.generateBallLocation = MagicMock(return_value=(image, x, y))

    frame = asyncio.run(track.recv())

    assert frame is not None
    assert np.sum(frame.to_ndarray()) == np.sum(image)
    assert frame.pts == 0


async def run_server(server):
    """
    Method: Helper method to test server
    """

    pc = CoroutineMock()
    signaling = CoroutineMock()

    # Patch async methods to return coroutine objects
    pc.createOffer = CoroutineMock(return_value='offer')
    pc.setLocalDescription = CoroutineMock(return_value=RTCSessionDescription(sdp='dummy', type='offer'))
    signaling.send = CoroutineMock(return_value='server_offer')
    signaling.receive = CoroutineMock(return_value=RTCSessionDescription(sdp='client_sdp',type='answer'))
    pc.setRemoteDescription = CoroutineMock(return_value=None)
    signaling.connect = CoroutineMock()
    signaling.send.return_value = None
    signaling.close.return_value = None
    pc.close.return_value = None

    await server.run_server(pc, signaling)


@patch("server.RTCPeerConnection")
def test_run_server(mock_peer_connection):
    """
    Test: Test server
    """

    # Create mock objects
    mock_pc = MagicMock()
    mock_channel = MagicMock()
    mock_track = MagicMock()

    # Configure mock objects
    mock_peer_connection.return_value = mock_pc
    mock_pc.createDataChannel.return_value = mock_channel
    mock_pc.addTrack.return_value = mock_track

    server = Server()

    # Patch the consume_signaling method
    server.consume_signaling = CoroutineMock(return_value=None)

    # Run the server
    asyncio.run(run_server(server))

    # Verify the method calls
    mock_peer_connection.assert_called_once()


async def run_client(client):
    """
    Test: Test client
    """

    pc = CoroutineMock()
    signaling = CoroutineMock()

    # Patch async methods to return coroutine objects
    pc.createAnswer = CoroutineMock(return_value='answer')
    pc.setLocalDescription = CoroutineMock(return_value=RTCSessionDescription(sdp='dummy', type='answer'))
    signaling.send = CoroutineMock(return_value='client_answer')
    signaling.receive = CoroutineMock(return_value=RTCSessionDescription(sdp='server_sdp',type='offer'))
    pc.setRemoteDescription = CoroutineMock(return_value=None)
    signaling.connect = CoroutineMock()
    signaling.send.return_value = None
    signaling.close.return_value = None
    pc.close.return_value = None

    await client.run_client(pc, signaling)


@patch("client.RTCPeerConnection")
def test_run_client(mock_peer_connection):
    # Create mock objects
    mock_pc = MagicMock()

    # Configure mock objects
    mock_peer_connection.return_value = mock_pc
    client = Client()

    # Patch the consume_signaling method
    client.consume_signaling = CoroutineMock(return_value=None)

    asyncio.run(run_client(client))

    mock_peer_connection.assert_called_once()