import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import av
import cv2

st.title("WebRTC Audio and Video Stream with Streamlit")

# Define client settings with TURN server for better connectivity
WEBRTC_CLIENT_SETTINGS = ClientSettings(
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},  # STUN server
            {
                "urls": "turn:turnserver.example.com:3478",  # Example TURN server (replace with a valid TURN server)
                "username": "user",
                "credential": "password"
            }
        ]
    },
    media_stream_constraints={"video": True, "audio": True},
)

# Video processing class
class VideoProcessor:
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# WebRTC component
webrtc_streamer(
    key="example",
    mode=WebRtcMode.SENDRECV,
    client_settings=WEBRTC_CLIENT_SETTINGS,
    video_processor_factory=VideoProcessor,
)
