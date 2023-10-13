# -*- coding: utf-8 -*-
import os
import time
from time import sleep
from threading import Thread

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import translation

# 설정 파라이터
video_id = "aSR-E4BmHcM"  # 스트리밍하는 동영상 ID로 수정
client_secrets_file_name = "youtube-api-credential.json"  # 유튜브 API 키 인증 정보를 담은 파일명으로 수정
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]  # 권한(수정할 필요 없음)
MAX_QUEUE_SIZE = 5  # 채팅 큐 사이즈

# 전역 변수
is_end = False
youtube = list()
live_chat_id = list()
chat_queue = list()
last_chat_check_time = time.time()-100
last_chat_index = -1
answer_queue = list()
voice_queue = list()

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

    polling_interval = 2

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
            eng_chat = translation.translate_text(raw_chat, "en")
            element = {
                'author': response['items'][i]['authorDetails']['displayName'],
                'raw_chat': raw_chat,
                'eng_chat': eng_chat
            }
            chat_queue.append(element)
        last_chat_index = len(response['items'])-1

def thread_answer():
    # chat_queue 큐에서 가져온 영어 질문에 대한 대답을 영어로 생성하고 텍스트를 전처리하고 나서 일본어로 변환한 후 큐에 넣음
    global is_end
    global youtube
    global live_chat_id
    global MAX_QUEUE_SIZE
    global chat_queue
    global last_chat_check_time
    global last_chat_index
    global answer_queue

    while True:
        if is_end and len(chat_queue) == 0:
            break
        if len(chat_queue) == 0:
            sleep(1)
            continue
        if len(answer_queue) > MAX_QUEUE_SIZE:
            sleep(3)
            continue
        print('Debug: generating answer')
        element = chat_queue.pop(0)
        print(element)




def thread_tts():
    # answer_queue 큐에서 영어를 가져와서 일본어로 변역하고 tts를 실행하고 큐에 넣음
    pass


def thread_send_chat():
    # voice_queue 큐에서 음성을 가져와서 출력하고 로그에 남김
    # 동시에 한글, 영어로 번역된 텍스트를 화면에 출력하고 로그에 남김
    pass


if __name__ == "__main__":
    init_youtube()
    request = youtube.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        id=video_id
    )
    response = request.execute()
    live_chat_id = response['items'][0]['snippet']['liveChatId']
    th_read_chat = Thread(target=thread_read_chat)
    th_answer = Thread(target=thread_answer)

    th_read_chat.start()
    th_answer.start()

    while True:
        input_str = input()
        if input_str == 'q':  # q를 입력하면 종료
            is_end = True
            break
    
    th_read_chat.join()
    th_answer.join()