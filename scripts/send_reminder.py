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
from datetime import datetime    # 時刻取得用に追加
from zoneinfo import ZoneInfo    # タイムゾーン指定用に追加

DEFAULT_MESSAGE = "【リマインダー】予定の確認をお願いします。"

def build_args():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Do not send, only print the message")
    p.add_argument("--message", "-m", help="Message to send (overrides REMINDER_MESSAGE)")
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
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    
    if resp.status_code == 200:
        return True
    else:
        print(f"API Error: {resp.status_code} - {resp.text}")
        return False

def main():
    args = build_args()
    base_message = args.message or os.getenv("REMINDER_MESSAGE") or DEFAULT_MESSAGE
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    to = os.getenv("LINE_TO")

    # --- 変更点：日本時間で現在時刻を取得し、メッセージに結合する ---
    now_jst = datetime.now(ZoneInfo("Asia/Tokyo"))
    time_str = now_jst.strftime("%Y/%m/%d %H:%M") # 例: 2026/03/30 15:30
    
    # 元のメッセージの末尾に時刻を追加
    message = f"{base_message}\n\n(送信日時: {time_str})"
    # -----------------------------------------------------------

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