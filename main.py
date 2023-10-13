# -*- coding: utf-8 -*-


import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

from threading import Thread

# 설정 파라이터
video_id = "aSR-E4BmHcM"  # 스트리밍하는 동영상 ID로 수정
client_secrets_file_name = "youtube-api-credential.json"  # 유튜브 API 키 인증 정보를 담은 파일명으로 수정
scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]  # 권한(수정할 필요 없음)

# 전역 변수
youtube = None
live_chat_id = None
chat_queue = None
test_queue = None
voice_queue = None

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

    

if __name__ == "__main__":
    init_youtube()
    request = youtube.liveBroadcasts().list(
        part="snippet,contentDetails,status",
        id=video_id
    )
    response = request.execute()
    live_chat_id = response['items'][0]['snippet']['liveChatId']