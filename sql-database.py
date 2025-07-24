# Import libraries
import pandas as pd
import sqlalchemy as sqla
import kagglehub
import os
import matplotlib.pyplot as plt
import seaborn as sns
from dotenv import load_dotenv

#Connect to .env
load_dotenv()
def get_uri_from_env():
    user = os.getenv("MYSQL_USER")  
    password = os.getenv("MYSQL_PASSWORD")
    host = os.getenv("MYSQL_HOST")
    port = os.getenv("MYSQL_PORT")
    db = os.getenv("MYSQL_DB")
    return f'mysql+pymysql://{user}:{password}@{host}:{port}/{db}'

uri = get_uri_from_env()
engine = sqla.create_engine(uri)

# Download the dataset

path = kagglehub.dataset_download("davidcariboo/player-scores")

# Load each CSV file into a pandas DataFrame and then writes it into the database, 
# creating or replacing tables with the same names as the CSV files.

tables = [
    'appearances',
    'clubs',
    'competitions',
    'players',
    ]

for table in tables:
    df = pd.read_csv(f"{path}/{table}.csv")
    df.to_sql(table, engine, if_exists='replace', index=False)
    
# SQL query to create a table with player statistics, including age, market value, and score of attack or midfield positions.
# Additionally, categorize players into age groups and score brackets in order to analyze their performance.
# The score is calculated using a formula that considers the number of goals, yellow cards, and red cards.
# Finally, calculate the average market value for each category.

avg_mkt_value_by_age = pd.read_sql_query(
    """
    -- Create a CTE to calculate age and score for each player
    WITH player_stats AS (
    SELECT
        p.player_id,
        p.market_value_in_eur,
        TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
        SUM(a.goals) AS goals,
        SUM(a.yellow_cards) AS yellow_cards,
        SUM(a.red_cards) AS red_cards,
        -- Score formula is:
        -- goals: The number of goals scored by the player. Each goal increases the score by 1
        -- yellow_cards: The number of yellow cards received. Each yellow card decreases the score by 0.5 
        -- red_cards: The number of red cards received. Each red card decreases the score by 1
        (SUM(a.goals) - (SUM(a.yellow_cards) * 0.5 + SUM(a.red_cards))) AS score
    FROM
        players p
        JOIN appearances a ON p.player_id = a.player_id
        -- Select only players with position of Attack or Midfield
        WHERE p.position = 'Attack' OR 'Midfield'
    GROUP BY
        p.player_id, p.market_value_in_eur, age
    ),

    -- Add age groups and score brackets
    categorized AS (
    SELECT
        *,
        CASE
        WHEN age < 20 THEN '<20'
        WHEN age BETWEEN 20 AND 24 THEN '20-24'
        WHEN age BETWEEN 25 AND 29 THEN '25-29'
        WHEN age BETWEEN 30 AND 34 THEN '30-34'
        ELSE '35+'
        END AS age_group,
        CASE
        WHEN score < 0 THEN '<0'
        WHEN score BETWEEN 0 AND 10 THEN '0-10'
        ELSE '10+'
        END AS score_bracket
    FROM player_stats
    )

    -- Final aggregation: average market value by age group and score bracket
    SELECT
    age_group,
    score_bracket,
    COUNT(*) AS num_players,
    ROUND(AVG(market_value_in_eur), 2) AS avg_market_value_eur
    FROM
    categorized
    GROUP BY
    age_group, score_bracket
    ORDER BY
    age_group, score_bracket;
""",
    engine
)

# Plot the data of average market value by age group and score bracket of  attack or midfield football players

import matplotlib.ticker as mticker

fig, ax = plt.subplots(figsize=(10, 6))
for score_bracket in avg_mkt_value_by_age['score_bracket'].unique():
    subset = avg_mkt_value_by_age[avg_mkt_value_by_age['score_bracket'] == score_bracket]
    ax.plot(subset['age_group'], subset['avg_market_value_eur'], marker='o', label=score_bracket)

ax.set_xlabel('Age Group')
ax.set_ylabel('Average Market Value (€)')
ax.set_title('Average Market Value by Age Group and Score Bracket of Attack and Midfield Football Players')
ax.legend(title='Score Bracket')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'€{int(x):,}'))
plt.tight_layout()
plt.show()

# SQL query to create a CTE with player statistics, including player id, market value, club id and competition name.
# Additionally, create a score to analyze players' performance using a formula that considers the number of goals, yellow and red cards.
# Finally, query the competitions table for league competitiveness and aggregate the number of players, average market value and
# average performance score.

league_competitiveness = pd.read_sql_query(
    """
    -- Create a CTE to calculate the performance score and extract competition name and market value for each player
    WITH player_stats AS (
    SELECT
        p.player_id,
        p.market_value_in_eur,
        comp.name AS competition_name,
        SUM(a.goals) AS total_goals,
        SUM(a.yellow_cards) AS total_yellow_cards,
        SUM(a.red_cards) AS total_red_cards,
        -- Score formula is:
        -- goals: The number of goals scored by the player. Each goal increases the score by 1
        -- yellow_cards: The number of yellow cards received. Each yellow card decreases the score by 0.5 
        -- red_cards: The number of red cards received. Each red card decreases the score by 1
        (SUM(a.goals) - (SUM(a.yellow_cards) * 0.5 + SUM(a.red_cards))) AS performance_score
    FROM
        players p
        JOIN clubs c ON p.current_club_id = c.club_id
        JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
        JOIN appearances a ON p.player_id = a.player_id
        -- Select only players with position of Attack or Midfield
        WHERE p.position = 'Attack' OR 'Midfield'
    GROUP BY
        p.player_id, p.market_value_in_eur, competition_name
    )
    -- Final aggregation: average market value by league competitiveness and performance score
    SELECT
    CASE
        WHEN competition_name IN (
        'premier-league',
        'laliga',
        'bundesliga',
        'serie-a',
        'ligue-1'
        ) THEN 'Competitive'
        ELSE 'Less Competitive'
    END AS league_competitiveness,
    COUNT(*) AS num_players,
    ROUND(AVG(market_value_in_eur), 2) AS avg_market_value_eur,
    ROUND(AVG(performance_score), 2) AS avg_performance_score
    FROM
    player_stats
    GROUP BY
    league_competitiveness;
""",
    engine
)

# Plot the data of average market value by league competitiveness for attack or midfield football players

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(
    league_competitiveness['league_competitiveness'],
    league_competitiveness['avg_market_value_eur'],
    color=['#20beff', '#ff7f0e']
)

ax.set_xlabel('League Competitiveness')
ax.set_ylabel('Average Market Value (€)')
ax.set_title('Average Market Value by League Competitiveness for Attack and Midfield players')

# Format y-axis as EUR currency
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'€{int(x):,}'))

# Annotate bars with EUR values
for bar in bars:
    height = bar.get_height()
    ax.annotate(f'€{int(height):,}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 1),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.show()