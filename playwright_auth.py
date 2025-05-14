import logging
import os
import urllib.request
import pydub
import sys
import random
import time
import json
import asyncio
from pathlib import Path
from fake_useragent import UserAgent
import speech_recognition as sr
from pydub.playback import play
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
# from playwright_stealth import stealth
# from playwright_stealth import stealth_sync

from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaywrightAuthenticator:
    def __init__(self, username, password, code,login_url, target_domain, api_key):
        """
        Initialize the authenticator.

        Args:
            username (str): The username for login.
            password (str): The password for login.
            login_url (str): The login page URL.
            target_domain (str): The domain for which cookies are required.
        """
        self.username = username
        self.password = password
        self.login_url = login_url
        self.target_domain = target_domain
        self.cookies = None
        self.api_key = api_key
        self.code = code
        self.solved = False
        self.profile = False
        # Get the directory where ffmpeg.exe and ffprobe.exe are located
        framework_dir = os.getcwd()  # Assuming ffmpeg.exe and ffprobe.exe are in the current working directory

        # self.session_dir = "sessions"
        self.session_file_name = f"{code}_{datetime.now().strftime('%Y-%m-%d')}.json"
        # self.session_file_path = os.path.join(self.session_dir, self.session_file_name)
        self.session_file_path = os.path.join('sessions', self.session_file_name)
        # Set the paths to ffmpeg and ffprobe
        self.ffmpeg_path = os.path.join(framework_dir, 'ffmpeg.exe')
        self.ffprobe_path = os.path.join(framework_dir, 'ffprobe.exe')

        # Add the directory to the system PATH (not the files themselves)
        os.environ["PATH"] += os.pathsep + framework_dir

        # Paths to other files
        self.path_to_mp3 = os.path.join(framework_dir, f"{code}.mp3")
        self.path_to_wav = os.path.join(framework_dir, f"{code}.wav")

        # try:
        #     os.system("ffmpeg -version")
        # except Exception as e:
        #     print(f"FFmpeg error: {e}")

    def authenticate(self):
        """
        Perform login and retrieve cookies for the target domain.

        Returns:
            list[dict]: List of cookies for the target domain.
        """
        with sync_playwright() as p:
            # Using fake-useragent to generate a random user agent for each session
            ua = UserAgent()
            user_agent = ua.random
            os.makedirs("sessions", exist_ok=True)
            # Randomly choose a browser from the available ones
            browser_choice = random.choice(["chromium", "firefox", "webkit", "firefox", "webkit"])
            # browser_choice = random.choice(["firefox"])
            # Randomly decide whether to run in headless mode
            headless_mode = random.choice([False])
            
            if browser_choice == "firefox":    
                browser = p.firefox.launch(
                    headless=headless_mode,
                    timeout=60000  # Increase timeout for WebKit
                )
            elif browser_choice == "webkit":
                browser = p.webkit.launch(
                    headless=headless_mode,
                    
                    timeout=60000  # Increase timeout for WebKit
                )
            else:
                browser = p.chromium.launch(
                    headless=headless_mode,
                    timeout=60000  # Increase timeout for WebKit
                )
            # Define a list of possible viewport sizes
            viewports = [
                {"width": 1280, "height": 800},
                {"width": 1280, "height": 768},
                {"width": 1280, "height": 720},
                {"width": 1176, "height": 664},
                
            ]
            # Randomly select a viewport size from the list
            selected_viewport = random.choice(viewports)
            if self.code.startswith("RICH"):

                context = browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                            viewport=selected_viewport,  # Set a realistic viewport
                            extra_http_headers={
                                "Accept": "*/*",
                                "Accept-Encoding": "gzip, deflate, br, zstd",
                                "Accept-Language": "en-US,en;q=0.9",
                                # "Content-Type": "text/plain",
                                "Origin": f"https://my.richads.com",
                                "Referer": f"https://my.richads.com",
                                "Sec-CH-UA": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
                                "Sec-CH-UA-Mobile": "?0",
                                "Sec-CH-UA-Platform": '"Windows"',
                                "Sec-Fetch-Dest": "empty",
                                # "Sec-Fetch-Mode": "no-cors",
                                "Sec-Fetch-Site": "cross-site",
                                # "X-Requested-With": "XMLHttpRequest"
                            }
                        )
            elif self.code.startswith("NOMAD"):
                context = browser.new_context(
                    user_agent=user_agent,
                    # user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 820},   # Set the same viewport size as your regular browser
                    locale="en-US",                            # Set locale to match your regular browsing locale
                    timezone_id="America/New_York"
                )

            page = context.new_page()
            page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            """)
            # Perform login
            try:
                page.goto(self.login_url)
               
                
                # Check if the code starts with "NOMAD" or "RICH"
                if self.code.startswith("NOMAD"):

                        print("The code starts with NOMAD")
                        # Randomly move mouse to email field before filling
                        # self.random_mouse_move(page, 'input[name="LoginForm[email]"]')
                        page.fill('input[name="LoginForm[email]"]', self.username)
                        self.random_delay(1, 3)  # Random delay between 1 to 3 seconds

                        # Randomly move mouse to email field before filling
                        # self.random_mouse_move(page, 'input[name="LoginForm[password]"]')
                        page.fill('input[name="LoginForm[password]"]', self.password)
                        self.random_delay(1, 3)  # Random delay between 1 to 3 seconds

                        self.solved = self.solve_recaptcha(page)
                
                elif self.code.startswith("RICH"):
                      # Randomly move mouse to email field before filling
                    # self.random_mouse_move(page, 'input[name="email"]')
                    page.fill('input[name="email"]', self.username)
                    self.random_delay(1, 3)  # Random delay between 1 to 3 seconds

                    # Randomly move mouse to email field before filling
                    # self.random_mouse_move(page, 'input[name="password"]')
                    page.fill('input[name="password"]', self.password)
                    self.random_delay(1, 3)  # Random delay between 1 to 3 seconds
                    print("The code starts with RICH")
                    page.get_by_role("button", name="Log In").click()
                    time.sleep(6)
                    # page.screenshot(path="debug_captcha.png")

                    print("Clicked 'Log In' button.")

                    is_logged_in = page.is_visible("img.mat-mdc-tooltip-trigger.manager-photo")
                    # time.sleep(6)
                    if is_logged_in:
                        print("Logged in successfully!")
                        # Optionally, confirm the image's src attribute
                        img_src = page.get_attribute("img.mat-mdc-tooltip-trigger.manager-photo", "src")
                        print("Profile Image Source:", img_src)
                        self.solved = True
                        self.profile = True
                    else:
                        print("Not logged in or profile image not found.")

                        self.solved = self.solve_recaptch_richads(page)
                    
                else:
                    print("The code does not start with NOMAD or RICH.")


                if self.solved:
                   
                    if self.code.startswith("NOMAD"):
                        print("You are daoad")
                        try:
                            self.random_delay(1, 3)  # Random delay between 1 to 3 seconds
                            page.get_by_role("button", name="Log In").click()
                            time.sleep(5)
                            
                            
                            html = page.content()
                            soup = BeautifulSoup(html, "lxml")

                            all_h2 = soup.find_all("h2")

                            for h2 in all_h2:
                                text = h2.get_text(strip=True)
                                
                                if "$" in text:
                                    # Option 1: Remove the $ sign and convert to float
                                    amount = float(text.replace('$', '').strip())
                                    print("🎯 Found balance:", amount)
                                    break
                                else:
                                    print("⏭ Skipped:", text)
                            return {
                                    "status" : 200,
                                    "Authentication" : True,
                                    "balance": amount,
                                    
                                } 
                        except PlaywrightTimeoutError:
                            logging.error("Timeout during form submission.")
                            return {
                                "status" : 400,
                                "Authentication" : False,
                                "cookies": []
                            }
                    else:
                        try:
                            if self.profile:
                                logger.info(f"Your already Authneticated...")
                                # return True
                            
                                
                            else:
                                page.get_by_role("button", name="Log In").click()

                            time.sleep(3)
                            
                            # Get page content and parse with BeautifulSoup
                            # Get the page content
                            html = page.content()

                            # Parse with BeautifulSoup
                            soup = BeautifulSoup(html, "lxml")

                            # Find all 'span' elements
                            all_spans = soup.find_all("span")

                            # Loop through the spans and check for the text that follows the '$' symbol
                            for i, span in enumerate(all_spans):
                                if span.get_text() == "$":
                                    # The next span should be the value
                                    next_span = all_spans[i + 1]
                                    print("Balance value:", next_span.get_text(strip=True))
                                                            
                            
                            return {
                                    "status" : 200,
                                    "Authentication" : True,
                                    "balance": next_span.get_text(strip=True),
                                    
                                } 
                        
                        except PlaywrightTimeoutError:
                            logging.error("Timeout during form submission.")
                            return {
                                "status" : 400,
                                "Authentication" : False,
                                "cookies": []
                            }
                    # return False
                else:
                    logger.info('Retry again...')
                    return {
                            "status" : 400,
                            "Authentication" : False,
                            "cookies": []
                        }
                     
            except Exception as e:
                logging.error(f"Error filling login form: {e}")
                return {
                            "status" : 400,
                            "Authentication" : False,
                            "cookies": []
                        }
            
            # Ensure the directory exists
            # session_dir = os.path.dirname(self.session_file_path)
            # if not os.path.exists(session_dir):
            #     os.makedirs(session_dir)
            #     logging.info(f"Directory '{session_dir}' created.")

            # # Get cookies for the target domain
            # state = context.storage_state()
            # Path(self.session_file_path).write_text(json.dumps(state))
            # logging.info("Session saved.")
            # Save the session state to the specified file
            # logger.info(self.session_file_path)
            # state = context.storage_state()
            # Path(self.session_file_path).write_text(json.dumps(state))
            
        # browser.close()

        # return self.cookies

    # Random delay between actions (in seconds)
    def random_delay(self,min_delay=1.0, max_delay=3.0):
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)

    def random_mouse_move(self,page, element_locator):
        """
        Simulate mouse movements to an element on the page with randomized movements.
        """
        element = page.locator(element_locator)
        element_box = element.bounding_box()
        
        if element_box:
             # Cast x and y values to integers to prevent float -> int conversion issues
            x = random.randint(int(element_box['x']), int(element_box['x'] + element_box['width']))
            y = random.randint(int(element_box['y']), int(element_box['y'] + element_box['height']))
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.5, 1.5))  # Simulate hover delay
            page.mouse.click(x, y)

    def get_cookie_header(self):
        """
        Convert cookies into a header-friendly format for API requests.

        Returns:
            dict: A dictionary with the "Cookie" header.
        """
        if not self.cookies:
            raise ValueError("Authenticate first to retrieve cookies.")

        cookie_header = "; ".join(f"{cookie['name']}={cookie['value']}" for cookie in self.cookies)
        return {"Cookie": cookie_header}

    def solve_recaptch_richads(self, page):
        # Locate all iframes with the title "reCAPTCHA"
        iframes = page.locator('iframe[title="reCAPTCHA"]')

        # Ensure at least one iframe is found
        iframe_count = iframes.count()
        if iframe_count == 0:
            logging.error("No reCAPTCHA iframe found.")
            return False

        # Access the first iframe using nth(0)
        iframe_locator = iframes.nth(0)

        # Check if the iframe is visible and ready
        try:
            # Wait for the iframe to be visible
            iframe_locator.wait_for(state="visible", timeout=10000)
            logging.info("Iframe is now visible.")

            # Access the content of the iframe
            iframe_content = iframe_locator.content_frame  # Correct usage of content_frame()

            # Check if the content of the iframe was accessed
            if iframe_content:
                logging.info("Iframe content accessed successfully.")
                 # Now, interact with elements inside the iframe, e.g., clicking the checkbox
                checkbox = iframe_content.locator('div.recaptcha-checkbox-border')
                checkbox.click()  # Example action on the checkbox
    
                logging.info("ReCAPTCHA checkbox clicked successfully.")
                # Check if the checkbox has the 'recaptcha-checkbox-checked' class
                checkbox_class = checkbox.get_attribute('class')
                if 'recaptcha-checkbox-checked' in checkbox_class:
                    print("ReCAPTCHA checkbox is already checked.")
                    return True
                else:
                    print("ReCAPTCHA checkbox is not checked.")

                if self.check_dos_captcha(page):
                    raise Exception("Detected 'Try again later' message.")
                status = self.solve_audio_challenge(page)
                if status:
                    logger.info("Audio solved!")
                    return True
                else:
                    logger.info("Audio not solved!")
                    return False
                #     return {
                #             "status" : 400,
                #             "Authentication" : False,
                #             "cookies": []
                #         }
                # # return iframe_content
            else:
                logging.error("Failed to access iframe content.")
                return False

        except Exception as e:
            logging.error(f"Error: {str(e)} - iframe not visible or could not access iframe content.")
            return False
        
    def solve_recaptcha(self, page):
        if page.frame_locator('iframe').first.locator('div.recaptcha-checkbox-border').is_visible():
            page.frame_locator('iframe').first.locator('div.recaptcha-checkbox-border').click()
            # Wait for a brief moment to ensure the checkbox state has been updated
            page.wait_for_timeout(1000)  # Wait for 1 second (adjust timing if needed)
            checkbox_locator = page.frame_locator('iframe').first.locator('span.recaptcha-checkbox')

            # Check if the checkbox has the 'recaptcha-checkbox-checked' class
            checkbox_class = checkbox_locator.get_attribute('class')
            if 'recaptcha-checkbox-checked' in checkbox_class:
                print("ReCAPTCHA checkbox is already checked.")
                return True
            else:
                print("ReCAPTCHA checkbox is not checked.")

            if self.check_dos_captcha(page):
                raise Exception("Detected 'Try again later' message.")
            status = self.solve_audio_challenge(page)
            if status:
                logger.info("Audio solved!")
                return True
            else:
                logger.info("Audio not solved!")
                return False
                # return {
                #             "status" : 400,
                #             "Authentication" : False,
                #             "cookies": []
                #         }
        else:
            print("ReCAPTCHA checkbox not found.")
            return False

    def check_dos_captcha(self, page):
        try:
            print("[INFO] Checking for the 'Try again later' message...")
            page.wait_for_selector('iframe[title="recaptcha challenge expires in two minutes"]', timeout=2000)
            iframe = page.frame_locator('iframe[title="recaptcha challenge expires in two minutes"]')
            page.wait_for_timeout(1)
            try_again_message_locator = iframe.locator('body > div > div > div:nth-child(1) > div.rc-doscaptcha-body > div > a')
            is_visible = try_again_message_locator.is_visible(timeout=2000)
            if is_visible:
                text_content = try_again_message_locator.inner_text()
                print(f"[INFO] 'Try again later' message detected: {text_content}")
                return True
            else:
                print("[INFO] 'Try again later' message not visible.")
                return False
        except Exception as e:
            print(f"[ERROR] An error occurred while checking 'Try again later' message: {e}")
            try:
                all_text = iframe.locator('body').inner_text()
                print(f"[DEBUG] Full text in iframe: {all_text}")
            except Exception as inner_e:
                print(f"[ERROR] Failed to retrieve iframe text content: {inner_e}")
            return True

    def solve_audio_challenge(self, page):
        audio_frame = page.frame_locator('iframe[title="recaptcha challenge expires in two minutes"]')
        audio_button = audio_frame.locator('button#recaptcha-audio-button')
        if audio_button.is_visible():
            audio_button.click()
            print("[INFO] Audio button clicked. Waiting for the audio source...")
            try:
                audio_source = audio_frame.locator('audio').get_attribute('src', timeout=3000)
                if not audio_source:
                    raise Exception("No audio source found.")
                print(f"[INFO] Audio source found: {audio_source}")

                urllib.request.urlretrieve(audio_source, self.path_to_mp3)
                print("[INFO] Audio CAPTCHA downloaded. Converting to WAV format...")
                # sound = pydub.AudioSegment.from_mp3(self.path_to_mp3)
                print(f"[INFO] Audio src: {audio_source}")

                # download_audio(audio_source, self.path_to_mp3)
                """Downloads audio from the provided URL."""
                try:
                    urllib.request.urlretrieve(audio_source, self.path_to_mp3)
                    print(f"[INFO] Audio downloaded successfully as '{self.path_to_mp3}'")
                except Exception as e:
                    print(f"[ERROR] Failed to download audio: {e}")

                """Plays the audio and attempts to recognize the CAPTCHA key."""
                try:
                    sound = pydub.AudioSegment.from_mp3(self.path_to_mp3)
                    sound.export(self.path_to_wav, format="wav")
                    sample_audio = sr.AudioFile(self.path_to_wav)
                except Exception as e:
                    print(f"[ERROR] Failed to convert MP3 to WAV: {e}")
                    sys.exit("[ERR] Please run the program as administrator or ensure that FFmpeg is correctly set up.")

                try:
                    play(sound)
                except Exception as e:
                    print(f"[ERROR] Failed to play audio: {e}")

                r = sr.Recognizer()
                with sample_audio as source:
                    audio = r.record(source)

                try:
                    key = r.recognize_google(audio)
                    print(f"[INFO] Recaptcha Passcode: {key}")
                except sr.UnknownValueError:
                    print("[ERROR] Google Speech Recognition could not understand the audio")
                    key = False
                except sr.RequestError as e:
                    print(f"[ERROR] Could not request results from Google Speech Recognition service; {e}")
                    key = False

                if not key:
                    raise Exception("Failed to recognize the CAPTCHA passcode.")
                audio_input_locator = audio_frame.locator('#audio-response')
                if audio_input_locator.is_visible():
                    audio_input_locator.fill(key)
                    print(f"[INFO] Recaptcha Passcode entered: {key}")
                    verify_button_locator = audio_frame.locator('#recaptcha-verify-button')
                    verify_button_locator.click()
                    print("[INFO] Recaptcha verify button clicked.")
                    page.wait_for_timeout(2)
                    return True
            except PlaywrightTimeoutError:
                logging.error("Audio challenge failed due to timeout.")
                page.reload()  # This reloads the current page in the browser
                return False
                # return {
                #             "status" : 400,
                #             "Authentication" : False,
                #             "cookies": []
                #         }