"""Streamlit dashboard for the IMDb 2026 GUVI project."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.analysis import run_analysis
from src.database import create_mysql_engine


st.set_page_config(
    page_title="IMDb 2026 Data Analysis",
    page_icon="🎬",
    layout="wide",
)


@st.cache_resource(show_spinner=False)
def get_engine(password):
    """Create and cache the local MySQL engine for the Streamlit session."""
    return create_mysql_engine(password)


@st.cache_data(show_spinner=False)
def load_movies(_engine):
    """Load the complete SQL movie table for interactive filtering."""
    query = text(
        """
        SELECT
            movie_name,
            genre,
            ratings,
            voting_counts,
            duration
        FROM imdb_movies
        ORDER BY movie_name, genre
        """
    )

    with _engine.connect() as connection:
        return pd.read_sql(query, connection)


@st.cache_data(show_spinner=False)
def load_analysis(_engine, analysis_name):
    """Load one validated GUVI SQL analysis."""
    return run_analysis(_engine, analysis_name)


def show_overview_metrics(movies):
    """Display compact summary statistics for the movie dataset."""
    unique_movies = movies.drop_duplicates(subset="movie_name")
    rated_movies = unique_movies.dropna(subset=["ratings"])

    average_rating = rated_movies["ratings"].mean()
    average_rating_text = (
        f"{average_rating:.2f}" if pd.notna(average_rating) else "N/A"
    )

    first, second, third, fourth = st.columns(4)
    first.metric("Unique Movies", f"{unique_movies['movie_name'].nunique():,}")
    second.metric("Genres", f"{movies['genre'].nunique():,}")
    third.metric("Movies with Ratings", f"{len(rated_movies):,}")
    fourth.metric("Average Rating", average_rating_text)


def show_top_movies(engine):
    """Show the top 10 movies by rating and voting count."""
    st.subheader("1. Top 10 Movies by Rating and Voting Counts")
    dataframe = load_analysis(engine, "top_10_movies")
    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def show_genre_distribution(engine):
    """Show movie counts by genre as a bar chart."""
    st.subheader("2. Genre Distribution")
    dataframe = load_analysis(engine, "genre_distribution")

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(dataframe["genre"], dataframe["movie_count"])
    axis.set_xlabel("Genre")
    axis.set_ylabel("Number of Movies")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_average_duration(engine):
    """Show average movie duration for each genre."""
    st.subheader("3. Average Duration by Genre")
    dataframe = load_analysis(engine, "average_duration_by_genre")

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(
        dataframe["genre"],
        dataframe["average_duration_minutes"],
    )
    axis.set_xlabel("Average Duration (Minutes)")
    axis.set_ylabel("Genre")
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_average_votes(engine):
    """Show average voting count by genre."""
    st.subheader("4. Voting Trends by Genre")
    dataframe = load_analysis(engine, "average_votes_by_genre")

    figure, axis = plt.subplots(figsize=(10, 5))
    axis.bar(dataframe["genre"], dataframe["average_voting_count"])
    axis.set_xlabel("Genre")
    axis.set_ylabel("Average Voting Count")
    axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_rating_distribution(engine):
    """Show the distribution of IMDb ratings."""
    st.subheader("5. Rating Distribution")
    dataframe = load_analysis(engine, "rating_distribution")

    figure, axis = plt.subplots(figsize=(10, 5))
    sns.histplot(data=dataframe, x="ratings", bins=20, ax=axis)
    axis.set_xlabel("IMDb Rating")
    axis.set_ylabel("Number of Movie-Genre Records")
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_top_movie_per_genre(engine):
    """Show the highest-rated movie for each genre."""
    st.subheader("6. Top-Rated Movie per Genre")
    dataframe = load_analysis(engine, "top_rated_movie_per_genre")
    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def show_total_votes(engine):
    """Show total voting count by genre as a pie chart."""
    st.subheader("7. Most Popular Genres by Total Votes")
    dataframe = load_analysis(engine, "total_votes_by_genre")

    figure, axis = plt.subplots(figsize=(8, 8))
    axis.pie(
        dataframe["total_voting_count"],
        labels=dataframe["genre"],
        autopct="%1.1f%%",
    )
    axis.set_title("Share of Total IMDb Votes by Genre")
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_duration_extremes(engine):
    """Show the shortest and longest movie records."""
    st.subheader("8. Duration Extremes")
    dataframe = load_analysis(engine, "duration_extremes")
    st.dataframe(dataframe, use_container_width=True, hide_index=True)


def show_rating_heatmap(engine):
    """Show average IMDb rating by genre as a heatmap."""
    st.subheader("9. Average Ratings by Genre")
    dataframe = load_analysis(engine, "average_rating_by_genre")

    heatmap_data = dataframe.set_index("genre")[["average_rating"]].T

    figure, axis = plt.subplots(figsize=(12, 3))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt=".2f",
        cbar=True,
        ax=axis,
    )
    axis.set_xlabel("Genre")
    axis.set_ylabel("")
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def show_ratings_votes_relationship(engine):
    """Show the relationship between ratings and voting counts."""
    st.subheader("10. Ratings vs Voting Counts")
    dataframe = load_analysis(engine, "ratings_votes_correlation")

    correlation = dataframe["ratings"].corr(dataframe["voting_counts"])
    correlation_text = (
        f"{correlation:.3f}" if pd.notna(correlation) else "N/A"
    )
    st.metric("Pearson Correlation", correlation_text)

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.scatter(dataframe["ratings"], dataframe["voting_counts"], alpha=0.5)
    axis.set_xlabel("IMDb Rating")
    axis.set_ylabel("Voting Count")
    figure.tight_layout()
    st.pyplot(figure)
    plt.close(figure)


def apply_interactive_filters(movies):
    """Apply the GUVI duration, rating, vote, and genre filters."""
    st.subheader("Interactive Movie Filters")

    genres = ["All"] + sorted(movies["genre"].dropna().unique().tolist())

    first, second = st.columns(2)

    with first:
        duration_filter = st.selectbox(
            "Duration",
            [
                "All Durations",
                "Under 2 Hours",
                "2 to 3 Hours",
                "Over 3 Hours",
            ],
        )
        genre_filter = st.selectbox("Genre", genres)

    with second:
        minimum_rating = st.slider(
            "Minimum Rating",
            min_value=0.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
        )
        minimum_votes = st.selectbox(
            "Minimum Voting Count",
            [0, 1000, 10000, 50000, 100000],
            format_func=lambda value: f"{value:,}+ votes",
        )

    filtered = movies.copy()

    if genre_filter != "All":
        filtered = filtered[filtered["genre"] == genre_filter]

    if duration_filter == "Under 2 Hours":
        filtered = filtered[filtered["duration"] < 120]
    elif duration_filter == "2 to 3 Hours":
        filtered = filtered[
            filtered["duration"].between(120, 180, inclusive="both")
        ]
    elif duration_filter == "Over 3 Hours":
        filtered = filtered[filtered["duration"] > 180]

    if minimum_rating > 0:
        filtered = filtered[filtered["ratings"] >= minimum_rating]

    if minimum_votes > 0:
        filtered = filtered[filtered["voting_counts"] >= minimum_votes]

    st.write(f"Matching movie-genre records: **{len(filtered):,}**")

    display_data = filtered.rename(
        columns={
            "movie_name": "Movie Name",
            "genre": "Genre",
            "ratings": "Ratings",
            "voting_counts": "Voting Counts",
            "duration": "Duration",
        }
    )

    st.dataframe(
        display_data,
        use_container_width=True,
        hide_index=True,
    )


def main():
    """Run the IMDb 2026 Streamlit dashboard."""
    st.title("IMDb 2026 Data Scraping and Visualization Dashboard")
    st.caption(
        "Selenium + Pandas + MySQL + Streamlit | GUVI Project"
    )

    st.sidebar.header("MySQL Connection")
    password = st.sidebar.text_input(
        "MySQL root password",
        type="password",
        help="Used only to connect to your local MySQL database.",
    )

    if not password:
        st.info("Enter your MySQL root password in the sidebar to continue.")
        st.stop()

    try:
        engine = get_engine(password)

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        movies = load_movies(engine)

    except SQLAlchemyError as error:
        st.error("Could not connect to the IMDb MySQL database.")
        st.code(str(error))
        st.stop()

    show_overview_metrics(movies)

    insights_tab, filters_tab = st.tabs(
        ["Analysis & Visualizations", "Interactive Filters"]
    )

    with insights_tab:
        show_top_movies(engine)
        show_genre_distribution(engine)
        show_average_duration(engine)
        show_average_votes(engine)
        show_rating_distribution(engine)
        show_top_movie_per_genre(engine)
        show_total_votes(engine)
        show_duration_extremes(engine)
        show_rating_heatmap(engine)
        show_ratings_votes_relationship(engine)

    with filters_tab:
        apply_interactive_filters(movies)


if __name__ == "__main__":
    main()
