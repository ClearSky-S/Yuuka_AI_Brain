import json
import requests
import os
from dotenv import load_dotenv
load_dotenv()

CHARACTER_NAME = os.environ.get('Inworld_CHARACTER_NAME')
WORKSPACE_ID = os.environ.get('Inworld_WORKSPACE_ID')
KEY = os.environ.get('Inworld_KEY')

is_first = True
url = f'https://studio.inworld.ai/v1/workspaces/{WORKSPACE_ID}/characters/{CHARACTER_NAME}:simpleSendText'
headers = {"Content-Type": "application/json", "authorization": f"Basic {KEY}"}

# x = requests.post(url, json = myobj, headers=headers)
# j = json.loads(x.text)
# print(''.join(j['textList']))


def conversation(chat, username, uid):
    global headers
    global is_first
    myobj = {"character":f"workspaces/{WORKSPACE_ID}/characters/{CHARACTER_NAME}", "text":chat, "endUserFullname":username, "endUserId":uid}
    x = requests.post(url, json = myobj, headers=headers)
    j = json.loads(x.text)
    if is_first:
        is_first = False
        headers = {"Content-Type": "application/json", "authorization": f"Basic {KEY}", "sessionId": j['sessionId']}
    # print(''.join(j['textList']))
    # print('')
    return ''.join(j['textList'])

if __name__ == "__main__":
    conversation("hello", "Teacher", "1234")
    conversation("good", "Teacher", "1234")
