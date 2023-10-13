import requests
from requests import get  # to make GET request
import os
import json
from dotenv import load_dotenv
import time

load_dotenv()
ENDPOINT = os.environ.get('TTS_ENDPOINT')
index = 1

start_time = round(time.time())
if not os.path.exists("tts_output"):
  os.mkdir("tts_output")
os.mkdir(f"tts_output/wav_{start_time}")

def download(url, file_name):
    with open(file_name, "wb") as file:   # open in binary mode
        response = get(url)               # get request
        file.write(response.content)      # write to file

def tts(text): # returns local file path
  try:
    global index
    response = requests.post(ENDPOINT+"/run/tts", json={
        "data": [
          text,
          "ブルアカ TTS",
          0.9,
          False,
      ]}).json()

    data = response["data"]
    file_url = ENDPOINT+"/file="+data[1]["name"]
    download(file_url,f"tts_output/wav_{start_time}/{index}.wav")
    index += 1
    # print(file_url)
    return f"tts_output/wav_{start_time}/{index-1}.wav"
  except:
    return "yuuka_error.wav"
    
if __name__ == "__main__":
  tts("こんにちは")
  tts("おはようございます")
  tts("こんばんは")
  tts("おやすみなさい")