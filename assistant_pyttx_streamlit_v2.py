import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoTransformerBase
import cv2
import numpy as np

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        self.frame = img
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def main():
    st.title("Webcam Stream using streamlit-webrtc")
    
    webrtc_ctx = webrtc_streamer(
        key="example",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )

    if webrtc_ctx.video_processor:
        if st.button("Capture Frame"):
            frame = webrtc_ctx.video_processor.frame
            if frame is not None:
                st.image(frame, channels="BGR")

if __name__ == "__main__":
    main()
