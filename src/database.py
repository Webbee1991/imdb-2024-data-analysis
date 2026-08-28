"""Load the cleaned IMDb 2026 dataset into MySQL."""

from getpass import getpass
from pathlib import Path

import pandas as pd
from sqlalchemy import BigInteger, Float, Integer, String, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


CSV_FILE = Path("data/cleaned/imdb_2026_movies.csv")
DATABASE_NAME = "imdb_2026"
TABLE_NAME = "imdb_movies"
MYSQL_SOCKET = "/tmp/mysql.sock"

REQUIRED_COLUMNS = [
    "Movie Name",
    "Genre",
    "Ratings",
    "Voting Counts",
    "Duration",
]

COLUMN_MAPPING = {
    "Movie Name": "movie_name",
    "Genre": "genre",
    "Ratings": "ratings",
    "Voting Counts": "voting_counts",
    "Duration": "duration",
}


def load_cleaned_csv():
    """Read and prepare the cleaned IMDb CSV for SQL storage."""
    if not CSV_FILE.exists():
        raise FileNotFoundError(
            f"{CSV_FILE} was not found. Run cleaner.py first."
        )

    dataframe = pd.read_csv(CSV_FILE)

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV is missing required columns: {missing_columns}"
        )

    dataframe = dataframe[REQUIRED_COLUMNS].rename(columns=COLUMN_MAPPING)

    dataframe["ratings"] = pd.to_numeric(
        dataframe["ratings"], errors="coerce"
    )
    dataframe["voting_counts"] = pd.to_numeric(
        dataframe["voting_counts"], errors="coerce"
    )
    dataframe["duration"] = pd.to_numeric(
        dataframe["duration"], errors="coerce"
    )

    return dataframe


def create_mysql_engine(password):
    """Create a SQLAlchemy connection to the local MySQL database."""
    connection_url = URL.create(
        drivername="mysql+pymysql",
        username="root",
        password=password,
        host="localhost",
        database=DATABASE_NAME,
    )

    return create_engine(
        connection_url,
        connect_args={"unix_socket": MYSQL_SOCKET},
        pool_pre_ping=True,
    )


def load_dataframe_to_mysql(dataframe, engine):
    """Replace the project table with the current cleaned movie dataset."""
    sql_types = {
        "movie_name": String(500),
        "genre": String(50),
        "ratings": Float(),
        "voting_counts": BigInteger(),
        "duration": Integer(),
    }

    dataframe.to_sql(
        TABLE_NAME,
        con=engine,
        if_exists="replace",
        index=False,
        dtype=sql_types,
        chunksize=1000,
    )


def verify_mysql_data(engine):
    """Verify the loaded row count and display five SQL records."""
    with engine.connect() as connection:
        row_count = connection.execute(
            text(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        ).scalar()

        sample = pd.read_sql(
            text(
                f"SELECT movie_name, genre, ratings, "
                f"voting_counts, duration "
                f"FROM {TABLE_NAME} LIMIT 5"
            ),
            connection,
        )

    print(f"\nRows stored in MySQL: {row_count}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Table: {TABLE_NAME}")
    print("\nFirst 5 SQL rows:")
    print(sample.to_string(index=False))


def main():
    """Load the cleaned IMDb dataset into the project MySQL database."""
    try:
        dataframe = load_cleaned_csv()
        print(f"Cleaned CSV rows ready for SQL: {len(dataframe)}")

        password = getpass("MySQL root password: ")
        engine = create_mysql_engine(password)

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("Connected to MySQL successfully.")
        print(f"Loading data into {DATABASE_NAME}.{TABLE_NAME}...")

        load_dataframe_to_mysql(dataframe, engine)
        verify_mysql_data(engine)

        print("\nIMDb 2026 dataset loaded into MySQL successfully.")

    except (FileNotFoundError, ValueError) as error:
        print(f"\nData error: {error}")
    except SQLAlchemyError as error:
        print("\nMySQL/SQLAlchemy error:")
        print(error)


if __name__ == "__main__":
    main()
