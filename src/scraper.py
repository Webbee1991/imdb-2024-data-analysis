"""Scrape IMDb 2026 movie data genre by genre with Selenium."""

import re
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


GENRES = {
    "Action": "action",
    "Adventure": "adventure",
    "Animation": "animation",
    "Comedy": "comedy",
    "Crime": "crime",
    "Drama": "drama",
    "Fantasy": "fantasy",
    "Horror": "horror",
    "Mystery": "mystery",
    "Romance": "romance",
    "Sci-Fi": "sci-fi",
    "Thriller": "thriller",
}

BASE_URL = (
    "https://www.imdb.com/search/title/"
    "?title_type=feature&release_date=2026-01-01,2026-08-28"
)

TITLE_SELECTOR = ".ipc-title__text"
MOVIE_CARD_SELECTOR = "li.ipc-metadata-list-summary-item"
LOAD_MORE_SELECTOR = "button.ipc-see-more__button"

REQUIRED_COLUMNS = [
    "Movie Name",
    "Genre",
    "Ratings",
    "Voting Counts",
    "Duration",
]


def build_genre_url(genre_slug):
    """Build the IMDb 2026 search URL for one genre."""
    return f"{BASE_URL}&genres={genre_slug}"


def clean_title(raw_title):
    """Remove ranking prefixes such as '1. Movie Name'."""
    return re.sub(r"^\d+\.\s*", "", raw_title).strip()


def convert_votes(raw_votes):
    """Convert vote text such as 591K or 1.2M into an integer."""
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


def save_debug_files(driver, genre):
    """Save the current page when IMDb does not load as expected."""
    debug_dir = Path("data/raw")
    debug_dir.mkdir(parents=True, exist_ok=True)

    safe_genre = genre.lower().replace(" ", "_").replace("-", "_")
    screenshot_path = debug_dir / f"imdb_{safe_genre}_debug.png"
    html_path = debug_dir / f"imdb_{safe_genre}_debug.html"

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


def load_genre_page(driver, genre, genre_slug):
    """Open one IMDb genre page and handle human verification if needed."""
    url = build_genre_url(genre_slug)
    print(f"\nOpening IMDb 2026 {genre} movies...")

    try:
        driver.get(url)
    except TimeoutException:
        print("Page load timed out. Checking available content...")

    time.sleep(3)

    if find_movie_titles(driver, timeout=15):
        return True

    print(f"IMDb data for {genre} is not visible yet.")
    print("If Chrome shows Human Verification, complete it manually.")
    print("Do NOT close Chrome.")
    input("After the movie list appears, press Enter here...")

    time.sleep(2)
    return bool(find_movie_titles(driver, timeout=30))


def find_load_more_button(driver):
    """Return IMDb's visible Load More button when available."""
    buttons = driver.find_elements(By.CSS_SELECTOR, LOAD_MORE_SELECTOR)

    for button in reversed(buttons):
        try:
            if button.is_displayed() and "more" in button.text.lower():
                return button
        except WebDriverException:
            continue

    return None


def load_all_movies(driver, genre):
    """Keep loading IMDb results until no more movie cards are available."""
    while True:
        button = find_load_more_button(driver)

        if button is None:
            break

        previous_count = len(
            driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)
        )
        print(f"{genre}: {previous_count} cards loaded. Loading more...")

        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                button,
            )
            time.sleep(1)

            try:
                button.click()
            except WebDriverException:
                driver.execute_script("arguments[0].click();", button)

            WebDriverWait(driver, 25).until(
                lambda current_driver: len(
                    current_driver.find_elements(
                        By.CSS_SELECTOR,
                        MOVIE_CARD_SELECTOR,
                    )
                )
                > previous_count
            )
        except TimeoutException:
            print(f"{genre}: no additional movie cards were loaded.")
            break
        except WebDriverException as error:
            print(f"{genre}: could not load more movies: {error}")
            break

    final_count = len(
        driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)
    )
    print(f"{genre}: {final_count} movie cards available for scraping.")


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
    """Convert one IMDb result card into the required project fields."""
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


def scrape_movies(driver, genre):
    """Extract the required fields from all loaded IMDb movie cards."""
    cards = driver.find_elements(By.CSS_SELECTOR, MOVIE_CARD_SELECTOR)
    movies = []

    for card in cards:
        record = extract_movie_record(card, genre)

        if record:
            movies.append(record)

    return movies


def save_movies_to_csv(movies, genre):
    """Save one genre-specific CSV with the required project columns."""
    output_dir = Path("data/genre")
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_genre = genre.lower().replace(" ", "_").replace("-", "_")
    output_path = output_dir / f"{safe_genre}_movies.csv"

    dataframe = pd.DataFrame(movies, columns=REQUIRED_COLUMNS)
    dataframe.to_csv(output_path, index=False)

    print(f"Saved {len(dataframe)} rows -> {output_path}")
    return len(dataframe)


def scrape_all_genres(driver):
    """Scrape each configured genre and save one CSV per genre."""
    summary = []

    for genre, genre_slug in GENRES.items():
        loaded = load_genre_page(driver, genre, genre_slug)

        if not loaded:
            print(f"Could not load {genre}. Skipping this genre.")
            save_debug_files(driver, genre)
            summary.append((genre, 0))
            continue

        load_all_movies(driver, genre)
        movies = scrape_movies(driver, genre)
        row_count = save_movies_to_csv(movies, genre) if movies else 0
        summary.append((genre, row_count))

    return summary


def print_summary(summary):
    """Print a summary of all generated genre CSV files."""
    print("\nGENRE SCRAPING SUMMARY")
    print("-" * 40)

    total_rows = 0

    for genre, row_count in summary:
        print(f"{genre}: {row_count} rows")
        total_rows += row_count

    print("-" * 40)
    print(f"Total rows across genre CSVs: {total_rows}")


def main():
    """Launch Chrome, scrape IMDb genres, and save genre CSV files."""
    driver = None

    try:
        print("Starting Chrome...")
        driver = create_driver()

        summary = scrape_all_genres(driver)
        print_summary(summary)

        input("\nPress Enter to close Chrome...")

    except WebDriverException as error:
        print("\nSelenium/Chrome error")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        if driver is not None:
            save_debug_files(driver, "general")

        input("\nPress Enter to close Chrome...")

    except Exception as error:
        print("\nUnexpected error")
        print("Error type:", type(error).__name__)
        print("Error details:", repr(error))

        if driver is not None:
            save_debug_files(driver, "general")

        input("\nPress Enter to close Chrome...")

    finally:
        if driver is not None:
            driver.quit()
            print("Chrome closed.")


if __name__ == "__main__":
    main()
