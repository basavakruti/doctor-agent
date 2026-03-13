import requests

url = "http://localhost:5000/speech"

files = {"audio": open("audio.wav", "rb")}

response = requests.post(url, files=files)

print(response.text)
