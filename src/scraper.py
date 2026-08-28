"""Scrape structured IMDb 2024 movie data with Selenium."""

import re
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


GENRE = "Action"

IMDB_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2024-01-01,2024-12-31"
    "&genres=action"
)

TITLE_SELECTOR = ".ipc-title__text"
MOVIE_CARD_SELECTOR = "li.ipc-metadata-list-summary-item"


def clean_title(raw_title):
    """Remove ranking prefixes such as '1. Movie Name'."""
    return re.sub(r"^\d+\.\s*", "", raw_title).strip()


def convert_votes(raw_votes):
    """Convert IMDb vote text such as 591K or 1.2M into an integer."""
    if not raw_votes:
        return None

    value = raw_votes.strip().upper().replace(",", "")
    multiplier = 1

    if value.endswith("K"):
        multiplier = 1_000
        value = value[:-1]
    elif value.endswith("M"):
        multiplier = 1_000_000
        value = value[:-1]
    elif value.endswith("B"):
        multiplier = 1_000_000_000
        value = value[:-1]

    try:
        return int(float(value) * multiplier)
    except ValueError:
        return None


def convert_duration_to_minutes(raw_duration):
    """Convert IMDb duration text such as '2h 8m' into total minutes."""
    if not raw_duration:
        return None

    hours_match = re.search(r"(\d{1,2})h", raw_duration)
    minutes_match = re.search(r"(\d{1,3})m", raw_duration)

    hours = int(hours_match.group(1)) if hours_match else 0
    minutes = int(minutes_match.group(1)) if minutes_match else 0

    total_minutes = (hours * 60) + minutes
    return total_minutes if total_minutes else None


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
    print(f"Opening IMDb 2024 {GENRE} movies page...")

    try:
        driver.get(IMDB_URL)
    except TimeoutException:
        print("Initial page load timed out. Checking the browser...")

    time.sleep(3)

    print("Current URL:", driver.current_url)
    print("Page title:", driver.title or "[blank]")

    title_elements = find_movie_titles(driver, timeout=15)

    if title_elements:
        return True

    print("\nIMDb movie data is not visible yet.")
    print("If Chrome shows 'Human Verification', complete it manually.")
    print("Do NOT close Chrome.")
    input("After the normal IMDb movie list appears, press Enter here...")

    print("Checking IMDb again after verification...")
    time.sleep(2)

    return bool(find_movie_titles(driver, timeout=30))


def extract_title(card):
    """Extract and clean the movie title from one result card."""
    elements = card.find_elements(By.CSS_SELECTOR, TITLE_SELECTOR)

    if not elements:
        return None

    return clean_title(elements[0].text)


def extract_duration(card_text):
    """Extract runtime safely even when IMDb joins year and duration."""
    year_runtime_match = re.search(
        r"(?:19|20)\d{2}(\d{1,2}h(?:\s*\d{1,2}m)?|\d{1,3}m)",
        card_text,
    )

    if year_runtime_match:
        return year_runtime_match.group(1)

    runtime_match = re.search(
        r"(?<!\d)(\d{1,2}h(?:\s*\d{1,2}m)?|\d{1,3}m)(?!\d)",
        card_text,
    )

    return runtime_match.group(1) if runtime_match else None


def extract_rating(card_text):
    """Extract IMDb rating from the visible lines of a movie card."""
    for line in card_text.splitlines():
        value = line.strip()

        if re.fullmatch(r"(?:10(?:\.0)?|[0-9](?:\.[0-9])?)", value):
            number = float(value)

            if 0 <= number <= 10:
                return number

    return None


def extract_votes(card_text):
    """Extract vote text such as '(591K)' from a movie card."""
    match = re.search(r"\(([\d,.]+\s*[KMB]?)\)", card_text, re.IGNORECASE)

    if not match:
        return None

    return match.group(1).replace(" ", "")


def extract_movie_record(card, genre):
    """Convert one IMDb result card into a structured movie dictionary."""
    card_text = card.text

    movie_name = extract_title(card)
    duration_text = extract_duration(card_text)
    rating = extract_rating(card_text)
    votes_text = extract_votes(card_text)

    if not movie_name:
        return None

    return {
        "Movie Name": movie_name,
        "Genre": genre,
        "Ratings": rating,
        "Voting Counts": convert_votes(votes_text),
        "Duration": convert_duration_to_minutes(duration_text),
    }


def scrape_visible_movies(driver, genre):
    """Extract structured records from all currently visible IMDb cards."""
    cards = driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)
    movies = []

    for card in cards:
        record = extract_movie_record(card, genre)

        if record:
            movies.append(record)

    return movies


def print_first_record(movies):
    """Print the first structured movie record for validation."""
    print("\nFIRST STRUCTURED MOVIE RECORD")
    print("-" * 50)

    if not movies:
        print("No structured movie records were extracted.")
        print("-" * 50)
        return

    first_movie = movies[0]

    for key, value in first_movie.items():
        print(f"{key}: {value}")

    print("-" * 50)


def main():
    """Launch Chrome and extract visible IMDb 2024 Action movies."""
    driver = None

    try:
        print("Starting Chrome...")
        driver = create_driver()

        if not load_imdb(driver):
            print("\nIMDb movie data still could not be detected.")
            save_debug_files(driver)
            input("\nPress Enter to close Chrome...")
            return

        movies = scrape_visible_movies(driver, GENRE)

        print(f"\nStructured movie records extracted: {len(movies)}")
        print_first_record(movies)

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
