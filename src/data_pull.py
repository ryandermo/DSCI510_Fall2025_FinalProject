#DSCI 510 - Ryan McDermott - Final Project
#Primary file used to both scrape data from SteamCharts and retrieve information from Steam using API


#Initially Scrapes SteamCharts various webpages to retrieve a set number of the most popular games.
#The web scraped data is then used to retrieve further information from Steam using the Steam Store API
#This retrieves information like price, discounts, release date, ratings and more


#Data Sources

#Source 1 - SteamCharts via Web Scraping
# https://steamcharts.com/top

#Source 2 - Steam Web Store API, no key needed
# https://store.steampowered.com/api/appdetails?appids=%3CAPPID%3E&cc=us&l=en

import requests
import math
import re
import pandas as pd
import os
import time
from bs4 import BeautifulSoup


#Website URLs
SteamCharts_URL_base = "https://steamcharts.com/top/p.{page}"
SteamStore_URL = "https://store.steampowered.com/api/appdetails"


### Scrape Data from SteamCharts ###
def most_popular_games_steamcharts_scrape(games: int = 100) -> list:
    headers = {"User-Agent": "Mozilla/5.0"}
    appids = []
    games_on_page = 25 #games per page on SteamCharts
    pages = math.ceil(games / games_on_page)  # uses math library to effectively round up to nearest integer to ensure enough pages are checked

    for page in range(1, pages + 1): #additional page to range in case some games fail
        if len(appids) >= games:
            break
        url = SteamCharts_URL_base.format(page=page)  # The website has 25 games per page, this modifies the end of the URL to swap between pages and collect more games
        print(f"Taking a closer look at SteamCharts page {page}: {url}")
        response = requests.get(url, headers=headers, timeout=100)

        if response.status_code != 200:
            print(f"Error fetching SteamCharts page {page}.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        retrieved_appids = []
        for search in soup.select("td.game-name a"):
            href = search.get("href", "")
            chunk = re.search(r"/app/(\d+)", href) #searches for digits after "app" which are the app id's
            if chunk:
                appid = int(chunk.group(1))
                if appid not in appids:
                    appids.append(appid)
                    retrieved_appids.append(appid)
                    if len(appids) >= games:
                        break
        print(f"  Located {len(retrieved_appids)} additional appids (total {len(appids)})")

        if not retrieved_appids:
            break

    print(f"Scraped a total of {len(appids)} appids from SteamCharts")
    return appids[:games]


### Retrieve Game Data from Steam API via appids ###
def retrieve_steam(appid: int) ->  dict:
    params = {"appids": appid, "cc": "us", "l": "en"} #Sets requests for specific game via appid in US currency and English language
    try:
        response = requests.get(SteamStore_URL, params=params, timeout=100)
        if response.status_code != 200:
            return None
        question = response.json()
        answer = question.get(str(appid), {})
        if not answer.get("success"):
            return None
        return answer.get("data", {}) #Return data of game from store given appid
    except Exception:
        return None

### Combines the SteamCharts and Steam API data together in to a dataset within Pandas ###
def collect_top_steamcharts_games(games: int = 100) -> pd.DataFrame:

    appids = most_popular_games_steamcharts_scrape(games)
    game_rows = []

    for i, appid in enumerate(appids, start=1):

        print(f"[{i}/{len(appids)}] Retrieving appid={appid}...")
        game_info = retrieve_steam(appid)
        if not game_info:
            continue

        game_name = game_info.get("name")
        free = game_info.get("is_free", False)

        base_price, current_price, discount_percentage, discounted = None, None, None, False
        price_info = game_info.get("price_overview")

        #Return USD currency in cents so must convert in to dollars
        if price_info:
            base_price_cents = price_info.get("initial")
            current_price_cents = price_info.get("final")
            discount_percentage = price_info.get("discount_percent")
            if isinstance(base_price_cents, int):
                base_price = base_price_cents / 100.0
            if isinstance(current_price_cents, int):
                current_price = current_price_cents / 100.0
            if discount_percentage > 0:
                discounted = True
        if base_price is None and free:
            base_price = current_price = 0.0

        #Retrieve some score data and release dates
        metacritic_score = (game_info.get("metacritic") or {}).get("score")
        recommendations = (game_info.get("recommendations") or {}).get("total")
        release_date = (game_info.get("release_date") or {}).get("date", "")

        #Add the retrieved data in to our list
        game_rows.append({
            "appid": appid,
            "game name": game_name,
            "Free game?": free,
            "Base Price (USD)": base_price,
            "Current Price (USD)": current_price,
            "Discount Percentage": discount_percentage,
            "On sale?": discounted,
            "Release Date": release_date,
            "Metacritic Score": metacritic_score,
            "Total Recommendations": recommendations,
        })
        time.sleep(0.25) #Try to slow down our requests and processing to not upset Steam

    dataFrame = pd.DataFrame(game_rows)
    return dataFrame

### Saves to /data in a .csv ###
def save_csv(df: pd.DataFrame, path: str = "data/most_popular_steam_games.csv") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} games to {path}")

### Simple function to rund the prograam assuming a set number of games ###
def run(games: int = 100):
    dataFrame = collect_top_steamcharts_games(games)
    save_csv(dataFrame, path="data/most_popular_steam_games.csv")