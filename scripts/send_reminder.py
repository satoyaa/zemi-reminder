#!/usr/bin/env python3
import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
import urllib3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# SSL警告を非表示にする
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === 設定部分 ===
LOGIN_URL = os.getenv("LOGIN_URL")
SCHEDULE_URL = os.getenv("SCHEDULE_URL")

ID_KEY = "wpName"
PASS_KEY = "wpPassword"
# =========================================================

def get_upcoming_events():
    """スクレイピングを行って、24時間以内の予定リストを返す"""
    # 秘匿情報は環境変数（GitHub Secrets）から取得
    service_id = os.getenv("SERVICE_LOGIN_ID")
    service_pass = os.getenv("SERVICE_PASSWORD")
    
    if not service_id or not service_pass:
        print("エラー: SERVICE_LOGIN_ID または SERVICE_PASSWORD が設定されていません。")
        sys.exit(1)

    session = requests.Session()
    session.verify = False # SSL検証スキップ

    # 1. トークンの取得
    pre_login_res = session.get(LOGIN_URL)
    pre_login_soup = BeautifulSoup(pre_login_res.text, "html.parser")
    token_input = pre_login_soup.find("input", {"name": "wpLoginToken"})
    token_value = token_input.get("value") if token_input else ""

    # 2. ログイン実行
    login_payload = {
        "title": "特別:ログイン",
        ID_KEY: service_id,
        PASS_KEY: service_pass,
        "wpLoginAttempt": "ログイン",  
        "wpEditToken": "+\\",  
        "authAction": "login",  
        "force": "",  
        "wpLoginToken": token_value,
    }
    session.post(LOGIN_URL, data=login_payload)

    # 3. スケジュールページの取得と解析
    schedule_res = session.get(SCHEDULE_URL)
    soup = BeautifulSoup(schedule_res.text, "html.parser")
    content = soup.find("div", class_="mw-parser-output")
    
    if not content:
        print("スケジュールのdivが見つかりませんでした。")
        return []

    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
    # 現在時刻（20:00）から24時間後（翌日の20:00）を期限とする
    deadline_jst = now_jst + timedelta(days=1)
    
    upcoming_events = []
    
    uls = content.find_all("ul")
    for ul in uls:
        lis = ul.find_all("li")
        for li in lis:
            text = li.text.strip()
            # 「/」と「:」が含まれていればスケジュールとみなす
            if "/" in text and ":" in text and "M・B4ゼミナール" in text:
                # 正規表現で「月, 日, 時, 分」の数字を抽出する
                match = re.search(r"(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{1,2})", text)
                if match:
                    month, day, hour, minute = map(int, match.groups())
                    year = now_jst.year
                    
                    # 年末対策（現在12月で、予定が1月なら来年とみなす）
                    if now_jst.month == 12 and month == 1:
                        year += 1
                        
                    try:
                        # 予定の日時データを作成
                        event_time = datetime(year, month, day, hour, minute, tzinfo=ZoneInfo("Asia/Tokyo"))
                        
                        # 「現在時刻」〜「明日の同じ時刻」の間にあるか判定
                        if now_jst <= event_time <= deadline_jst:
                            upcoming_events.append(text)
                    except ValueError:
                        pass # 日付として不正な文字列（2/30など）は無視
                        
    return upcoming_events

def send_message(token: str, to: str, message: str) -> bool:
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "to": to,
        "messages": [{"type": "text", "text": message}]
    }
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    return resp.status_code == 200

def main():
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to = os.getenv("LINE_TO")

    if not token or not to:
        print("エラー: LINEの環境変数が設定されていません")
        sys.exit(1)

    # 予定を取得
    print("スケジュールの取得を開始します...")
    events = get_upcoming_events()

    if not events:
        print("24時間以内の予定はありませんでした。終了します。")
        sys.exit(0) # 正常終了（LINEは送らない）

    # 送信するメッセージを作成
    message_lines = ["【明日の予定リマインド】", "以下の予定があります．\n"]
    for event in events:
        message_lines.append(f"・{event}")
    message_lines.append("\nお忘れないようによろしくお願いいたします．")
    final_message = "\n".join(message_lines)
    
    print("以下のメッセージを送信します:\n", final_message)

    # LINE送信（リトライ処理付き）
    retries = 3
    backoff = 1
    for attempt in range(1, retries + 1):
        try:
            if send_message(token, to, final_message):
                print("送信完了")
                return 0
        except Exception as e:
            print(f"エラー: {e}")
            
        time.sleep(backoff)
        backoff *= 2

    return 1

if __name__ == '__main__':
    sys.exit(main())