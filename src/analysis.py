"""Run the SQL analyses required for the IMDb 2026 GUVI project."""

from getpass import getpass

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

try:
    from .database import create_mysql_engine
except ImportError:
    from database import create_mysql_engine


QUERIES = {
    "top_10_movies": """
        SELECT
            movie_name,
            GROUP_CONCAT(
                DISTINCT genre
                ORDER BY genre
                SEPARATOR ', '
            ) AS genres,
            MAX(ratings) AS ratings,
            MAX(voting_counts) AS voting_counts
        FROM imdb_movies
        WHERE ratings IS NOT NULL
          AND voting_counts IS NOT NULL
        GROUP BY movie_name
        ORDER BY ratings DESC, voting_counts DESC
        LIMIT 10
    """,
    "genre_distribution": """
        SELECT
            genre,
            COUNT(DISTINCT movie_name) AS movie_count
        FROM imdb_movies
        GROUP BY genre
        ORDER BY movie_count DESC
    """,
    "average_duration_by_genre": """
        SELECT
            genre,
            ROUND(AVG(duration), 2) AS average_duration_minutes
        FROM imdb_movies
        WHERE duration IS NOT NULL
        GROUP BY genre
        ORDER BY average_duration_minutes DESC
    """,
    "average_votes_by_genre": """
        SELECT
            genre,
            ROUND(AVG(voting_counts), 2) AS average_voting_count
        FROM imdb_movies
        WHERE voting_counts IS NOT NULL
        GROUP BY genre
        ORDER BY average_voting_count DESC
    """,
    "rating_distribution": """
        SELECT
            ratings
        FROM imdb_movies
        WHERE ratings IS NOT NULL
    """,
    "top_rated_movie_per_genre": """
        SELECT
            genre,
            SUBSTRING_INDEX(
                GROUP_CONCAT(
                    movie_name
                    ORDER BY ratings DESC, voting_counts DESC
                    SEPARATOR '||'
                ),
                '||',
                1
            ) AS movie_name,
            MAX(ratings) AS ratings
        FROM imdb_movies
        WHERE ratings IS NOT NULL
        GROUP BY genre
        ORDER BY genre
    """,
    "total_votes_by_genre": """
        SELECT
            genre,
            SUM(voting_counts) AS total_voting_count
        FROM imdb_movies
        WHERE voting_counts IS NOT NULL
        GROUP BY genre
        ORDER BY total_voting_count DESC
    """,
    "duration_extremes": """
        (
            SELECT
                'Shortest' AS duration_type,
                movie_name,
                genre,
                duration
            FROM imdb_movies
            WHERE duration IS NOT NULL
            ORDER BY duration ASC, movie_name ASC
            LIMIT 1
        )
        UNION ALL
        (
            SELECT
                'Longest' AS duration_type,
                movie_name,
                genre,
                duration
            FROM imdb_movies
            WHERE duration IS NOT NULL
            ORDER BY duration DESC, movie_name ASC
            LIMIT 1
        )
    """,
    "average_rating_by_genre": """
        SELECT
            genre,
            ROUND(AVG(ratings), 2) AS average_rating
        FROM imdb_movies
        WHERE ratings IS NOT NULL
        GROUP BY genre
        ORDER BY average_rating DESC
    """,
    "ratings_votes_correlation": """
        SELECT
            movie_name,
            MAX(ratings) AS ratings,
            MAX(voting_counts) AS voting_counts
        FROM imdb_movies
        WHERE ratings IS NOT NULL
          AND voting_counts IS NOT NULL
        GROUP BY movie_name
        ORDER BY movie_name
    """,
}


ANALYSIS_TITLES = {
    "top_10_movies": "1. Top 10 Movies by Rating and Voting Counts",
    "genre_distribution": "2. Genre Distribution",
    "average_duration_by_genre": "3. Average Duration by Genre",
    "average_votes_by_genre": "4. Voting Trends by Genre",
    "rating_distribution": "5. Rating Distribution",
    "top_rated_movie_per_genre": "6. Top-Rated Movie per Genre",
    "total_votes_by_genre": "7. Most Popular Genres by Total Votes",
    "duration_extremes": "8. Duration Extremes",
    "average_rating_by_genre": "9. Average Ratings by Genre",
    "ratings_votes_correlation": "10. Ratings vs Voting Counts",
}


def run_analysis(engine, analysis_name):
    """Run one named SQL analysis and return the result as a DataFrame."""
    if analysis_name not in QUERIES:
        raise ValueError(f"Unknown analysis: {analysis_name}")

    with engine.connect() as connection:
        return pd.read_sql(text(QUERIES[analysis_name]), connection)


def print_analysis_result(analysis_name, dataframe):
    """Print one analysis result in a compact form for testing."""
    print("\n" + "=" * 70)
    print(ANALYSIS_TITLES[analysis_name])
    print("=" * 70)

    if analysis_name == "rating_distribution":
        print(f"Ratings available for analysis: {len(dataframe)}")
        print(dataframe["ratings"].describe().round(2).to_string())
        return

    if analysis_name == "ratings_votes_correlation":
        print(f"Movies available for scatter plot: {len(dataframe)}")
        print("\nSample rows:")
        print(dataframe.head(10).to_string(index=False))
        return

    print(dataframe.to_string(index=False))


def main():
    """Connect to MySQL and test all GUVI-required SQL analyses."""
    try:
        password = getpass("MySQL root password: ")
        engine = create_mysql_engine(password)

        for analysis_name in QUERIES:
            result = run_analysis(engine, analysis_name)
            print_analysis_result(analysis_name, result)

        print("\nAll 10 GUVI SQL analyses completed successfully.")

    except ValueError as error:
        print(f"\nAnalysis error: {error}")
    except SQLAlchemyError as error:
        print("\nMySQL/SQLAlchemy error:")
        print(error)


if __name__ == "__main__":
    main()
