import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException


class SubtitleDownloader:
    def __init__(self, username, password, link_sub, from_episode, to_episode):
        # Get the current working directory
        self.download_dir = os.path.join(os.getcwd(), 'downloaded_srt_eng')
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        # Set Chrome options
        chrome_options = webdriver.ChromeOptions()
        prefs = {'download.default_directory': self.download_dir}
        chrome_options.add_experimental_option('prefs', prefs)

        # Initialize the webdriver with the options
        self.driver = webdriver.Chrome(options=chrome_options)
        self.username = username
        self.password = password
        self.link_sub = link_sub
        self.from_episode = from_episode
        self.to_episode = to_episode

    def eps(self):
        if self.from_episode == self.to_episode:
            self.download_sub_episode(self.from_episode)
        else:
            for eps in range(self.from_episode, self.to_episode + 1):
                self.download_sub_episode(eps)
        self.driver.quit()

    def download_sub_episode(self, episode_number):
        self.driver.get(self.link_sub)
        self.driver.set_window_size(1936, 1096)

        # Click on the episode download button
        self.safe_click(f".box:nth-child({episode_number}) > .box-sub-action-button .btn")

        # Click on the download buttons
        self.safe_click(".hidden-xs > .icon-download")
        self.safe_click(".hidden-xs > .icon-download")
        self.safe_click(".flag:nth-child(2)")
        self.safe_click(".btn-warning > .icon-download")
        self.safe_click(".no-opt-link")
        self.safe_click(".btn-sm")
        self.safe_click(".mfp-close")

        # Rename the downloaded file
        self.rename_latest_file(episode_number)

    def safe_click(self, css_selector):
        retries = 3
        for _ in range(retries):
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
                )
                element.click()
                return True
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)
        return False

    def safe_send_keys(self, css_selector, keys):
        retries = 3
        for _ in range(retries):
            try:
                element = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, css_selector))
                )
                element.send_keys(keys)
                return True
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(1)
        return False

    def rename_latest_file(self, episode_number):
        # Wait for the file to be fully downloaded
        time.sleep(5)  # Adjust this sleep if needed for larger files

        # Find the latest file in the download directory
        files = [f for f in os.listdir(self.download_dir) if os.path.isfile(os.path.join(self.download_dir, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.download_dir, x)), reverse=True)
        latest_file = files[0] if files else None

        if latest_file:
            # Define the new file name
            new_name = f"episode_{episode_number}.srt"
            new_path = os.path.join(self.download_dir, new_name)
            old_path = os.path.join(self.download_dir, latest_file)

            # Rename the file
            os.replace(old_path, new_path)
            print(f"Renamed {old_path} to {new_path}")

    def login(self):
        self.driver.get(self.link_sub)
        self.driver.set_window_size(1936, 1096)
        if self.check_element_exists("#public_user_links .login-li > .visible-lg-inline"):
            # Login
            self.safe_click("#public_user_links .login-li > .visible-lg-inline")

            self.safe_send_keys("#user_login", self.username)
            self.safe_send_keys("#user_password", self.password)

            self.safe_click(".checkbox > label")

            self.safe_click("#page_login_btn")
        self.eps()

    def check_element_exists(self, css_selector):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
            )
            return True
        except NoSuchElementException:
            return False


if __name__ == "__main__":
    # username = input("Username from opensubtitles: ")
    # password = input("Password from opensubtitles: ")
    # link_sub = input("Put sub link from opensubtitles: ")
    # from_episode = int(input("From Episode: "))
    # to_episode = int(input("To Episode: "))

    username = "xochaels"
    password = "opensubtitles.com"
    link_sub = "https://www.opensubtitles.com/en/tvshows/2024-marry-my-husband"
    from_episode = 1
    to_episode = 2
    downloader = SubtitleDownloader(username, password, link_sub, from_episode, to_episode)
    downloader.login()
