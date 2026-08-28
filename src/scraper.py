"""Open IMDb 2024 movies and extract the first movie title."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
)


def open_imdb_page():
    """Launch Chrome, open IMDb, and extract the first movie title."""
    options = Options()
    options.add_argument("--start-maximized")

    print("Starting Chrome...")
    driver = webdriver.Chrome(options=options)

    try:
        print("Opening IMDb 2024 movies page...")
        driver.get(IMDB_URL)
        print("Page title:", driver.title)

        print("Waiting for the IMDb movie list...")
        print("If IMDb shows a human verification, complete it manually.")

        first_title = WebDriverWait(driver, 300).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h3.ipc-title__text")
            )
        )

        print("First movie title found:", first_title.text)
        input("Press Enter to close Chrome...")
    finally:
        driver.quit()


if __name__ == "__main__":
    open_imdb_page()
