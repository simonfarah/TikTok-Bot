import re
import io
import base64
from os import system
from time import sleep
from PIL import Image
import pytesseract
from selenium import webdriver
import time
from PIL import ImageEnhance, ImageFilter
import cv2
from skimage import filters
# Configure Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Bot:

    def __init__(self):
        system("cls || clear")

        self._print_banner()
        self.driver = self._init_driver()
        self.services = self._init_services()

    def _close_popups(self):
        """Helper method to close any popups (ads, consent forms, etc)"""
        
        print("pop_up_seen")
        try:
            # Check for and close ad popups using multiple selectors
            selectors = [
                "[aria-label='Close ad']",
                ".ns-ji8qz-e-5.close-button",  # Specific ad close button
                "[class*='close-button']",     # Any element with close-button in class
                "[class*='dismiss-button']",   # Any dismiss button
                "button[class*='close']",      # Any button with close in class
            ]
            
            for selector in selectors:
                close_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in close_buttons:
                    if button.is_displayed():
                        try:
                            print(f"[~] Found popup with selector '{selector}', attempting to close...")
                            button.click()
                            print("[+] Popup closed")
                            sleep(0.5)  # Brief pause to let any animations complete
                        except:
                            pass
            
            # Check for and handle consent popup
            try:
                # Try multiple selectors for the consent button, from most to least specific
                consent_selectors = [
                    "button.fc-button.fc-cta-consent.fc-primary-button[role='button'][aria-label='Consent'][tabindex='0']",  # Exact match
                    "button.fc-button.fc-cta-consent.fc-primary-button",  # Class-based
                    ".fc-footer-buttons-container button[aria-label='Consent']",  # Container-based
                    "button[aria-label='Consent']",  # Simple aria-label
                ]
                
                for selector in consent_selectors:
                    try:
                        consent_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if consent_button.is_displayed():
                            print(f"[~] Found consent popup with selector '{selector}'")
                            # Scroll into view if needed
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", consent_button)
                            sleep(0.5)  # Brief pause after scroll
                            consent_button.click()
                            print("[+] Consent popup handled")
                            sleep(0.5)  # Wait for popup to close
                            break
                    except NoSuchElementException:
                        continue
            except Exception as e:
                print(f"[!] Error handling consent popup: {str(e)}")
                
        except Exception as e:
            print(f"[!] Error handling popups: {str(e)}")

    def start(self):
        self.driver.get("https://zefoy.com")
        
        # Initial popup check
        self._close_popups()
        
        # Add periodic popup checks during CAPTCHA solving
        self._solve_captcha()

        # Page refresh 1
        sleep(2)
        self.driver.refresh()

        # Page refresh 2
        sleep(2)
        self.driver.refresh()

        self._check_services_status()
        self.driver.minimize_window()
        self._print_services_list()
        service = self._choose_service()
        video_url = self._choose_video_url()
        self._start_service(service, video_url)

    def _print_banner(self):
        print("+--------------------------------------------------------+")
        print("|                                                        |")
        print("|   Made by : Simon Farah                                |")
        print("|   Github  : https://github.com/simonfarah/tiktok-bot   |")
        print("|                                                        |")
        print("+--------------------------------------------------------+")

        print("\n")

    def _init_driver(self):
        try:
            print("[~] Loading driver, please wait...")
            options = webdriver.FirefoxOptions()
            options.binary_location = "/usr/bin/firefox"
            options.add_argument("--width=800")
            options.add_argument("--height=700")

            service = webdriver.FirefoxService(log_output="geckodriver.log")
            service.path = (
                "/usr/local/bin/geckodriver"  # Assicurati che il percorso sia corretto
            )

            driver = webdriver.Firefox(options=options, service=service)

            print("[+] Driver loaded successfully")
        except Exception as e:
            print("[x] Error loading driver: {}".format(e))
            exit(1)

        print("\n")
        return driver

    def _init_services(self):
        return {
            "followers": {
                "title": "Followers",
                "selector": "t-followers-button",
                "status": None,
            },
            "hearts": {
                "title": "Hearts",
                "selector": "t-hearts-button",
                "status": None,
            },
            "comments_hearts": {
                "title": "Comments Hearts",
                "selector": "t-chearts-button",
                "status": None,
            },
            "views": {
                "title": "Views",
                "selector": "t-views-button",
                "status": None,
            },
            "shares": {
                "title": "Shares",
                "selector": "t-shares-button",
                "status": None,
            },
            "favorites": {
                "title": "Favorites",
                "selector": "t-favorites-button",
                "status": None,
            },
            "live_stream": {
                "title": "Live Stream [VS+LIKES]",
                "selector": "t-livesteam-button",
                "status": None,
            },
        }

    def _solve_captcha(self):
        print("[~] Attempting automatic CAPTCHA solving...")
        max_retries = 20
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Wait for CAPTCHA elements
                input_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "input"))
                )
                captcha_container = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "card.mb-3.word-load"))
                )
                captcha_img = captcha_container.find_element(By.CLASS_NAME, "img-thumbnail")
                
                # Capture CAPTCHA image
                img_data = captcha_img.screenshot_as_png
                img = Image.open(io.BytesIO(img_data))
                
                print("[~] Applying simplified image preprocessing...")
                
                # Convert to grayscale
                img = img.convert('L')
                
                # Basic contrast enhancement
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)  # Increase contrast
                
                # Simple thresholding
                img = img.point(lambda x: 0 if x < 150 else 255)
                
                # Scale up image
                img = img.resize((img.width * 4, img.height * 4), Image.Resampling.BICUBIC)
                
                # Add white border
                border = 30
                new_img = Image.new('L', (img.width + 2*border, img.height + 2*border), 255)
                new_img.paste(img, (border, border))
                img = new_img
                
                print("[~] Performing OCR with basic settings...")
                custom_config = '--psm 7 --oem 3 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz'
                text = pytesseract.image_to_string(img, config=custom_config).strip().lower()
                
                if not text:
                    print("[!] OCR failed to extract text, retrying...")
                    retry_count += 1
                    self.driver.refresh()
                    sleep(2)
                    continue
                
                # Simple text cleaning
                text = ''.join(c for c in text if c.isalpha()).lower()
                
                print(f"[+] OCR extracted text: {text}")
                
                # Submit and verify
                input_field.clear()
                input_field.send_keys(text)
                input_field.submit()
                
                sleep(2)
                
                try:
                    youtube = self.driver.find_element(By.LINK_TEXT, "Youtube")
                    if youtube.is_displayed():
                        print("[+] CAPTCHA solved automatically!")
                        print("\n")
                        return True
                except NoSuchElementException:
                    pass
                
                try:
                    error_modal = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "modal-footer"))
                    )
                    print("[!] Error modal detected, refreshing page...")
                    self.driver.refresh()
                    sleep(2)
                    retry_count += 1
                    continue
                except TimeoutException:
                    print("[!] Could not verify result, refreshing page...")
                    self.driver.refresh()
                    sleep(2)
                    retry_count += 1
                    continue
                    
            except Exception as e:
                print(f"[!] Error during CAPTCHA solving: {str(e)}")
                self.driver.refresh()
                sleep(2)
                retry_count += 1
        
        print("[!] Failed to solve CAPTCHA after maximum retries")
        return False
    def _wait_for_error_modal(self, timeout=5):
        """Wait for error modal to appear and handle it if found"""
        try:
            modal = WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "modal-footer"))
            )
            print("[!] Error modal detected")
            
            # Find and click close button
            close_button = modal.find_element(
                By.CSS_SELECTOR, 
                "button.btn.btn-secondary.col-sm[data-dismiss='modal']"
            )
            close_button.click()
            print("[+] Closed error modal")
            sleep(1)
            return True
        except TimeoutException:
            return False

    def _check_services_status(self):
            for service in self.services:
                selector = self.services[service]["selector"]

                try:
                    element = self.driver.find_element(By.CLASS_NAME, selector)

                    if element.is_enabled():
                        self.services[service]["status"] = "[WORKING]"
                    else:
                        self.services[service]["status"] = "[OFFLINE]"
                except NoSuchElementException:
                    self.services[service]["status"] = "[OFFLINE]"

    def _print_services_list(self):
            for index, service in enumerate(self.services):
                title = self.services[service]["title"]
                status = self.services[service]["status"]

                print("[{}] {}".format(str(index + 1), title).ljust(30), status)

            print("\n")

    def _choose_service(self):
            while True:
                try:
                    choice = int(input("[~] Choose an option : "))
                except ValueError:
                    print("[!] Invalid input format. Please try again...")
                    print("\n")
                    continue

                if choice in range(1, 8):
                    key = list(self.services.keys())[choice - 1]

                    if self.services[key]["status"] == "[OFFLINE]":
                        print("[!] Service is offline. Please choose another...")
                        print("\n")
                        continue

                    print("[+] You have chosen {}".format(self.services[key]["title"]))
                    print("\n")
                    break
                else:
                    print("[!] No service found with this number")
                    print("\n")

            return key

    def _choose_video_url(self):
        video_url = input("[~] Video URL : ")
        print("\n")

        return video_url

    def _start_service(self, service, video_url):
        # Close any popups before starting
        self._close_popups()
        
        # Click on the corresponding service button
        self._wait_for_element(
            By.CLASS_NAME, self.services[service]["selector"]
        ).click()

        # Get the container of the selected service
        container = self._wait_for_element(
            By.CSS_SELECTOR, "div.col-sm-5.col-xs-12.p-1.container:not(.nonec)"
        )

        # Insert the video url in the input field
        input_element = container.find_element(By.TAG_NAME, "input")
        input_element.clear()
        input_element.send_keys(video_url)

        while True:
            # Close any popups before clicking
            self._close_popups()
            
            # Click the search button
            container.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

            sleep(2)
            # Check for popups after search click
            self._close_popups()
            sleep(1)

            # Click the submit button if it's present, otherwise pass
            try:
                container.find_element(By.CSS_SELECTOR, "button.btn.btn-dark").click()
                print(
                    "[~] {} sent successfully".format(self.services[service]["title"])
                )
            except NoSuchElementException:
                pass

            sleep(2)
            # Check for popups after submit
            self._close_popups()
            sleep(1)

            remaining_time = self._compute_remaining_time(container)

            if remaining_time is not None:
                minutes = remaining_time // 60
                seconds = remaining_time - minutes * 60
                print("[~] Sleeping for {} minutes {} seconds".format(minutes, seconds))
                sleep(remaining_time)

            print("\n")

    def _compute_remaining_time(self, container):
        try:
            element = container.find_element(By.CSS_SELECTOR, "span.br")
            text = element.text

            if "Please wait" in text:
                [minutes, seconds] = re.findall(r"\d+", text)
                remaining_time = (
                    int(minutes) * 60 + int(seconds) + 5
                )  # plus 5 for safety

                return remaining_time
            else:
                print("NO TIME")
                return None
        except NoSuchElementException:
            print("NO ELEMENT")
            return None

    def _wait_for_element(self, by, value):
        while True:
            try:
                element = self.driver.find_element(by, value)
                return element
            except NoSuchElementException:
                sleep(1)


if __name__ == "__main__":
    bot = Bot()
    bot.start()
