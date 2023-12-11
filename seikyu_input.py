import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from time import sleep
import os
import datetime
import time
from slack_sdk import WebClient
import requests
import certifi
import ssl
import logging
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# 設定を読み込むためのconfigparserオブジェクトを作成
config = configparser.ConfigParser()

# Docker環境内で実行されているかどうかを判定する関数
def is_running_in_docker():
    return os.path.exists('/.dockerenv')

# ローカル環境での設定ファイルのパスを動的に取得する関数
def get_local_config_path():
    current_script_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_script_path)
    return os.path.join(current_directory, 'settings.ini')

# Docker環境内での実行を確認
if is_running_in_docker():
    print("このプログラムはDockerコンテナ内で実行されています。")
    path = 'settings.ini'
else:
    print("このプログラムはローカル環境で実行されています。")
    path = get_local_config_path()

# 設定ファイルを読み込む
config.read(path, encoding='utf-8')

# 設定ファイルから各種設定を取得
site_url = config.get('site', 'url')
basic_id = config.get('basic_auth', 'id')
basic_pw = config.get('basic_auth', 'password')
admin_id = config.get('auth', 'id')
admin_pw = config.get('auth', 'password')

# WebDriverのインスタンスを作成
if is_running_in_docker():
    # Docker環境でのFirefox WebDriverの設定
    firefox_options = FirefoxOptions()
    cloud_options = {'build': 'build_1', 'name': 'test_abc'}
    firefox_options.set_capability('cloud:options', cloud_options)
    
    # 環境変数"SELENIUM_URL"が設定されている場合は、Remote WebDriverを使用
    if "SELENIUM_URL" in os.environ:
        driver = webdriver.Remote(
            command_executor=os.environ["SELENIUM_URL"],
            options=firefox_options
        )
    else:
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)
else:
    # ローカル環境でのChrome WebDriverの設定
    chrome_options = ChromeOptions()
    chrome_options.set_capability('pageLoadStrategy', 'eager')
    chrome_options.set_capability('acceptInsecureCerts', True)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    
# Basic認証用のURLを生成
basic_auth_url = f"https://{basic_id}:{basic_pw}@{site_url.replace('https://', '')}"   

# # 環境を判断し、対応するパスで設定ファイルを読み込む
# if os.path.exists(docker_path):
#     config.read(docker_path, encoding='utf-8')
# elif os.path.exists(local_path):
#     config.read(local_path, encoding='utf-8')
# else:
#     raise FileNotFoundError("設定ファイルが見つかりません。")

"""
# WebDriverの設定（ここではChromeを使用）
#driver = webdriver.Chrome()
options = webdriver.ChromeOptions()
options.set_capability('pageLoadStrategy', 'eager')
options.set_capability('acceptInsecureCerts', True)
#driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
from selenium.webdriver.firefox.options import Options as FirefoxOptions
options = FirefoxOptions()
cloud_options = {}
cloud_options['build'] = "build_1"
cloud_options['name'] = "test_abc"
options.set_capability('cloud:options', cloud_options)

driver = webdriver.Remote(
    command_executor=os.environ["SELENIUM_URL"],
    options=options
)
driver.implicitly_wait(5)
"""

# WebDriverの設定
try:
    # ローカル環境でのChrome WebDriverの設定
    chrome_options = ChromeOptions()
    chrome_options.set_capability('pageLoadStrategy', 'eager')
    chrome_options.set_capability('acceptInsecureCerts', True)
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
except Exception as e:
    # Docker環境でのFirefox WebDriverの設定
    firefox_options = FirefoxOptions()
    cloud_options = {'build': 'build_1', 'name': 'test_abc'}
    firefox_options.set_capability('cloud:options', cloud_options)

    # 環境変数"SELENIUM_URL"が設定されている場合は、Remote WebDriverを使用
    if "SELENIUM_URL" in os.environ:
        driver = webdriver.Remote(
            command_executor=os.environ["SELENIUM_URL"],
            options=firefox_options
        )
    else:
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=firefox_options)

driver.implicitly_wait(5)

# Basic認証ページにアクセス
driver.get(basic_auth_url)

# Pythonのloggingを設定
#logging.basicConfig(level=logging.DEBUG)
# SSLContextオブジェクトを作成
context = ssl.create_default_context()
print(type(context))
# コンテキストが証明書を検証するかどうかを確認
will_verify = context.verify_mode != ssl.CERT_NONE
print(context)
print(will_verify)

# Slack APIトークンを取得（環境変数から取得する例）
slack_token = "xoxb-246742194723-5374572540225-pKfdHzQwc5bAP5k9tMhVXZO8"  # Don't actually do this

