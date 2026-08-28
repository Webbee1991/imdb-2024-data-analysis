"""Open IMDb 2024 movies and extract visible movie titles."""

import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
)


def clean_title(raw_title):
    """Remove IMDb's numeric ranking prefix, for example '1. Movie Name'."""
    return re.sub(r"^\d+\.\s*", "", raw_title).strip()


def extract_title_from_card(card):
    """Return the visible title text from one IMDb movie card."""
    selectors = [
        "a.ipc-title-link-wrapper",
        "a[href*='/title/tt']",
    ]

    for selector in selectors:
        elements = card.find_elements(By.CSS_SELECTOR, selector)
        for element in elements:
            text = element.text.strip()
            href = element.get_attribute("href") or ""

            if text and "/title/tt" in href:
                return clean_title(text.split("\n")[0])

    return None


def open_imdb_page():
    """Launch Chrome, open IMDb, and extract visible movie titles."""
    options = Options()
    options.add_argument("--start-maximized")

    print("Starting Chrome...")
    driver = webdriver.Chrome(options=options)

    try:
        print("Opening IMDb 2024 movies page...")
        driver.get(IMDB_URL)
        print("Page title:", driver.title)

        print("Waiting for IMDb movie cards...")
        print("If IMDb shows a human verification, complete it manually.")

        movie_cards = WebDriverWait(driver, 300).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")
            )
        )

        print(f"Movie cards found: {len(movie_cards)}")

        titles = []

        for card in movie_cards:
            title = extract_title_from_card(card)
            if title:
                titles.append(title)

        print("\nFirst visible movie titles:")
        for number, title in enumerate(titles[:10], start=1):
            print(f"{number}. {title}")

        print(f"\nMovie titles extracted: {len(titles)}")
        input("Press Enter to close Chrome...")
    finally:
        driver.quit()


if __name__ == "__main__":
    open_imdb_page()
