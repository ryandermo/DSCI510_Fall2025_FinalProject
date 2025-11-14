# DSCI510_Fall2025_FinalProject
Steam Hidden Gems

# <Steam Hidden Gems>
The program takes one input, the total # of games.
The program them takes this input number and scrapes SteamCharts for the top "#" games, which are based on their player count.
The scraping will return the Steam "appid"s which are the unique identifiers used by Steam.
Using the Steam Web Store API the appids are used to request data about each game including the base price, sale price, discount %, relase date and more.
The data for each game is printed to a csv.

# Data sources
SteamCharts "https://steamcharts.com/top" is used to scrape and determine the most popular games in real time. Using beuatifulsoup4 the appid's are retrieved.
Steam Web Store API is then utilized to retrieved further data based off the popular games' appid's.
OpenCritic API or another source will be used to retrieve more reviews about the popular games.
I'm still working on determing how to include data table...

# Results 
_describe your findings_

# Installation
No API Keys are required.
The program requires requests, pandas and beautifulsoup4


# Running analysis 
From `src/` directory run:

`python test.py `
This file can be modifed to alter the number of the most popular games retrieved.

The results will appear in `results/` folder. All obtained data will be stored in `data/`
