import base64
import threading
import time

import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, VideoProcessorBase, AudioProcessorBase
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
import pyttsx3


class VideoProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame):
        self.frame = frame.to_ndarray(format="bgr24")
        return frame

    def get_frame(self):
        return self.frame


class AudioProcessor(AudioProcessorBase):
    def __init__(self, assistant, recognizer, stop_callback):
        self.assistant = assistant
        self.recognizer = recognizer
        self.stop_callback = stop_callback

    def recv(self, audio_frame):
        audio_data = audio_frame.to_ndarray()
        # You would need to convert audio_data to a format that can be processed by the speech recognizer
        try:
            # Process the audio input and convert it to text
            prompt = self.recognizer.recognize_whisper(audio_data, model="base", language="english")
            # Use the assistant to generate a response
            self.assistant.answer(prompt, video_processor.get_frame(), self.stop_callback)
        except Exception as e:
            print("Audio processing error:", e)

        return audio_frame


class Assistant:
    def __init__(self, model):
        self.chain = self._create_inference_chain(model)
        self.last_prompt = None
        self.last_response = None
        self.tts_lock = threading.Lock()

    def answer(self, prompt, image, stop_listening_callback):
        if not prompt or image is None:
            return

        self.last_prompt = prompt
        print("Prompt:", prompt)

        # Encode the image as a JPEG
        _, buffer = cv2.imencode(".jpeg", image)

        # Convert the buffer to a base64 string
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        response = self.chain.invoke(
            {"prompt": prompt, "image_base64": image_base64},
            config={"configurable": {"session_id": "unused"}},
        ).strip()

        self.last_response = response
        print("Response:", response)

        if response:
            self._tts(response, stop_listening_callback)

    def _tts(self, response, stop_listening_callback):
        def speak():
            with self.tts_lock:
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 1.0)

                engine.say(response)
                engine.runAndWait()

                engine.stop()

            stop_listening_callback()

        threading.Thread(target=speak).start()

    def _create_inference_chain(self, model):
        SYSTEM_PROMPT = """
        You are being used to power a video assistant and you have knowledge on celebrities that will use the chat history and the image 
        provided by the user to answer its questions. Wait for the user prompt
        and greet them for the first time.

        recognize the actors in the image and answer the questions based on the actors in the image.

        recognize the image who is speaking with you and remember his name and whenever he asks respond accordingly.

        Do not use any emoticons or emojis. Do not use any special characters. Answer straight to the point. Don't tell
        the user about what you are learning.

        Be friendly and helpful. Show some personality. Do not be too formal.
        """

        prompt_template = ChatPromptTemplate.from_messages(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "human",
                    [
                        {"type": "text", "text": "{prompt}"},
                        {
                            "type": "image_url",
                            "image_url": "data:image/jpeg;base64,{image_base64}",
                        },
                    ],
                ),
            ]
        )

        chain = prompt_template | model | StrOutputParser()
        chat_message_history = ChatMessageHistory()
        return RunnableWithMessageHistory(
            chain,
            lambda _: chat_message_history,
            input_messages_key="prompt",
            history_messages_key="chat_history",
        )


def main():
    # Initialize recognizer and assistant model
    assistant_model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
    assistant = Assistant(assistant_model)

    # Streamlit UI setup
    st.title("SAGE: A Video Assistant")
    st.write("This application recognizes celebrities from your webcam feed and responds to your questions.")

    # WebRTC video and audio streams
    global video_processor
    video_processor = VideoProcessor()

    webrtc_streamer(
        key="video",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=lambda: video_processor,
        media_stream_constraints={"video": True, "audio": True},
    )

    recognizer = Recognizer()

    # Placeholder for showing responses
    prompt_placeholder = st.empty()
    response_placeholder = st.empty()

    # Add audio processor to process the speech
    webrtc_streamer(
        key="audio",
        mode=WebRtcMode.SENDRECV,
        audio_processor_factory=lambda: AudioProcessor(assistant, recognizer, lambda: None),
        media_stream_constraints={"audio": True},
    )

    # Loop to update UI with the assistant responses
    while True:
        if assistant.last_prompt and assistant.last_response:
            prompt_placeholder.markdown(f"*Prompt:* {assistant.last_prompt}")
            response_placeholder.markdown(f"*Response:* {assistant.last_response}")
        elif assistant.last_response:
            response_placeholder.markdown(f"*Response:* {assistant.last_response}")
        else:
            prompt_placeholder.markdown("*Prompt:* Waiting for input...")
            response_placeholder.markdown("*Response:* Waiting for response...")

        time.sleep(0.1)


if __name__ == "__main__":
    main()
