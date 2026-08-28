"""Open IMDb 2024 movies and extract visible movie titles safely."""

import re
import time

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

TITLE_LINK_SELECTOR = "a[href*='/title/tt']"
MOVIE_CARD_SELECTOR = "li.ipc-metadata-list-summary-item"


def clean_title(raw_title):
    """Remove IMDb ranking prefixes such as '1. Movie Name'."""
    return re.sub(r"^\d+\.\s*", "", raw_title).strip()


def create_driver():
    """Create and return a Chrome WebDriver configured for this project."""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-notifications")
    options.page_load_strategy = "eager"

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver


def page_has_movie_titles(driver):
    """Return True when IMDb title links are present on the current page."""
    return bool(driver.find_elements(By.CSS_SELECTOR, TITLE_LINK_SELECTOR))


def load_imdb_page(driver, attempts=3):
    """Open IMDb and retry if the result page does not load correctly."""
    for attempt in range(1, attempts + 1):
        print(f"Opening IMDb page - attempt {attempt}/{attempts}...")

        try:
            driver.get(IMDB_URL)
        except TimeoutException:
            print("Page load took too long. Checking the loaded content...")

        try:
            WebDriverWait(driver, 30).until(
                lambda browser: browser.execute_script(
                    "return document.readyState"
                )
                in ("interactive", "complete")
            )

            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, TITLE_LINK_SELECTOR)
                )
            )
        except TimeoutException:
            pass

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title or "[blank]")

        if page_has_movie_titles(driver):
            return True

        if attempt < attempts:
            print("Movie data not detected. Retrying...")
            time.sleep(3)
            driver.refresh()
            time.sleep(2)

    return False


def extract_title_from_card(card):
    """Extract a valid movie title from one IMDb result card."""
    links = card.find_elements(By.CSS_SELECTOR, TITLE_LINK_SELECTOR)

    for link in links:
        text = link.text.strip()
        href = link.get_attribute("href") or ""

        if text and "/title/tt" in href:
            title = clean_title(text.split("\n")[0])
            if title:
                return title, href

    return None, None


def scrape_visible_titles(driver):
    """Extract visible movie titles from IMDb without duplicate titles."""
    cards = driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)
    print(f"Movie cards found: {len(cards)}")

    titles = []
    seen_links = set()

    for card in cards:
        title, href = extract_title_from_card(card)

        if title and href and href not in seen_links:
            seen_links.add(href)
            titles.append(title)

    # Fallback if IMDb changes the result-card wrapper but keeps title links.
    if not titles:
        print("Card-based extraction returned no titles. Using link fallback...")

        links = driver.find_elements(By.CSS_SELECTOR, TITLE_LINK_SELECTOR)

        for link in links:
            text = link.text.strip()
            href = link.get_attribute("href") or ""

            if not text or not href or href in seen_links:
                continue

            title = clean_title(text.split("\n")[0])

            if title:
                seen_links.add(href)
                titles.append(title)

    return titles


def main():
    """Launch Chrome, open IMDb, and print visible 2024 movie titles."""
    driver = None

    try:
        print("Starting Chrome...")
        driver = create_driver()

        if not load_imdb_page(driver):
            print("\nIMDb did not return the movie-results page after 3 attempts.")
            print("Check the Chrome window for a network, consent, or verification page.")
            input("Press Enter to close Chrome...")
            return

        titles = scrape_visible_titles(driver)

        print("\nIMDb 2024 Movies")
        print("-" * 50)

        for number, title in enumerate(titles, start=1):
            print(f"{number}. {title}")

        print(f"\nMovie titles extracted: {len(titles)}")
        input("\nPress Enter to close Chrome...")

    except WebDriverException as error:
        print("\nSelenium/Chrome error:")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))
        input("\nPress Enter to close Chrome...")

    except Exception as error:
        print("\nUnexpected error:")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))
        input("\nPress Enter to close Chrome...")

    finally:
        if driver is not None:
            driver.quit()
            print("Chrome closed.")


if __name__ == "__main__":
    main()
