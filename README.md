# Football Data Analysis Project

## Overview

This project analyzes football player and club data, focusing on market values, performance scores, and league competitiveness. By joining multiple data sources, we evaluate player performance and club characteristics, test hypotheses, and uncover insights about player value and impact across domestic and international competitions.

## Data Sources

The project utilizes the following tables from the SQL database 'Football Data from Transfermarkt' by David Cariboo on [Kaggle](https://www.kaggle.com/datasets/davidcariboo/player-scores):

- **players**: Contains player information, including position, market value, goals, yellow/red cards, and country of birth.
- **clubs**: Contains club details, including club name and domestic competition ID.
- **competitions**: Contains competition details, including competition name (e.g., 'uefa-champions-league').
- **appearances**: Tracks player appearances, goals, and cards per match.

## Key Features

- **Performance Scoring**:  
  Calculates player performance using the formula:  
  `score = goals - (yellow_cards * 0.5 + red_cards)`

- **Market Value Analysis**:  
  Compares market values of players by position, club, and league.

- **League Competitiveness**:  
  Groups players by the competitiveness of their domestic leagues (based on UEFA coefficients or top league lists).

- **Hypothesis Testing**:  
  Tests multiple hypotheses including:
  - Market value differences between younger and older players with similar performance scores.
  - Value and performance differences between competitive and less competitive leagues.
  
- **Data Visualization**:  
  Plots average market value by age group, score bracket, and league competitiveness for attack and midfield players.