"""Open IMDb 2024 and extract visible movie titles with Selenium."""

import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
)

TITLE_SELECTOR = ".ipc-title__text"
MOVIE_CARD_SELECTOR = "li.ipc-metadata-list-summary-item"


def clean_title(raw_title):
    """Remove ranking prefixes such as '1. Movie Name'."""
    return re.sub(r"^\d+\.\s*", "", raw_title).strip()


def create_driver():
    """Create a normal visible Chrome browser."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-notifications")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)
    return driver


def save_debug_files(driver):
    """Save the current page when IMDb does not load as expected."""
    debug_dir = Path("data/raw")
    debug_dir.mkdir(parents=True, exist_ok=True)

    screenshot_path = debug_dir / "imdb_debug.png"
    html_path = debug_dir / "imdb_debug.html"

    try:
        driver.save_screenshot(str(screenshot_path))
        html_path.write_text(driver.page_source, encoding="utf-8")
        print(f"Debug screenshot saved to: {screenshot_path}")
        print(f"Debug HTML saved to: {html_path}")
    except Exception as error:
        print("Could not save debug files:", repr(error))


def find_movie_titles(driver, timeout=20):
    """Wait for IMDb movie-title elements and return them."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, TITLE_SELECTOR)
            )
        )
    except TimeoutException:
        return []


def load_imdb(driver):
    """Open IMDb and allow manual completion of human verification."""
    print("Opening IMDb 2024 movies page...")

    try:
        driver.get(IMDB_URL)
    except TimeoutException:
        print("Initial page load timed out. Checking the browser...")

    time.sleep(3)

    print("Current URL:", driver.current_url)
    print("Page title:", driver.title or "[blank]")

    title_elements = find_movie_titles(driver, timeout=15)

    if title_elements:
        return title_elements

    print("\nIMDb movie data is not visible yet.")
    print("If Chrome shows 'Human Verification', complete it manually.")
    print("Do NOT close Chrome.")
    input("After the normal IMDb movie list appears, press Enter here...")

    print("Checking IMDb again after verification...")
    time.sleep(2)

    print("Current URL:", driver.current_url)
    print("Page title:", driver.title or "[blank]")

    return find_movie_titles(driver, timeout=30)


def extract_titles(elements):
    """Convert Selenium title elements into a clean unique title list."""
    titles = []
    seen = set()

    for element in elements:
        raw_title = element.text.strip()

        if not raw_title:
            continue

        title = clean_title(raw_title)

        if title and title not in seen:
            seen.add(title)
            titles.append(title)

    return titles


def print_first_movie_card(driver):
    """Print visible text from the first IMDb result card for inspection."""
    cards = driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)

    print("\nFIRST MOVIE CARD DATA")
    print("-" * 50)

    if not cards:
        print("No movie cards found with the current selector.")
        print("-" * 50)
        return

    print(cards[0].text)
    print("-" * 50)


def main():
    """Launch Chrome and print visible IMDb 2024 movie titles."""
    driver = None

    try:
        print("Starting Chrome...")
        driver = create_driver()

        title_elements = load_imdb(driver)

        if not title_elements:
            print("\nIMDb movie titles still could not be detected.")
            save_debug_files(driver)
            input("\nPress Enter to close Chrome...")
            return

        titles = extract_titles(title_elements)

        print(f"\nTitle elements found: {len(title_elements)}")
        print("\nIMDb 2024 Movies")
        print("-" * 50)

        for number, title in enumerate(titles, start=1):
            print(f"{number}. {title}")

        print(f"\nMovie titles extracted: {len(titles)}")

        print_first_movie_card(driver)

        input("\nPress Enter to close Chrome...")

    except WebDriverException as error:
        print("\nSelenium/Chrome error")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        if driver is not None:
            save_debug_files(driver)

        input("\nPress Enter to close Chrome...")

    except Exception as error:
        print("\nUnexpected error")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        if driver is not None:
            save_debug_files(driver)

        input("\nPress Enter to close Chrome...")

    finally:
        if driver is not None:
            driver.quit()
            print("Chrome closed.")


if __name__ == "__main__":
    main()
