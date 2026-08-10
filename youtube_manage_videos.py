from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

def main():
    # Set up Chrome options (uncomment if you need headless mode)
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # Initialize the Chrome WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Step 1: Go to YouTube
        print("Navigating to YouTube...")
        driver.get("https://www.youtube.com")
        time.sleep(3)

        # Step 2: Wait for the page to load and find the account icon
        print("Waiting for account icon to load...")
        wait = WebDriverWait(driver, 15)

        # The account icon is typically at the top-right corner
        # YouTube uses a button with class 'style-scope ytd-button-renderer' or an image for user avatar
        account_icon = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#avatar-btn"))
        )
        print("Clicking account icon...")
        account_icon.click()
        time.sleep(2)

        # Step 3: Click on "Manage videos" from the dropdown menu
        print("Looking for 'Manage videos' option...")
        manage_videos = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Manage videos')]"))
        )
        print("Clicking 'Manage videos'...")
        manage_videos.click()
        time.sleep(3)

        print("Successfully navigated to 'Manage videos' page!")
        print(f"Current URL: {driver.current_url}")

        # Keep the browser open to view the result
        print("\nBrowser will stay open. Close it manually when done.")
        input("Press Enter to close the browser...")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()
