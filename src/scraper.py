"""Open IMDb 2024 movies and extract visible movie titles."""

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
)


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
        print("\nFirst visible movie titles:")

        titles = []

        for card in movie_cards:
            try:
                title_element = card.find_element(
                    By.CSS_SELECTOR,
                    "h3.ipc-title__text",
                )
                titles.append(title_element.text)
            except NoSuchElementException:
                continue

        for title in titles[:10]:
            print(title)

        print(f"\nMovie titles extracted: {len(titles)}")
        input("Press Enter to close Chrome...")
    finally:
        driver.quit()


if __name__ == "__main__":
    open_imdb_page()
