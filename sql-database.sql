-- First Hypothesis:
-- Do younger players tend to have a higher market value than older players with similar performance scores?

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


-- Second hypothesis:
-- Do players in top domestic leagues have higher average market values and performance scores than those in less competitive leagues?

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