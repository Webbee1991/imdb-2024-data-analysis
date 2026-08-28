"""Merge and clean genre-wise IMDb 2024 CSV files."""

from pathlib import Path

import pandas as pd


GENRE_DIR = Path("data/genre")
CLEANED_DIR = Path("data/cleaned")

GENRE_OUTPUT = CLEANED_DIR / "imdb_2024_movies_genre.csv"
MASTER_OUTPUT = CLEANED_DIR / "imdb_2024_movies.csv"

REQUIRED_COLUMNS = [
    "IMDb ID",
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


def clean_combined_data(dataframe):
    """Standardize fields and remove duplicate IMDb-ID/genre rows."""
    cleaned = dataframe.copy()

    cleaned["IMDb ID"] = cleaned["IMDb ID"].astype("string").str.strip()
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

    cleaned = cleaned.dropna(subset=["IMDb ID", "Movie Name", "Genre"])
    cleaned = cleaned[
        (cleaned["IMDb ID"] != "")
        & (cleaned["Movie Name"] != "")
        & (cleaned["Genre"] != "")
    ]

    cleaned = cleaned.drop_duplicates(
        subset=["IMDb ID", "Genre"], keep="first"
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

    return cleaned


def first_valid(series):
    """Return the first non-null value from a Pandas Series."""
    valid_values = series.dropna()

    if valid_values.empty:
        return pd.NA

    return valid_values.iloc[0]


def combine_genres(series):
    """Combine a movie's genres into one comma-separated string."""
    genres = sorted({str(value).strip() for value in series.dropna()})
    return ", ".join(genres)


def build_master_data(genre_dataframe):
    """Create one unique row per IMDb ID for overall analysis and SQL."""
    master = (
        genre_dataframe.groupby("IMDb ID", as_index=False)
        .agg(
            {
                "Movie Name": first_valid,
                "Genre": combine_genres,
                "Ratings": first_valid,
                "Voting Counts": "max",
                "Duration": first_valid,
            }
        )
    )

    master = master.sort_values(
        by=["Ratings", "Voting Counts"],
        ascending=[False, False],
        na_position="last",
        kind="stable",
    ).reset_index(drop=True)

    return master[REQUIRED_COLUMNS]


def save_cleaned_files(genre_dataframe, master_dataframe):
    """Save genre-level and unique movie-level cleaned datasets."""
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    genre_dataframe.to_csv(GENRE_OUTPUT, index=False)
    master_dataframe.to_csv(MASTER_OUTPUT, index=False)

    print(f"\nSaved genre-level dataset: {GENRE_OUTPUT}")
    print(f"Rows: {len(genre_dataframe)}")

    print(f"\nSaved unique movie dataset: {MASTER_OUTPUT}")
    print(f"Unique movies: {len(master_dataframe)}")


def print_data_quality(master_dataframe):
    """Print basic data-quality information for the master dataset."""
    print("\nDATA QUALITY CHECK")
    print("-" * 45)
    print(f"Missing IMDb IDs: {master_dataframe['IMDb ID'].isna().sum()}")
    print(f"Missing ratings: {master_dataframe['Ratings'].isna().sum()}")
    print(
        "Missing voting counts: "
        f"{master_dataframe['Voting Counts'].isna().sum()}"
    )
    print(f"Missing durations: {master_dataframe['Duration'].isna().sum()}")

    print("\nTop 5 movies by rating:")
    print(master_dataframe.head().to_string(index=False))


def main():
    """Merge genre CSVs, clean the data, and build project datasets."""
    print("Loading genre CSV files...")
    combined = load_genre_csvs()

    print(f"\nRows before cleaning: {len(combined)}")

    genre_data = clean_combined_data(combined)
    print(f"Rows after movie-genre de-duplication: {len(genre_data)}")

    master_data = build_master_data(genre_data)

    save_cleaned_files(genre_data, master_data)
    print_data_quality(master_data)


if __name__ == "__main__":
    main()
