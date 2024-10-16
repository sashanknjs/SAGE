import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import cv2

st.title("WebRTC Audio and Video Stream with Streamlit")

# Define client settings
WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    media_stream_constraints={"video": True, "audio": True},
)

# Video processing class
class VideoProcessor:
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        # You can add processing logic here
        # For example, convert the image to grayscale
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# WebRTC component
webrtc_streamer(
    key="example",
    mode=WebRtcMode.SENDRECV,
    client_settings=WEBRTC_CLIENT_SETTINGS,
    video_processor_factory=VideoProcessor,
)

