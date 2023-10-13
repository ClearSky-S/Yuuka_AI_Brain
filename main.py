# -*- coding: utf-8 -*-
import os
import time
from time import sleep
from threading import Thread  # 비싼 연산은 모두 클라우드 컴퓨팅으로 진행되기 때문에 멀티프로세싱으로 구현할 필요 없음
from dotenv import load_dotenv
load_dotenv()

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import deepl

# import translation
import conversation
import tts




# 설정 파라이터
is_debug = True  # 디버그 모드 여부
video_id = "Iq9xLMdqFsc"  # 스트리밍하는 동영상 ID로 수정
client_secrets_file_name = "youtube-api-credential.json"  # 유튜브 API 키 인증 정보를 담은 파일명으로 수정
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]  # 권한(수정할 필요 없음)
MAX_QUEUE_SIZE = 3  # 채팅 큐 사이즈


# 전역 변수
is_end = False
youtube = list()
live_chat_id = list()
chat_queue = list()
last_chat_check_time = time.time()-100
last_chat_index = -1
answer_queue = list()
voice_queue = list()
translator = deepl.Translator(os.environ.get('deepl_auth_key'))


def init_youtube():
    # Made based on sample Python code for youtube.liveBroadcasts.list
    # See instructions for running these code samples locally:
    # https://developers.google.com/explorer-help/code-samples#python

    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = client_secrets_file_name

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    global youtube
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

def thread_read_chat():
    # 유튜브에서 챗을 읽어 오고 영어로 변환해서 큐에 넣음
    global is_end
    global youtube
    global live_chat_id
    global MAX_QUEUE_SIZE
    global chat_queue
    global last_chat_check_time
    global last_chat_index
    global translator

    polling_interval = 2

    # 시작 전에 친 채팅은 무시
    request = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails"
        )
    response = request.execute()
    last_chat_index = len(response['items'])-1 

    while True:
        if is_end:
            break
        if len(chat_queue) > MAX_QUEUE_SIZE:
            sleep(3)
            continue
        if last_chat_check_time + polling_interval > time.time():
            sleep(1)
            continue

        last_chat_check_time = time.time()
        request = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails"
        )
        if is_debug:
            print('Debug: calling youtube chat list api')
        response = request.execute()
        start_index = max( len(response['items'])-MAX_QUEUE_SIZE, last_chat_index+1)
        # 새로운 채팅이 없으면 채팅 polling 간격을 증가시킴
        if start_index >= len(response['items']):
            if polling_interval < 8:
                polling_interval += 2
            sleep(1)
            continue
        polling_interval = 2
        for i in range(start_index , len(response['items'])):
            # TODO: 영어로 변환해서 큐에 넣기
            raw_chat = response['items'][i]['snippet']['displayMessage']
            # en_chat = translation.translate_text(raw_chat, "en")
            en_chat = translator.translate_text(raw_chat, target_lang="EN-US").text
            element = {
                'author': response['items'][i]['authorDetails']['displayName'],
                'author_id': response['items'][i]['authorDetails']['channelId'],
                'raw_chat': raw_chat,
                'en_chat': en_chat
            }
            chat_queue.append(element)
        last_chat_index = len(response['items'])-1

def thread_answer():
    # chat_queue 큐에서 가져온 영어 질문에 대한 대답을 영어로 생성하고 다국어로 변환한 후 큐에 넣음
    global is_end
    global youtube
    global live_chat_id
    global MAX_QUEUE_SIZE
    global chat_queue
    global last_chat_check_time
    global last_chat_index
    global answer_queue
    global translator


    while True:
        if is_end and len(chat_queue) == 0:
            break
        if len(chat_queue) == 0:
            sleep(1)
            continue
        if len(answer_queue) > MAX_QUEUE_SIZE:
            sleep(3)
            continue
        if is_debug:
            print('Debug: generating answer')
        element = chat_queue.pop(0)
        answer = conversation.conversation(element['en_chat'], element['author'], element['author_id'])
        element['answer_en'] = answer
        # element['answer_ja'] = translation.translate_text(answer, "ja")
        # element['answer_ko'] = translation.translate_text(answer, "ko")
        element['answer_ja'] = translator.translate_text(answer, target_lang="JA").text
        element['answer_ko'] = translator.translate_text(answer, target_lang="KO").text
        answer_queue.append(element)

        
def thread_tts():
    # answer_queue 큐에서 일본어를 가져와서 tts를 실행하고 큐에 넣음
    global is_end
    global answer_queue
    global voice_queue
    global translator


    while True:
        if is_end and len(answer_queue) == 0:
            break
        if len(answer_queue) == 0:
            sleep(1)
            continue
        if len(voice_queue) > MAX_QUEUE_SIZE:
            sleep(3)
            continue
        if is_debug:
            print('Debug: generating voice')
        element = answer_queue.pop(0)
        start = time.time()
        voice = tts.tts(element['answer_ja'])
        if is_debug:
            print(f'Debug: voice generation time: {time.time()-start}')
        element['voice'] = voice
        voice_queue.append(element)
        print(element)



def thread_send_chat():
    # voice_queue 큐에서 음성을 가져와서 출력하고 로그에 남김
    # 동시에 한글, 영어로 번역된 텍스트를 화면에 출력하고 로그에 남김
    from flask import Flask
    app = Flask(__name__)
    def shutdown_server():
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
    
    @app.route('/get-data')
    def get_data():
        if is_end and len(voice_queue) == 0:
            return ''
        
        if len(voice_queue) == 0:
            return ''
        element = voice_queue.pop(0)
        # tts_output/wav_1697215286/3.wav
        # change to absolute path
        element['voice'] = os.path.abspath('.').replace('\\','/') +'/' + element['voice']
        print(element['voice'])
        return element

    app.run()

if __name__ == "__main__":
    init_youtube()
    request = youtube.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        id=video_id
    )
    response = request.execute()
    live_chat_id = response['items'][0]['snippet']['liveChatId']
    print('liveChatId: ' + live_chat_id)
    th_read_chat = Thread(target=thread_read_chat)
    th_answer = Thread(target=thread_answer)
    th_tts = Thread(target=thread_tts)
    # th_tts2 = Thread(target=thread_tts)

    th_send_chat = Thread(target=thread_send_chat)

    th_read_chat.start()
    th_answer.start()
    th_tts.start()
    # th_tts2.start()
    th_send_chat.start()

    while True:
        input_str = input()
        if input_str == 'q':  # q를 입력하면 종료
            print('end process triggered')
            is_end = True
            ending_voice = {
  "answer_en": "I'll end the broadcast. Thank you for watching the show!!",
  "answer_ja": "時間が遅くなりましたので、そろそろ放送を終了したいと思います。 放送を視聴してくださってありがとうございます!!",
  "answer_ko": "시간이 늦었으니 슬슬 방종하도록 하겠습니다. 방송 시청해주셔서 감사합니다!!",
  "author": "Admin",
  "author_id": "Admin",
  "en_chat": "end",
  "raw_chat": "end",
  "voice": "F:/python/bluearchive-ai/Yuuka_AI_Brain/ending_voice.wav"
}
            voice_queue.append({'voice': 'end'})

            while len(chat_queue) > 0:
                sleep(1)
            break
    
    th_read_chat.join()
    th_answer.join()
    th_tts.join()
    # th_tts2.join()
