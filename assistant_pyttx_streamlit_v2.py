import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase

# Define a VideoTransformer class for video processing
class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        # You can process the frame here if needed
        return frame

def main():
    st.title("Audio and Video Streaming with Streamlit-WeRTC")

    # Description of the application
    st.write("This app captures audio and video from your browser and streams it in real-time.")

    # Set up the WebRTC streamer
    webrtc_streamer(
        key="audio-video",
        mode="sendonly",  # Only send video and audio, no need to receive data
        media_stream_constraints={"video": True, "audio": True},  # Enable video and audio capture
        video_processor_factory=VideoTransformer,  # Optional video processing
        async_processing=False,  # Synchronous processing for real-time streaming
    )

if __name__ == "__main__":
    main()
