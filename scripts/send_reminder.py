#!/usr/bin/env python3
"""
Send a LINE Messaging API reminder.

Usage:
  python scripts/send_reminder.py [--dry-run] [--message "..."]

Environment:
  LINE_CHANNEL_ACCESS_TOKEN: required unless --dry-run
  LINE_TO: User ID, Group ID, or Room ID to send the message to (required unless --dry-run)
  REMINDER_MESSAGE: optional default message override
"""
import os
import sys
import time
import argparse

DEFAULT_MESSAGE = "【リマインダー】予定の確認をお願いします。"

def build_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Do not send, only print the message")
    p.add_argument("--message", "-m", help="Message to send (overrides REMINDER_MESSAGE)")
    p.add_argument("--retries", type=int, default=3, help="Number of retries on failure")
    return p.parse_args()

def send_message(token: str, to: str, message: str) -> bool:
    import requests

    # Messaging APIのPush Messageエンドポイント
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    # 送信先IDとメッセージ内容をJSON形式で構築
    data = {
        "to": to,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    # dataではなくjson引数を使用します
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    
    # デバッグ用にエラーメッセージを出力するよう改善
    if resp.status_code == 200:
        return True
    else:
        print(f"API Error: {resp.status_code} - {resp.text}")
        return False

def main():
    args = build_args()
    message = args.message or os.getenv("REMINDER_MESSAGE") or DEFAULT_MESSAGE
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to = os.getenv("LINE_TO") # 送信先IDの環境変数を追加

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