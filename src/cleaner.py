"""Merge and clean genre-wise IMDb 2026 CSV files."""

from pathlib import Path

import pandas as pd


GENRE_DIR = Path("data/genre")
CLEANED_DIR = Path("data/cleaned")
OUTPUT_FILE = CLEANED_DIR / "imdb_2026_movies.csv"

REQUIRED_COLUMNS = [
    "Movie Name",
    "Genre",
    "Ratings",
    "Voting Counts",
    "Duration",
]


def load_genre_csvs():
    """Read every genre CSV and combine them into one DataFrame."""
    csv_files = sorted(GENRE_DIR.glob("*_movies.csv"))

    if not csv_files:
        raise FileNotFoundError(
            "No genre CSV files found in data/genre. Run scraper.py first."
        )

    frames = []

    for csv_file in csv_files:
        dataframe = pd.read_csv(csv_file)

        missing_columns = [
            column for column in REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            print(
                f"Skipping {csv_file.name}: "
                f"missing columns {missing_columns}"
            )
            continue

        frames.append(dataframe[REQUIRED_COLUMNS])
        print(f"Loaded {csv_file.name}: {len(dataframe)} rows")

    if not frames:
        raise ValueError("No valid genre CSV files could be loaded.")

    return pd.concat(frames, ignore_index=True)


def clean_data(dataframe):
    """Clean the combined IMDb dataset and validate required fields."""
    cleaned = dataframe.copy()

    cleaned["Movie Name"] = cleaned["Movie Name"].astype("string").str.strip()
    cleaned["Genre"] = cleaned["Genre"].astype("string").str.strip()

    cleaned["Ratings"] = pd.to_numeric(
        cleaned["Ratings"], errors="coerce"
    )
    cleaned["Voting Counts"] = pd.to_numeric(
        cleaned["Voting Counts"], errors="coerce"
    )
    cleaned["Duration"] = pd.to_numeric(
        cleaned["Duration"], errors="coerce"
    )

    cleaned = cleaned.dropna(subset=["Movie Name", "Genre"])
    cleaned = cleaned[
        (cleaned["Movie Name"] != "") & (cleaned["Genre"] != "")
    ]

    cleaned = cleaned.drop_duplicates(
        subset=["Movie Name", "Genre"], keep="first"
    )

    cleaned = cleaned[
        cleaned["Ratings"].isna()
        | cleaned["Ratings"].between(0, 10)
    ]
    cleaned = cleaned[
        cleaned["Voting Counts"].isna()
        | (cleaned["Voting Counts"] >= 0)
    ]
    cleaned = cleaned[
        cleaned["Duration"].isna()
        | cleaned["Duration"].between(1, 600)
    ]

    cleaned = cleaned.sort_values(
        by=["Genre", "Movie Name"],
        kind="stable",
    ).reset_index(drop=True)

    return cleaned[REQUIRED_COLUMNS]


def save_cleaned_data(dataframe):
    """Save the single combined dataset required by the project."""
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved combined dataset: {OUTPUT_FILE}")
    print(f"Rows: {len(dataframe)}")


def print_data_quality(dataframe):
    """Print basic validation information for the cleaned dataset."""
    print("\nDATA QUALITY CHECK")
    print("-" * 45)
    print(f"Missing ratings: {dataframe['Ratings'].isna().sum()}")
    print(
        "Missing voting counts: "
        f"{dataframe['Voting Counts'].isna().sum()}"
    )
    print(f"Missing durations: {dataframe['Duration'].isna().sum()}")
    print(
        "Duplicate movie-genre rows: "
        f"{dataframe.duplicated(['Movie Name', 'Genre']).sum()}"
    )

    print("\nFirst 5 cleaned rows:")
    print(dataframe.head().to_string(index=False))


def main():
    """Merge genre CSVs, clean the data, and save one combined dataset."""
    print("Loading genre CSV files...")
    combined = load_genre_csvs()

    print(f"\nRows before cleaning: {len(combined)}")

    cleaned = clean_data(combined)
    print(f"Rows after cleaning: {len(cleaned)}")

    save_cleaned_data(cleaned)
    print_data_quality(cleaned)


if __name__ == "__main__":
    main()