# この部分はスキップ；SSLContextを使用している場合、証明書のパスを指定する必要はありません
ssl_cert_path = certifi.where()
print(certifi.where())
# WebClient設定のカスタマイズ（必要な場合）
from slack_sdk.http_retry import RateLimitErrorRetryHandler
# SSLContextオブジェクトを使ってWebClientを初期化
client = WebClient(
    token=slack_token,
    ssl=context  # SSLContextオブジェクトを渡す
)

# 管理画面ログイン
try:
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input#login'))
    )
    element.send_keys(admin_id)
    element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input#password'))
    )
    element.send_keys(admin_pw)
    submit_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#login > form > p:nth-child(5) > input[type=submit]"))
    )
    submit_button.click()
    # ログイン後にクリックするリンクのCSSセレクタ
    click_after_login_css_selector = "#sub > div > ul:nth-child(10) > li:nth-child(4) > a"
    # クリックする要素が出現するまで待つ
    element_to_click = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, click_after_login_css_selector))
    )
    # 要素をクリック
    element_to_click.click()
    # 請求数合計を取得
    target_element_css = "#main > table > tbody > tr:nth-child(2) > td:nth-child(4)"
    # target_element_xpath = "/html/body/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[2]"
    target_element_all = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, target_element_css))
    )
    
    time.sleep(1)
    
    # 要素のテキストを取得して表示
    all_text = target_element_all.text
    print("請求数合計:", all_text)
    
    # 1. "塾講師ステーション"を選択
    element = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'select#c_divide_grade'))
    )
    select_object = Select(element)
    
    time.sleep(10)
    
    # ドロップダウンから"塾講師ステーション"を選択
    select_object.select_by_visible_text("塾講師ステーション")
    
    time.sleep(1)
    
    # 2. 指定したsubmitボタンをクリック
    submit_button_css = "#main > form:nth-child(3) > div > input[type=submit]:nth-child(1)"
    # submit_button_xpath = "/html/body/div[1]/div[2]/div[1]/form[1]/div/input[1]"
    submit_button = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, submit_button_css))
    )
    submit_button.click()  # クリック
    
    time.sleep(25)
        
    # 3. 指定した要素のテキストを取得して表示
    target_element_css = "#main > table > tbody > tr:nth-child(2) > td:nth-child(4)"
    # target_element_xpath = "/html/body/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[2]"
    target_element_st = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, target_element_css))
    )
    
    # 要素のテキストを取得して表示
    st_text = target_element_st.text
    print("ステーション:", st_text)
    
    time.sleep(1)
    
    # 1. "塾講師ステーション【キャリア版】"を選択
    element = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'select#c_divide_grade'))
    )
    # <select>要素の操作を容易にするためにSelectオブジェクトを生成
    select_object = Select(element)
    # ドロップダウンから"塾講師ステーション【キャリア版】"を選択
    select_object.select_by_visible_text("塾講師ステーション【キャリア版】")
    
    time.sleep(1)
    
    # 2. 指定したsubmitボタンをクリック
    submit_button_css = "#main > form:nth-child(3) > div > input[type=submit]:nth-child(1)"
    # submit_button_xpath = "/html/body/div[1]/div[2]/div[1]/form[1]/div/input[1]"
    submit_button = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, submit_button_css))
    )
    submit_button.click() # クリック
    
    time.sleep(25)
    
    # 3. 指定した要素のテキストを取得して表示
    target_element_css = "#main > table > tbody > tr:nth-child(2) > td:nth-child(4)"
    # target_element_xpath = "/html/body/div[1]/div[2]/div[1]/table/tbody/tr[2]/td[2]"
    target_element_ca = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, target_element_css))
    )
    
    # 要素のテキストを取得して表示
    ca_text = target_element_ca.text
    print("キャリア:", target_element_ca.text)
    # driver.quit()

    # 通知する内容を指定
    current_date_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
    message = f"▼取得時刻（{current_date_time}）\n▶ 請求数合計: {all_text} 件\n┣ ステーション: {st_text} 件\n┗ キャリア: {ca_text} 件"
    # Slackにメッセージを送信
    response = client.chat_postMessage(
        channel="C015RKAL49K",  # メッセージを送信するチャンネルを指定
        text=message,
        username="当月の請求確定Bot（現在は手動送信中）",  # 送信元の名前を指定
        icon_emoji=":moneybag:"  # 送信元のアイコンを絵文字で指定
    )
    
finally:
    # レスポンスを表示
    print("Message sent")