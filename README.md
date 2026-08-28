# IMDb 2026 Data Scraping and Visualizations

This project implements the GUVI IMDb data-scraping and visualization assignment using current 2026 IMDb feature-film data while preserving the original project workflow and requirements.

The application scrapes IMDb movie data with Selenium, stores genre-wise CSV files, combines and cleans the data with Pandas, loads the final dataset into MySQL, runs SQL-based analysis, and presents the results in an interactive Streamlit dashboard.

## Project Scope

The dataset contains the five required fields:

- Movie Name
- Genre
- Ratings
- Voting Counts
- Duration

The scraper currently uses IMDb feature-film results from **2026-01-01 through 2026-08-28**.

## Technologies Used

- Python
- Selenium
- Pandas
- MySQL
- SQLAlchemy
- PyMySQL
- Streamlit
- Matplotlib
- Seaborn

## Project Workflow

```text
IMDb
  |
  v
Selenium Scraping
  |
  v
Genre-wise CSV Files
  |
  v
Pandas Cleaning and Merge
  |
  v
Combined Cleaned CSV
  |
  v
MySQL Database
  |
  v
SQL Analysis
  |
  v
Streamlit Dashboard and Interactive Filters
```

## Project Structure

```text
imdb-2024-data-analysis/
├── data/
│   ├── raw/
│   ├── genre/
│   └── cleaned/
├── src/
│   ├── scraper.py
│   ├── cleaner.py
│   ├── database.py
│   └── analysis.py
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Data Collection

`src/scraper.py` uses Selenium to open IMDb search results for each genre and extracts:

- Movie Name
- Genre
- Ratings
- Voting Counts
- Duration

The scraper uses IMDb's **Load More** functionality to retrieve the available movie records for each selected genre. If IMDb displays human verification, complete it manually and continue the script. The project does not attempt to bypass verification.

Genre-wise output files are written to:

```text
data/genre/
```

## Data Cleaning

Run:

```bash
python src/cleaner.py
```

The cleaning stage:

- combines the genre-wise CSV files,
- validates the five required columns,
- converts ratings, voting counts, and duration to numeric values,
- removes invalid blank movie/genre rows,
- removes duplicate Movie Name + Genre records,
- validates rating and duration ranges,
- retains legitimate missing IMDb values for later analysis.

The final cleaned dataset is stored as:

```text
data/cleaned/imdb_2026_movies.csv
```

A movie can appear in multiple genre rows because IMDb titles may belong to multiple genres. Overall movie-level analyses therefore group by movie name where required, while genre analyses use the genre-wise rows.

## MySQL Database

The project uses:

```text
Database: imdb_2026
Table: imdb_movies
```

SQL column names are normalized to:

```text
movie_name
 genre
 ratings
 voting_counts
 duration
```

Missing numeric IMDb values are stored as SQL `NULL` values.

Create the database before loading the dataset:

```sql
CREATE DATABASE imdb_2026;
```

Then run:

```bash
python src/database.py
```

The script securely asks for the local MySQL root password at runtime. The password is not stored in the repository.

## SQL Analysis

Run:

```bash
python src/analysis.py
```

The project implements the required analyses:

1. Top 10 Movies by Rating and Voting Counts
2. Genre Distribution
3. Average Duration by Genre
4. Average Voting Count by Genre
5. Rating Distribution
6. Top-Rated Movie per Genre
7. Most Popular Genres by Total Votes
8. Shortest and Longest Movies
9. Average Rating by Genre
10. Ratings vs Voting Counts Correlation

Movie-level ranking and correlation queries group duplicate genre rows by movie name so that the same title is not counted repeatedly in overall movie-level results.

## Streamlit Dashboard

Start the application with:

```bash
streamlit run app.py
```

Enter the local MySQL password in the Streamlit sidebar to connect to the database.

The dashboard contains two main sections:

### Analysis & Visualizations

- Top 10 movie table
- Genre distribution bar chart
- Average duration by genre horizontal bar chart
- Average voting count by genre chart
- Rating distribution histogram
- Top-rated movie per genre table
- Total votes by genre pie chart
- Duration extremes table
- Average rating by genre heatmap
- Ratings vs voting-count scatter plot with Pearson correlation

### Interactive Filters

Users can dynamically filter the movie dataset by:

- Duration: Under 2 Hours, 2 to 3 Hours, Over 3 Hours
- Minimum Rating
- Minimum Voting Count
- Genre
- Combined filter conditions

The filtered result is displayed as an interactive DataFrame.

## Installation and Execution

Clone the repository and move into the project folder:

```bash
git clone https://github.com/Webbee1991/imdb-2024-data-analysis.git
cd imdb-2024-data-analysis
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Execute the project in this order:

```bash
python src/scraper.py
python src/cleaner.py
python src/database.py
python src/analysis.py
streamlit run app.py
```

Before running `database.py`, ensure the local MySQL server is running and the `imdb_2026` database exists.

## Data Validation Notes

Some recent or less-known IMDb titles do not yet have ratings, vote counts, or runtime information. These legitimate missing values are retained instead of deleting the movie record. SQL aggregate functions naturally ignore `NULL` values where appropriate, while analyses requiring ratings or voting counts explicitly filter out missing records.

## Deliverables

- Selenium scraping script
- Genre-wise CSV output
- Combined cleaned dataset
- MySQL movie database
- SQL analysis script
- Streamlit visualizations
- Interactive filtering application
- Public GitHub repository
- Project documentation and execution instructions

## Submission Demo Flow

For the project demonstration:

1. Briefly explain the problem statement and five scraped fields.
2. Show `scraper.py` and the genre-wise CSV output.
3. Show the cleaned combined CSV.
4. Show the `imdb_2026.imdb_movies` MySQL table and one analysis query.
5. Run `src/analysis.py` and explain the SQL insights.
6. Launch the Streamlit dashboard.
7. Demonstrate two or three visualizations.
8. Demonstrate combined filters such as Action + rating 8+ + votes 10,000+ + duration under 2 hours.
9. End by explaining the complete Selenium → Pandas → MySQL → Streamlit workflow.

## Note on Project Year

The original GUVI assignment was framed around IMDb 2024 data. This implementation applies the same required architecture, fields, analyses, visualizations, and interactive-filter workflow to current 2026 IMDb data.
