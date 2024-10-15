import base64
from threading import Lock, Thread
import time

import cv2
import streamlit as st
from cv2 import VideoCapture, imencode
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI
from speech_recognition import Microphone, Recognizer, UnknownValueError
import pyttsx3
import threading  # For running TTS asynchronously

class WebcamStream:
    def __init__(self):     
        self.stream = VideoCapture(index=0)
        _, self.frame = self.stream.read()
        self.running = False
        self.lock = Lock()

    def start(self):
        if self.running:
            return self

        self.running = True
        self.thread = Thread(target=self.update, args=())
        self.thread.start()
        return self

    def update(self):
        while self.running:
            _, frame = self.stream.read()

            self.lock.acquire()
            self.frame = frame
            self.lock.release()

    def read(self, encode=False):
        self.lock.acquire()
        frame = self.frame.copy()
        self.lock.release()

        if encode:
            _, buffer = imencode(".jpeg", frame)
            return base64.b64encode(buffer).decode('utf-8')

        return frame

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join()

    def _exit_(self, exc_type, exc_value, exc_traceback):
        self.stream.release()


class Assistant:
    def __init__(self, model):
        self.chain = self._create_inference_chain(model)
        self.last_prompt = None
        self.last_response = None
        self.tts_lock = threading.Lock()

    def answer(self, prompt, image, stop_listening_callback):
        if not prompt:
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
        """Convert the response text to speech using pyttsx3 in a separate thread."""
        def speak():
            with self.tts_lock:
                # Initialize pyttsx3 engine every time
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)  # Set TTS speaking rate
                engine.setProperty('volume', 1.0)  # Set TTS volume
                
                engine.say(response)
                engine.runAndWait()  # Wait for TTS to finish speaking
                
                # Stop and reset engine after finishing
                engine.stop()

            # After speaking, resume listening
            stop_listening_callback()  # This will restart the microphone listener

        # Run TTS in a separate thread to avoid blocking the main thread
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


def audio_callback(recognizer, audio):
    """Process audio input and send it to the assistant."""
    try:
        prompt = recognizer.recognize_whisper(audio, model="base", language="english")
        assistant.answer(prompt, webcam_stream.read(), resume_listening)  # Process the audio input

    except UnknownValueError:
        print("There was an error processing the audio.")


def stop_listening():
    """Stop the microphone listener."""
    global stop_listening_callback
    if stop_listening_callback:
        stop_listening_callback(wait_for_stop=False)


def resume_listening():
    """Resume listening to the microphone after the assistant finishes responding."""
    global stop_listening_callback
    stop_listening_callback = recognizer.listen_in_background(microphone, audio_callback)


# Initialize recognizer and microphone
recognizer = Recognizer()
microphone = Microphone()

# Start listening to the microphone in a separate thread
with microphone as source:
    recognizer.adjust_for_ambient_noise(source)

stop_listening_callback = recognizer.listen_in_background(microphone, audio_callback)


# Initialize webcam stream and the model
webcam_stream = WebcamStream().start()
model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest")
assistant = Assistant(model)

# Streamlit UI
st.title("SAGE: A Video Assistant")
st.write("This application recognizes celebrities from your webcam feed and responds to your questions.")

# Create columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    st.write("### Webcam Feed")
    frame_placeholder = st.empty()

with col2:
    st.write("### Chat")
    prompt_placeholder = st.empty()
    response_placeholder = st.empty()

# Loop to update the video frame and display chat messages
while webcam_stream.running:
    frame = webcam_stream.read()
    frame_placeholder.image(frame, channels="BGR", caption="Webcam Feed")
    
    # Display the chat history
    if assistant.last_prompt and assistant.last_response:
        prompt_placeholder.markdown(f"*Prompt:* {assistant.last_prompt}")
        response_placeholder.markdown(f"*Response:* {assistant.last_response}")
    elif assistant.last_response:
        response_placeholder.markdown(f"*Response:* {assistant.last_response}")
    else:
        prompt_placeholder.markdown("*Prompt:* Waiting for input...")
        response_placeholder.markdown("*Response:* Waiting for response...")

    time.sleep(0.1)  # Adjust the sleep time as necessary

# Stop the webcam stream and microphone listener when the app ends
webcam_stream.stop()
stop_listening()
