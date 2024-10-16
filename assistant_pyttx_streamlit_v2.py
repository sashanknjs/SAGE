import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av

# Title of the app
st.title("Audio and Video Streaming with Streamlit WebRTC")

# Define a class for video transformation (optional)
class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        # You can add any image processing here
        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Start the WebRTC streamer with video transformation
webrtc_streamer(key="example", video_frame_callback=VideoTransformer().transform)

# Instructions for users
st.write("Click 'START' to begin streaming your webcam video and audio.")
