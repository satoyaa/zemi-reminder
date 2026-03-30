#!/usr/bin/env python3
"""
Send a LINE Messaging API reminder.
"""
import os
import sys
import time
import argparse
from datetime import datetime, timedelta  # timedeltaを追加
from zoneinfo import ZoneInfo

# DEFAULT_MESSAGEは今回はコード内で直接作るので削除しても構いません

def build_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Do not send, only print the message")
    p.add_argument("--retries", type=int, default=3, help="Number of retries on failure")
    return p.parse_args()

def send_message(token: str, to: str, message: str) -> bool:
    import requests
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
    if resp.status_code == 200:
        return True
    else:
        print(f"API Error: {resp.status_code} - {resp.text}")
        return False

def main():
    args = build_args()
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to = os.getenv("LINE_TO")

    # --- 変更点：日付の自動計算 ---
    # 日本時間で現在時刻（実行時の日曜日）を取得
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
    
    # 来週の予定日を計算（例：日曜日実行なら、+1日して月曜日の日付にする）
    # ※もし予定が「来週の水曜日」なら days=3 に変更してください
    target_date = now_jst + timedelta(days=1)
    
    # 日付を文字列にする（Linux環境のGitHub Actionsでは %-m で「04月」ではなく「4月」になります）
    date_str = target_date.strftime("%-m月%-d日")
    
    # ご要望のメッセージを作成
    message = f"明日{date_str},4限にゼミがあります．\n忘れないようにしてください．"
    # -----------------------------------

    if args.dry_run:
        print("[dry-run] message to send:\n", message)
        return 0

    if not token or not to:
        print("ERROR: environment variables LINE_CHANNEL_ACCESS_TOKEN and LINE_TO are required")
        return 2

    retries = max(0, args.retries)
    backoff = 1
    for attempt in range(1, retries + 1):
        try:
            ok = send_message(token, to, message)
            if ok:
                print(f"Sent reminder (attempt {attempt})")
                return 0
            else:
                print(f"Attempt {attempt} failed: non-200 response")
        except Exception as e:
            print(f"Attempt {attempt} exception: {e}")

        if attempt < retries:
            time.sleep(backoff)
            backoff *= 2

    print("Failed to send reminder after retries")
    return 1

if __name__ == '__main__':
    sys.exit(main())