import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoTransformerBase
import av
import cv2

class VideoProcessor(VideoTransformerBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # You can add any processing to the frame here if needed.
        # For now, it's just returning the original frame.
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")

def main():
    st.title("Webcam Stream using streamlit-webrtc")
    
    # Start the webrtc_streamer
    webrtc_ctx = webrtc_streamer(
        key="example",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=VideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )

    # Optional check to see if the video_processor is active
    if webrtc_ctx.video_processor:
        st.write("Webcam is active.")
    
if __name__ == "__main__":
    main()
