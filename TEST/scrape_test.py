import requests
from bs4 import BeautifulSoup
import re
import urllib3

# === 設定部分 ===
LOGIN_URL = "https://www.sos.info.hiroshima-cu.ac.jp/wiki/index.php?title=%E7%89%B9%E5%88%A5:%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3&returnto=%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8"
SCHEDULE_URL = "https://www.sos.info.hiroshima-cu.ac.jp/wiki/index.php/%E3%83%86%E3%83%B3%E3%83%97%E3%83%AC%E3%83%BC%E3%83%88:%E5%B9%B4%E9%96%93%E3%82%B9%E3%82%B1%E3%82%B8%E3%83%A5%E3%83%BC%E3%83%AB"

# 実際のIDとパスワード（テスト用なので直接書いてOKです）
USER_ID = "Iwamuro25"
PASSWORD = "wiki-Iwamuro25"

# POSTするデータ（Payloadのキー名に合わせてください）

# ==============


def test_scrape():
    session = requests.Session()
    session.verify = False

    # 🌟 ステップ1: ログイン画面をGETして「隠しトークン」を取得する
    print("ログイン画面を開いてトークンを探します...")
    pre_login_res = session.get(LOGIN_URL)
    pre_login_soup = BeautifulSoup(pre_login_res.text, "html.parser")

    # inputタグの中から、nameが "wpLoginToken" のものを探す
    # （※もしNetworkタブのPayloadで違う名前のトークンが送られていたら、ここを書き換えてください）
    token_input = pre_login_soup.find("input", {"name": "wpLoginToken"})
    
    if not token_input:
        print("❌ トークンが見つかりませんでした。HTMLの構造が違うかもしれません。")
        return # 中断
    
    token_value = token_input.get("value")
    print(f"✅ トークンを取得しました: {token_value[:10]}...")

    # 🌟 ステップ2: 取得したトークンをPayloadに混ぜてPOSTする
    login_payload = {
        "title": "特別:ログイン",
        "wpName": USER_ID,
        "wpPassword": PASSWORD,
        "wpLoginAttempt": "ログイン",  # ログインボタンの名前（value）に合わせてください
        "wpEditToken": "+\\",  # MediaWikiのCSRFトークン（必要な場合は取得してここに入れます）
        "authAction": "login",  # MediaWikiの場合、ログインアクションを指定することがあります（必要に応じて）
        "force": "",  # これもMediaWikiでログインを強制するためのパラメータ（必要に応じて）
        "wpLoginToken": token_value,
        # MediaWikiの場合、tokenなどが必要な場合があります。
        # ログイン時のPayloadに他にも必須項目があればここに追加します。
    }

    print("ログインを試行します...")
    login_response = session.post(LOGIN_URL, data=login_payload)
    login_response.raise_for_status()

    # 3. スケジュールページの取得
    print("スケジュールページを取得します...")
    schedule_response = session.get(SCHEDULE_URL)
    schedule_response.raise_for_status()
    
    soup = BeautifulSoup(schedule_response.text, "html.parser")
    #print(f"ページの中身: {soup.find_all("li")}")
    # mw-parser-output の div を取得
    content = soup.find("div", class_="mw-parser-output")

    # その中の ul を取得
    uls = content.find_all("ul")

    uls = content.find_all("ul")

    for ul in uls:
        lis = ul.find_all("li")
        
        for li in lis:
            text = li.text.strip()
            
            # スケジュールっぽいものだけ抽出
            if "/" in text and ":" in text:
                print(text)

if __name__ == "__main__":
    test_scrape()