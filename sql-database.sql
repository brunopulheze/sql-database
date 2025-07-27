-- First Hypothesis:
-- Do younger players tend to have a higher market value than older players?

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


-- Second hypothesis:
-- Do players in top domestic leagues have higher average market values than those in less competitive leagues?

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

-- Bonus: SQL query to find the top 10 attack and midfield players with the highest market value
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

-- Average age and market value of the top 10 attack and midfield players with the highest market value

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