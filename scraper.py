import random
import requests
import time
import re
import urllib.parse
import speech_recognition as sr
import pydub
from fake_useragent import UserAgent
import os
from pydub.playback import play
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from config import Config
from playwright_auth import PlaywrightAuthenticator

from bs4 import BeautifulSoup
# from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError

# Get the directory where ffmpeg.exe and ffprobe.exe are located
framework_dir = os.getcwd()  # Assuming ffmpeg.exe and ffprobe.exe are in the current working directory

ffmpeg_path = os.path.join(framework_dir, 'ffmpeg.exe')
ffprobe_path = os.path.join(framework_dir, 'ffprobe.exe')

# Add the directory to the system PATH (not the files themselves)
os.environ["PATH"] += os.pathsep + framework_dir

# Paths to other files
path_to_mp3 = os.path.join(framework_dir, f"recaptcha.mp3")
path_to_wav = os.path.join(framework_dir, f"recaptcha.wav")

def collect_ads_balance():
    """
    Simulates collecting ad balance data.
    Replace this with actual scraping or API calls.
    """
    platforms = ["Facebook", "Google Ads", "Twitter", "TikTok"]
    brands = ["Baji", "Six6s", "Jeetbuzz"]
    config_dict = Config.as_dict()
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_info(config_dict, scopes=scope)

    """Fetches data from the spreadsheet."""

    try:
        # Build the service
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Get the main spreadsheet data
        result = sheet.values().get(
            spreadsheetId="1-XxiPmxfN1QxnB93blEu6iY79qCYIh8w4YlSBHUzSFs",
            range="MediaBalance!A2:J"
        ).execute()
        values = result.get("values", [])

        # Get the secondary spreadsheet once
        secondary_result = sheet.values().get(
            spreadsheetId="1PKdQR3zvTNwfDmlEwSayYaFfR7r97fZfRoUlQDUD2OE",
            range="threshold!A2:E"
        ).execute()
        secondary_values = secondary_result.get("values", [])

        # Build CODE → threshold_low dictionary
        code_to_threshold = {
            row[0]: row[4] for row in secondary_values if len(row) > 4
        }

        responses = []

        for row in values:
            platform = row[1]
            code = row[9] if len(row) > 9 else None
            threshold_low = code_to_threshold.get(code, row[7])  # fallback to original row[7] if not found

            if platform == "ADSTERRA":
                response_data = sendRequestADS(row[3], row[4])
                balance = response_data.get("item", 0.0)

            elif platform == "TRAFFICSTARS":
                response_data = sendRequestTRAFF(row[3], row[4])
                balance = response_data.get("balance", 0.0)

            elif platform == "PROFELLERADS":
                balance = profellerAds(row[3], row[4])

            elif platform == "ADXAD":
                response_data = ADXAD(row[3], row[5], row[6])
                balance = response_data.get("data", {}).get("balance", 0.0)

            elif platform == "CLICKADU":
                response_data = CLICKADU(row[3], row[4])
                balance = response_data.get("result", {}).get("advertiser", {}).get("balance", 0.0)

            elif platform == "EZMOB":
                response_data = EZMOB(row[3], row[4])
                balance = response_data["response"]["0"]["balance"]

            elif platform == "POPADS":
                response_data = POPADS(row[3], row[4])
                balance = response_data["user"]["balance"]

            elif platform == "ADCASH":
                balance = ADCASH(row[3], row[5], row[6])

            elif platform == "TRAFFICNOMADS":
                response_data = TRAFFICNOMADS(row[3], row[4])
                balance = response_data.get("balance", 0)

            elif platform == "RICHADS":
                balance = RICHAD(row[3], row[5], row[6])

            elif platform == "DAOAD":
                balance = DAOAD(row[3], row[5], row[6])

            elif platform == "ADPROFEX":
                response_data = ADPROFEX(row[3], row[4])
                balance = response_data.get("data", {}).get("balance", 0.0)

            elif platform == "EVADAV":
                response_data = EVADAV(row[3], row[4])
                balance = response_data.get("data", {}).get("advertiser", 0.0)

            elif platform == "OCTOCLICK":
                response_data = OCTOCLICK(row[3], row[5], row[6])
                balance = response_data.get("data", {}).get("balance_total", 0.0)

            else:
                continue  # Skip unknown platforms

            responses.append({
                "brand": row[0],
                "platform": platform,
                "balance": balance,
                "currency": row[2],
                "threshold_low": threshold_low,
                # "threshold_high": row[8]
            })
            print(responses)

    except HttpError as err:
        print(f"An error occurred: {err}")

    # data = {
    #     "brand": random.choice(brands),
    #     "platform": random.choice(platforms),
    #     "balance": round(random.uniform(100.0, 5000.0), 2),
    #     "currency": "USD"
    # }
    
    return responses

# send api request to ads
def sendRequestADS(link,api):
    headers = {
        "Accept": "application/json",
        "X-API-Key": f"{api}"
    }
    response = requests.get(link, headers=headers)
    # print(response.json())
    return response.json()

# send api to traff
def sendRequestTRAFF(link,api):
    headerAuth = {
        "Content-Type": "application/x-www-form-urlencoded"  # Important for JSON requests
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": f"{api}"  # Replace with your actual refresh token
    }
    responseAuth = requests.post("https://api.trafficstars.com/v1/auth/token", headers=headerAuth, data=data)
    token = responseAuth.json()
    print(f'TOKEN:{token}')
    headers = {
        "Authorization": f"bearer {token.get('access_token')}"
    }
    response = requests.get(link, headers=headers)
    print("trafficstars request...")
    print(response.json())
    return response.json()

#profeller ads
def profellerAds(link,api):
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": f"application/json",
        "Authorization": f"Bearer {api}"
    }
    response = requests.get(link, headers=headers)
    # print(response.json())
    return response.json()

