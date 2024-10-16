from flask import Flask, Response, render_template
import cv2
import wave
import pyaudio

app = Flask(__name__)

# Function to generate video stream from webcam
def video_stream():
    video_capture = cv2.VideoCapture(0)  # Use 0 for the default camera

    while True:
        success, frame = video_capture.read()
        if not success:
            break
        
        # Encode frame as JPEG
        _, jpeg = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    video_capture.release()

# Function to generate audio stream
def audio_stream():
    chunk = 1024  # Sample size
    wf = wave.open('your_audio_file.wav', 'rb')
    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio_feed')
def audio_feed():
    return Response(audio_stream(), mimetype='audio/wav')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
