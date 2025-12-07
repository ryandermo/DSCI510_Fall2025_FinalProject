# DSCI510_Fall2025_FinalProject
Steam Hidden Gems

#**Special Notes!**
Requires an API Key from OpenCritic API to be included in "key.txt"
https://rapidapi.com/opencritic-opencritic-default/api/opencritic-api

# <Steam Hidden Gems>
The program takes one input, the total # of games.
The program them takes this input number and scrapes SteamCharts for the top "#" games, which are based on their player count.
The scraping will return the Steam "appid"s which are the unique identifiers used by Steam.
Using the Steam Web Store API the appids are used to request data about each game including the base price, sale price, discount %, relase date and more.
The data for each game is printed to a csv.

Note: To run the code a "key.txt" file is required that includes a free api key from Open Critic API on RapidAPI. The free key is limited to 25 requests per day... which greatly reduces the maximum 

# Data sources
SteamCharts "https://steamcharts.com/top" is used to scrape and determine the most popular games in real time. Using beuatifulsoup4 the appid's are retrieved.
Steam Web Store API is then utilized to retrieved further data based off the popular games' appid's.
OpenCritic API is then utilized to pull critic and review information that is then compiled to create various dataframes.
I'm still working on determing how to include data table...

Due to the issues presented by the OpenCritic API key, the data used in the results shown for the jupyter notebook and the final presentation all come from the following google drive:
**https://drive.google.com/file/d/1a4A44AJ9wzXytDundqsrbDVMmrFXqmU6/view?usp=drive_link**

This data can be downloaed and used in the jupyter notebook to analyze a larger swath of data.

# Analysis
The analysis with the project included generating a "popularity facotr" that looked at how popular a game currently is vs it's peak popularity. Additionally it looked at the effect of discounts and ratings.
Comparisons were made between the free vs. paid games and the age of the games was checked.
Analysis looked at how the most popular games have been able to last in popularity and how new games are quite popular.
It then looks for "hidden gems" using a value calculation based on the discounts, popularity, and cost.

# Results 
The data is skewed and hard to draw any real conclusions because the data pulled is from all of the most popular games. 
However, it is clear that cheaper, well discounted games that are near their peak popularity are the true hidden gems.

# Installation
First acquire Opencritc API key from link above and place in "key.txt".
The program requires requests, pandas, numpy, matplotlib.pyplot, seaborn and beautifulsoup4


# Running analysis 
First acquire Opencritc API key from link above and place in "key.txt".

From `src/` directory run:

`python main.py `
This file can be modifed to alter the number of the most popular games retrieved. Default is set to 25 due to the OpenCritic API key limitations.

The results will appear in `results/` folder. All obtained data will be stored in `data/`
