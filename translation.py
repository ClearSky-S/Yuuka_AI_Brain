# 네이버 Papago 언어감지 API
# 그런데 파파고는 기본 제공량이 적어 사용하지 않기로 함.
import json
import os
import sys
import urllib.request
from dotenv import load_dotenv
load_dotenv()

client_id = os.environ.get('client_id') # 개발자센터에서 발급받은 Client ID 값
client_secret = os.environ.get('client_secret') # 개발자센터에서 발급받은 Client Secret 값


def translate_text(text, target_lang="en"):
    try:
    # ko, en, ja
    # 텍스트의 언어를 인식하는 API 호출하고 그 결과를 바탕으로 다시 번역하는 API 호출
        global client_id
        global client_secret
        
        encQuery = urllib.parse.quote(text)
        data = "query=" + encQuery
        url = "https://openapi.naver.com/v1/papago/detectLangs"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        source_lang = ""
        if(rescode==200):
            response_body = response.read()
            # print(response_body.decode('utf-8'))
            response_body = json.loads(response_body.decode('utf-8'))
            source_lang = response_body['langCode']
        else:
            return "Error Code:" + rescode
        # print(source_lang)
        if source_lang == target_lang:
            return text
        
        data = f"source={source_lang}&target={target_lang}&text=" + encQuery
        url = "https://openapi.naver.com/v1/papago/n2mt"
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id",client_id)
        request.add_header("X-Naver-Client-Secret",client_secret)
        response = urllib.request.urlopen(request, data=data.encode("utf-8"))
        rescode = response.getcode()
        if(rescode==200):
            response_body = response.read()
            # print(response_body.decode('utf-8'))
            response_body = json.loads(response_body.decode('utf-8'))
            return response_body['message']['result']['translatedText']
        else:
            return "Error Code:" + rescode
    except:
        return "Translation Error"

if __name__ == "__main__":
    print(translate_text("할룽~=~", "ja"))