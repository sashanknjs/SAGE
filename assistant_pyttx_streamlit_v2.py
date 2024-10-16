import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode, RTCConfiguration

# Define a VideoTransformer class for video processing
class VideoTransformer(VideoTransformerBase):
    def transform(self, frame):
        # You can process the frame here if needed
        return frame

def main():
    st.title("Audio and Video Streaming with Streamlit-WeRTC")

    # Description of the application
    st.write("This app captures audio and video from your browser and streams it in real-time.")

    # Configure ICE servers
    rtc_configuration = RTCConfiguration({
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]  # Google's public STUN server
    })

    # Set up the WebRTC streamer
    webrtc_streamer(
        key="audio-video",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"video": True, "audio": True},
        rtc_configuration=rtc_configuration,
        video_processor_factory=VideoTransformer,
        async_processing=False,
    )

    # Debugging output
    st.write("If the video does not appear, check the browser's console for errors.")

if __name__ == "__main__":
    main()
