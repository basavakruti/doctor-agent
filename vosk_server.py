from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer
import wave
import json
import os

app = Flask(__name__)

model = Model("model/vosk-model-small-en-us-0.15")

def recognize_audio(file_path):

    wf = wave.open(file_path, "rb")

    rec = KaldiRecognizer(model, wf.getframerate())

    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break

        rec.AcceptWaveform(data)

    result = json.loads(rec.FinalResult())
    return result


# API for uploaded files
@app.route('/speech', methods=['POST'])
def speech():

    file = request.files['audio']
    file_path = "temp_audio.wav"
    file.save(file_path)

    result = recognize_audio(file_path)

    os.remove(file_path)

    return jsonify(result)


# API for local files
@app.route('/local-speech', methods=['GET'])
def local_speech():

    file_name = request.args.get("file")

    if not file_name:
        return jsonify({"error": "No file provided"}), 400

    if not os.path.exists(file_name):
        return jsonify({"error": "File not found"}), 404

    result = recognize_audio(file_name)

    return jsonify(result)


if __name__ == "__main__":
    app.run(port=5000)
