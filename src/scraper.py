"""Open the IMDb 2024 movies page with Selenium."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
)


def open_imdb_page():
    """Launch Chrome, open IMDb 2024 movies, and display the page title."""
    options = Options()
    options.add_argument("--start-maximized")

    print("Starting Chrome...")
    driver = webdriver.Chrome(options=options)

    print("Opening IMDb 2024 movies page...")
    driver.get(IMDB_URL)

    print("Page title:", driver.title)

    input("Press Enter to close Chrome...")
    driver.quit()


if __name__ == "__main__":
    open_imdb_page()
