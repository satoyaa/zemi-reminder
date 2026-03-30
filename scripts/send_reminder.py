#!/usr/bin/env python3
"""
Send a LINE Notify reminder.

Usage:
  python scripts/send_reminder.py [--dry-run] [--message "..."]

Environment:
  LINE_NOTIFY_TOKEN: required unless --dry-run
  REMINDER_MESSAGE: optional default message override

The script avoids importing `requests` when running in dry-run mode so local tests
without installing dependencies are convenient.
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


def send_message(token: str, message: str) -> bool:
    # import here to allow dry-run without installing requests
    import requests

    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    resp = requests.post(url, headers=headers, data=data, timeout=10)
    return resp.status_code == 200


def main():
    args = build_args()
    message = args.message or os.getenv("REMINDER_MESSAGE") or DEFAULT_MESSAGE
    token = os.getenv("LINE_NOTIFY_TOKEN")

    if args.dry_run:
        print("[dry-run] message to send:\n", message)
        return 0

    if not token:
        print("ERROR: environment variable LINE_NOTIFY_TOKEN is required (or run with --dry-run)")
        return 2

    retries = max(0, args.retries)
    backoff = 1
    for attempt in range(1, retries + 1):
        try:
            ok = send_message(token, message)
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