# ADXAD
def ADXAD(link,email,password):
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": f"application/json",
        "authority": f"td.adxad.com"
    }
    payload = {
        "email":email,
        "password":password,
        "grant_type":"urn:saas-password",
        "scope":"adxad"
    }

    response = requests.post('https://td.adxad.com/api/oauth/token', headers=headers, json=payload)
    token = response.json()
    print(token)

    headersBalance = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token.get('access_token')}"
    }
    responseBalance = requests.get(link, headers=headersBalance)
    # print(response.json())
    return responseBalance.json()

# CLICKADU
def CLICKADU(link,api):
    headersBalance = {
        "accept": "application/json",
        "Authorization": f"{api}"
    }
    responseBalance = requests.get(link, headers=headersBalance)
    # print(response.json())
    #sample response
    # {
    # "result": {
    #     "advertiser": {
    #     "balance": "698.75"
    #     }
    # }
    # }
    return responseBalance.json()

# EZMOB
def EZMOB(link,api):
    headersBalance = {
        "Content-Type": "application/json",
        # "userToken": f"{api}"
    }
    params = {"userToken": api}

    responseBalance = requests.get(link, headers=headersBalance, params=params)
    return responseBalance.json()

#ADPROFEX
def ADPROFEX(link,api):
    headersBalance = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api}"
    }
    responseBalance = requests.get(link, headers=headersBalance)
    return responseBalance.json()

#EVADAV
def EVADAV(link,api):
    headersBalance = {
        "Accept": "application/json",
        "X-Api-Key": f"{api}"
    }
    responseBalance = requests.get(link, headers=headersBalance)
    return responseBalance.json()

#OCTOCLICK
def OCTOCLICK(link,email,password):
    login_url = "https://api.octoclick.com/api/v4/auth/email"
    login_payload = {
        "email": email,
        "password": password
    }

    login_headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(login_url, json=login_payload, headers=login_headers)
    response.raise_for_status()

    data = response.json()
    token = data.get("data", {}).get("token")

    print("Token:", token)

    if not token:
        print("Failed to retrieve token.")
        return

    # Step 2: Use token to access balance endpoint
    balance_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    balance_response = requests.get(link, headers=balance_headers)
    balance_response.raise_for_status()

    balance_data = balance_response.json()
    print("Balance Data:", balance_data)

    return balance_data
    
# POPADS
def POPADS(link,api):
    
    params = {"key": api}

    responseBalance = requests.get(link, params=params)
    print(responseBalance)
    return responseBalance.json()

#ADCASH
def ADCASH(link, email, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--remote-debugging-port=9224",
                "--window-position=-2000,0"
            ],  
            # args=["--window-position=-2000,0"],
            timeout=300000
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 820},
            extra_http_headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Accept-Language": "en-US,en;q=0.9",
                "Content-Type": "application/x-www-form-urlencoded",
                "Sec-CH-UA": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
                "Sec-Fetch-Site": "same-origin",
            }
        )

        page = context.new_page()
        retries = 5
        attempt = 0
        success = False

        while attempt < retries and not success:
            try:
                attempt += 1
                print(f"Attempt {attempt} of {retries}...")

                # Open website
                page.goto(link)
                print("Visiting Adcash page...")

                # Click login button
                page.click('body > header > div > nav.button-menu > a:nth-child(1)')
                print("Login button clicked...")
                page.wait_for_selector('input[name="username"]')

                # Fill in credentials
                page.fill('input[name="username"]', email)
                print("Username filled...")

                page.fill('input[name="password"]', password)
                print("Password filled...")

                # Click login
                page.click('#kc-login')
                page.wait_for_selector('a[title="Wallet"]', timeout=10000)
                print("Successful Login...")

                # Get page content and parse with BeautifulSoup
                html = page.content()
                soup = BeautifulSoup(html, "lxml")

                # Locate the wallet balance
                wallet_link = soup.find("a", {"title": "Wallet"})
                if wallet_link:
                    balance_text = wallet_link.get_text(strip=True).split()[0]
                    balance = re.sub(r"[^\d.]", "", balance_text)
                    print("Wallet Balance:", balance)
                else:
                    print("Wallet balance not found.")
                    balance = None

                browser.close()
                success = True
                return balance

            except Exception as e:
                print(f"Error filling login form: {e}")
                if attempt == retries:
                    print("Max retry attempts reached. Exiting.")
                else:
                    print(f"Retrying... {retries - attempt} attempts left.")
                    time.sleep(3)

def TRAFFICNOMADS(link,api):
    headersBalance = {
        "Content-Type": "application/json",
        "X-Api-Key": f"{api}"
    }

    responseBalance = requests.get(link, headers=headersBalance)
    return responseBalance.json()
#DAOAD
def DAOAD(link, email, password):
    playwright_authenticator = PlaywrightAuthenticator(email, password, 'NOMAD','https://dao.ad/login', 'daoad.com', 0)
    response = playwright_authenticator.authenticate()
    print(f"this is the response:{response}")
    if response.get("Authentication", False) == False:
        print("Authentication failed, retrying...")
        return DAOAD(link, email, password)  # Recursively retry
    return response.get('balance',0.0)
#RICHADS
def RICHAD(link, email,password):
    playwright_authenticator = PlaywrightAuthenticator(email, password, 'RICH','https://my.richads.com/login', 'my.richads.com', 0)
    response = playwright_authenticator.authenticate()
    print(f"this is the response:{response}")
    # Retry logic if authentication fails
    if response.get("Authentication", False) == False:
        print("Authentication failed, retrying...")
        return RICHAD(link, email, password)  # Recursively retry

    
    return response.get('balance',0.0)
