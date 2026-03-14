from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer
from datetime import datetime
import wave
import json
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Load Vosk model
model = Model("model/vosk-model-small-en-us-0.15")

# n8n webhook URL
N8N_WEBHOOK = "http://localhost:5678/webhook/doctor-text"


def recognize_audio(file_path):
    wf = wave.open(file_path, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    text = ""

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break

        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += res.get("text", "") + " "

    final = json.loads(rec.FinalResult())
    text += final.get("text", "")

    return text.strip()


def send_to_n8n(text):
    try:
        response = requests.post(
            N8N_WEBHOOK,
            json={"transcript": text}
        )
        print("Sent to n8n:", response.status_code)
    except Exception as e:
        print("Error sending to n8n:", e)


# API for uploaded audio files (frontend)
@app.route('/speech', methods=['POST'])
def speech():

    if 'audio' not in request.files:
        return jsonify({"error": "No audio file"}), 400

    file = request.files['audio']

    file_path = f"audio/recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"    
    file.save(file_path)
    
    text = recognize_audio(file_path)
    print("Transcribed:", text)
    
    # Send transcript to n8n
    requests.post(
        "http://localhost:5678/webhook/doctor-text",
        json={"transcript": text}
    )

    #os.remove(file_path)

    return jsonify({
        "status": "success",
        "text": text
    })


# API for testing local audio files
@app.route('/local-speech', methods=['GET'])
def local_speech():

    file_name = request.args.get("file")

    if not file_name:
        return jsonify({"error": "No file provided"}), 400

    if not os.path.exists(file_name):
        return jsonify({"error": "File not found"}), 404

    text = recognize_audio(file_name)
    print("Transcribed:", text)

    # Send transcript to n8n
    requests.post(
        "http://localhost:5678/webhook/doctor-text",
        json={"transcript": text}
    )

    return jsonify({
        "status": "success",
        "text": text
    })


@app.route("/")
def home():
    return jsonify({
        "message": "Vosk Speech Server Running"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)