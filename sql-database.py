# Import libraries
import pandas as pd
import sqlalchemy as sqla
import kagglehub
import os
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
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
    
# SQL query to create a table with player statistics, including age and market value of all positions.<br>
# Categorize players into age groups.<br>
# Finally, calculate the average market value for each age bin.

avg_mkt_value_by_age = pd.read_sql_query(
    """
    -- Create a CTE to calculate age and score for each player
    WITH player_stats AS (
        SELECT
            p.player_id,
            p.market_value_in_eur,
            TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age
        FROM
            players p
            JOIN appearances a ON p.player_id = a.player_id
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
            END AS age_group
        FROM player_stats
    )

    -- Final aggregation: average market value by age group
    SELECT
        age_group,
        COUNT(*) AS num_players,
        ROUND(AVG(market_value_in_eur), 2) AS avg_market_value_eur
    FROM
        categorized
    GROUP BY
        age_group
    ORDER BY
        age_group;
""",
    engine
)

# Plot the data of average market value by age group of all positions
fig, ax = plt.subplots(figsize=(10, 6))
for score_bracket in avg_mkt_value_by_age['age_group'].unique():
    subset = avg_mkt_value_by_age[avg_mkt_value_by_age['age_group'] == score_bracket]
    ax.bar(subset['age_group'], subset['avg_market_value_eur'], label=score_bracket)
ax.set_title('Average Market Value of Football Players of All Positions by Age Group')
ax.set_xlabel('Age Group')
ax.set_ylabel('Average Market Value (EUR)')
ax.legend(title='Age Group')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x/1e6)}M'))
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# SQL query to create a CTE with player statistics, including player id, market value, club id and competition name.<br>
# Finally, query the competitions table for league competitiveness and aggregate the number of players and average market value.

league_competitiveness = pd.read_sql_query(
    """
    -- Create a CTE to calculate the performance score and extract competition name and market value for each player
    WITH player_stats AS (
    SELECT
        p.player_id,
        p.market_value_in_eur,
        comp.name AS competition_name
    FROM
        players p
        JOIN clubs c ON p.current_club_id = c.club_id
        JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
        JOIN appearances a ON p.player_id = a.player_id
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
    ROUND(AVG(market_value_in_eur), 2) AS avg_market_value_eur
    FROM
    player_stats
    GROUP BY
    league_competitiveness;
""",
    engine
)

# Plot the data of average market value by league competitiveness for all positions

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(
    league_competitiveness['league_competitiveness'],
    league_competitiveness['avg_market_value_eur'],
    color=['#20beff', '#ffbd59']
)

ax.set_xlabel('League Competitiveness')
ax.set_ylabel('Average Market Value (€)')
ax.set_title('Average Market Value by League Competitiveness for All Player Positions')

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

# Bonus: SQL query to find the top 10 attack and midfield players with the highest market value.

highest_market_value = pd.read_sql_query(
    """
    SELECT
        p.name AS player_name,
        TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE()) AS age,
        p.position,
        p.market_value_in_eur,
        c.name AS club_name,
        comp.name AS competition_name
    FROM
        players p
        JOIN clubs c ON p.current_club_id = c.club_id
        JOIN competitions comp ON c.domestic_competition_id = comp.competition_id
        WHERE
        p.position IN ('Attack', 'Midfield')
    ORDER BY
        p.market_value_in_eur DESC
    LIMIT 10;
""",
    engine
)
highest_market_value

# Average age and market value of the top 10 attack and midfield players with the highest market value

avg_age_and_market_value_top10 = pd.read_sql_query(
    """
    SELECT
        AVG(TIMESTAMPDIFF(YEAR, p.date_of_birth, CURDATE())) AS avg_age,
        AVG(p.market_value_in_eur) AS avg_market_value
    FROM (
        SELECT *
        FROM players
        WHERE position IN ('Attack', 'Midfield')
        ORDER BY market_value_in_eur DESC
        LIMIT 10
    ) p
""",
    engine
)
avg_age_and_market_value_top10