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

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from bs4 import BeautifulSoup

### Website URLs ###
SteamCharts_URL_base = "https://steamcharts.com/top/p.{page}"
SteamStore_URL = "https://store.steampowered.com/api/appdetails"
OpenCritic_URL = "https://opencritic-api.p.rapidapi.com"

### Retrieves API key for RAPIDAPI for Opencritic API in the 'key.txt' ###
def retrieve_key(filename="key.txt"):
    try:
        with open(filename, "r") as f:
            key =  f.read().strip()
    except ValueError:
        raise ValueError("Filename not located")
    if key == "":
        raise ValueError("Key is empty")
    return key

### Clean and Strip Numbers from Web Scraping ###
def to_int(text: str):
    text = text.replace(",", "").strip()
    try:
        return int(text)
    except:
        return None

### Scrape Data from SteamCharts ###
def most_popular_games_steamcharts_scrape(games: int = 100):
    headers = {"User-Agent": "Mozilla/5.0"}
    appids = []
    retrieved_data = []
    games_on_page = 25 #games per page on SteamCharts
    pages = math.ceil(games / games_on_page)  # uses math library to effectively round up to nearest integer to ensure enough pages are checked

    for page in range(1, pages + 1): #additional page added to range in case some games fail
        if len(appids) >= games:
            break
        url = SteamCharts_URL_base.format(page=page)  # The website has 25 games per page, this modifies the end of the URL to swap between pages and collect more games
        print(f"Taking a closer look at SteamCharts page {page}: {url}")
        response = requests.get(url, headers=headers, timeout=100)

        if response.status_code != 200:
            print(f"Error fetching SteamCharts page {page}.")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")

        # Iterate over each game row in the table
        for table_row in table.find_all("tr"):
            table_data = table_row.find_all("td")
            # There should be 6 columns of data for the table, Rank / Name / Current Count / Last30 Count / Peak Count / HoursPlayed in last 30d
            if len(table_data) < 6:
                continue

            ### Extract the appid and the name
            Identifier = table_data[1].find("a")
            if not Identifier:
                continue

            href = Identifier.get("href", "")
            chunk = re.search(r"/app/(\d+)", href)
            if not chunk:
                continue

            appid = int(chunk.group(1))
            if appid in appids:
                continue

            ### Extract and strip the player counts
            current_players = to_int(table_data[2].get_text(strip=True))
            peak_players = to_int(table_data[4].get_text(strip=True))

            appids.append(appid)
            retrieved_data.append(
                {
                    "appid": appid,
                    "name": Identifier.get_text(strip=True),
                    "current_players": current_players,
                    "peak_players": peak_players,
                }
            )

            if len(appids) >= games:
                break

        if not retrieved_data:
            break

    return appids[:games], retrieved_data


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

    appids, chart_rows = most_popular_games_steamcharts_scrape(games)
    game_rows = []

    for i, appid in enumerate(appids, start=1):

        print(f"[{i}/{len(appids)}] Retrieving appid={appid}...")
        game_info = retrieve_steam(appid)
        if not game_info:
            print(f"Looks like the appid: {appid}, was not found in Steam...")
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

        ### Retrieve some score data and release dates
        metacritic_score = (game_info.get("metacritic") or {}).get("score")
        recommendations = (game_info.get("recommendations") or {}).get("total")
        release_date = (game_info.get("release_date") or {}).get("date", "")

        row = chart_rows[i-1] #Used to find the additional data scraped off of SteamCharts

        ### Add the retrieved data in to our list
        game_rows.append({
            "appid": appid,
            "SteamCharts Name": row["name"],
            "Current Players": row["current_players"],
            "Peak Players": row["peak_players"],
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
        time.sleep(1.70) ### Try to slow down our requests and processing to not upset Steam
        ### Appears that the Steam API has a 5 minute window that allows ~200 requests, so 5 mins * 60 seconds = 300 seconds, 200 requests in 300 seconds is  1.5 reqeust a second
        ### This ensures that a user requesting > 200 games can fulfill that request without crashing

    dataFrame = pd.DataFrame(game_rows)
    return dataFrame

### Retrieves the API Key and contain headers for OpenCritic ###
def opencritic_headers() -> dict:
    key = retrieve_key("key.txt")
    if not key:
        raise RuntimeError("No key file found.")
    return {
        "x-rapidapi-key": key,
        "x-rapidapi-host": "opencritic-api.p.rapid.com"
    }

### Checks if a certain game is in OpenCritic by searching for the name, takes the first available and returns the game ID in OpenCritic ###
def check_opencritic(game: str) -> dict:
    #Checks Opencritic to verify the game is contained
    headers = opencritic_headers()

    try:
        response = requests.get(
            f"{OpenCritic_URL}/meta/search",
            headers = headers,
            params = {"criteria":game},
            timeout = 50,
        )
    except Exception as error:
        print(f"Error fetching OpenCritic page {game}: {error}")

    if response.status_code != 200:
        print(f"Search failed for {game} in OpenCritic.")
        return None

    try:
        results = response.json()
    except ValueError:
        print(f"Error parsing OpenCritic page {game}: {response.text}")
        return None

    if not results:
        print(f"No results for {game} in OpenCritic.")
        return None

    return results[0]

### Retrieves review information from OpenCritic based on an OpenCritic ID ###
def retrieve_opencritic(id: int) -> dict:
    headers = opencritic_headers()

    try:
        response = requests.get(
            f"{OpenCritic_URL}/game/{id}",
            headers = headers,
            timeout = 50,
        )
    except Exception as error:
        print(f"Error fetching OpenCritic page {id}: {error}")
        return None

    if response.status_code != 200:
        print(f"Search failed for {id} in OpenCritic.")
        return None

    try:
        reviews = response.json()
    except ValueError:
        print(f"Error parsing OpenCritic page {id}: {response.text}")
        return None

    return reviews

### Alters the original DataFrame to include information from OpenCritic API ###
def include_opencritic_data(dataframe: pd.DataFrame, max_games: int) -> pd.DataFrame:

    #Uses the previously created dataframe and searches Opencritic to located Opencritic ID and then requests review information for each of the games in the dataframe

    dataframe = dataframe.copy()

    dataframe["OC_ID"] = pd.NA
    dataframe["OC_Name"] = pd.NA
    dataframe["TopCriticScore"] = pd.NA
    dataframe["MedianCriticScore"] = pd.NA
    dataframe["PercentRecommended"] = pd.NA
    dataframe["TotalReviews"] = pd.NA
    dataframe["OC_Tier"] = pd.NA

    rows = dataframe.head(max_games) if max_games is not None else dataframe

    for i, (row_index, row) in enumerate(rows.iterrows(), start=1):
        name = row["game name"]
        print(f"Processing row {i}/{len(rows)}...Currently searching for {name}")

        results = check_opencritic(name)
        if not results:
            continue

        OC_ID = results.get("id")
        OC_Name = results.get("name")

        dataframe.at[row_index, "OC_ID"] = OC_ID
        dataframe.at[row_index, "OC_Name"] = OC_Name

        if OC_ID is None:
            print(f"No OpenCritic ID found for {name}... moving on")
            continue

        reviews = retrieve_opencritic(OC_ID)
        if not reviews:
            print(f"No OpenCritic reviews for {OC_ID}... moving on")
            continue

        dataframe.at[row_index, "TopCriticScore"] = reviews.get("topCriticScore")
        dataframe.at[row_index, "MedianCriticScore"] = reviews.get("medianScore")
        dataframe.at[row_index, "PercentRecommended"] = reviews.get("percentRecommended")
        dataframe.at[row_index, "TotalReviews"] = reviews.get("numReviews")
        dataframe.at[row_index, "OC_Tier"] = reviews.get("tier")

    time.sleep(0.25)
    print("The dataframe now has information from OpenCritic.")

    return dataframe

### Saves to /data in a .csv ###
def save_csv(df: pd.DataFrame, path: str = "data/most_popular_steam_games.csv") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} games to {path}")

def analyze_data(file_path: str = "data/most_popular_steam_games.csv") -> None:
    plt.style.use("Solarize_Light2")
    sns.set_theme()

    df = pd.read_csv(file_path)
    print(df.shape)
    df.head()

    output_folder = "results"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Clean release dates into datetime and years
    if "Release Date" in df.columns:
        df["Release Date Formatted"] = pd.to_datetime(df["Release Date"], errors="coerce")
        df["Release Year"] = df["Release Date Formatted"].dt.year
    else:
        df["Release Year"] = np.nan

    # Extract age of each game
    current_year = pd.Timestamp.today().year
    df["Game Age (Years)"] = current_year - df["Release Year"]

    df["Popularity_Factor"] = df["Current Players"] / df["Peak Players"]

    # Modify the critic score to be between a range of 0-1
    df["Critic Score Normalized"] = df["TopCriticScore"] / 100

    # Attempt to account for $$$ by incorporating the cost
    df["Dollar Value"] = df["Critic Score Normalized"] / (df["Current Price (USD)"] + 1)

    print(df.shape)
    df.head(50)

    # Creates a clean copy of the dataframe if there is an opencritic tier review - eliminates all NaN
    df_clean = df.copy()

    df_clean = df_clean[df_clean["OC_Tier"].notna() & (df_clean["OC_Tier"].astype(str).str.strip() != "")]

    print("After OpenCritic Filtering:", len(df_clean), "from", len(df))

    # Some games are not marked as free and do not contain a price, sometimes these are bundles for games and work as a single launcher. These are filtered out.
    df_clean["Current Price (USD)"] = pd.to_numeric(df_clean["Current Price (USD)"], errors="coerce")

    Mask_Valid_Paid = ((df_clean["Free game?"] == False) & (df_clean["Current Price (USD)"] > 0))
    Mask_Valid_Free = (df_clean["Free game?"] == True)

    df_clean = df_clean[Mask_Valid_Paid | Mask_Valid_Free]
    print("After removing erroneous price entries, for example games that appear as bundles and have no price:",
          len(df_clean))

    print(df_clean.shape)
    df_clean.head(50)

    # Copies separate data sets for free and paid games
    df_free = df_clean[df_clean["Free game?"] == True].copy()
    df_paid = df_clean[df_clean["Free game?"] == False].copy()
    df_discounted = df_paid[df_paid["Discount Percentage"].fillna(0) > 0].copy()

    print("Total free games:", len(df_free))
    print("Total paid games:", len(df_paid))
    print("Total discounted games:", len(df_discounted))

    # Histogram of Critic Tiers
    plt.figure(figsize=(4, 3))
    df_clean["OC_Tier"].value_counts().plot(kind="bar")

    plt.xlabel("OpenCritic Tier")
    plt.ylabel("Number of Games")
    plt.title("Distribution of OpenCritic Tiers [Filtered]")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "OC_Tiers_Histo.png")
    plt.savefig(full_path)

    # Histogram of Release Date
    plt.figure(figsize=(4, 3))
    sns.histplot(df_clean["Release Year"].dropna(), bins=20)

    plt.xlabel("Release Year")
    plt.ylabel("Number of Games")
    plt.title("Games per Release Year [Filtered]")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Release_Date_Histo.png")
    plt.savefig(full_path)

    # Boxplot of Free vs Paid (Top Score)
    plt.figure(figsize=(4, 3))
    sns.boxplot(df_clean, x=df_clean["Free game?"].map({True: "Free", False: "Paid"}), y=df_clean["TopCriticScore"])

    plt.xlabel("Free/Paid")
    plt.ylabel("Top Critic Score")
    plt.title("Top Critic Scores - Free vs Paid")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Free_vs_Paid_Top_Score.png")
    plt.savefig(full_path)

    # Boxplot of Free vs Paid (Median Score)
    plt.figure(figsize=(4, 3))
    sns.boxplot(df_clean, x=df_clean["Free game?"].map({True: "Free", False: "Paid"}), y=df_clean["MedianCriticScore"])

    plt.xlabel("Free/Paid")
    plt.ylabel("Median Critic Score")
    plt.title("Median Critic Scores - Free vs Paid")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Free_vs_Paid_Med_Score.png")
    plt.savefig(full_path)

    # Boxplot of Free vs Paid (Popularity Factor)
    plt.figure(figsize=(4, 3))
    sns.boxplot(df_clean.dropna(subset=["Popularity_Factor"]),
                x=df_clean["Free game?"].map({True: "Free", False: "Paid"}), y=df_clean["Popularity_Factor"])

    plt.xlabel("Free/Paid")
    plt.ylabel("Popularity Factor")
    plt.title("Popularity Factor - Free vs Paid")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Free_vs_Paid_PopularityFactor.png")
    plt.savefig(full_path)

    # Scatterplot Discount Percentage and Popularity
    plt.figure(figsize=(4, 3))
    sns.scatterplot(df_discounted, x="Discount Percentage", y="Popularity_Factor")

    plt.xlabel("Discount Percentage")
    plt.ylabel("Popularity Factor")
    plt.title("Discount Percentage vs Popularity Factor")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Scatter_Discount_Popularity.png")
    plt.savefig(full_path)

    correlation_discount_popularity = df_discounted[["Discount Percentage", "Popularity_Factor"]].corr().iloc[0, 1]
    print(f"Correlation between the discount percentage and the popularity factor: {correlation_discount_popularity}")

    # Scatterplot of Ratings vs Age
    plt.figure(figsize=(4, 3))
    sns.scatterplot(df_clean.dropna(subset=["Game Age (Years)", "TopCriticScore"]), x="Game Age (Years)",
                    y="TopCriticScore")

    plt.xlabel("Game Age (Years)")
    plt.ylabel("Top Critic Score")
    plt.title("Game Age vs Top Critic Score")
    plt.xticks(rotation=0)

    full_path = os.path.join(output_folder, "Scatter_Ratings_Age.png")
    plt.savefig(full_path)

    # Pair plot for comparison of reviews
    columns = ["TopCriticScore", "MedianCriticScore", "PercentRecommended", "TotalReviews"]
    sns.pairplot(df_clean[columns].dropna())
    plt.suptitle("Pair Plot: Critic Scores", y=1.02)

    full_path = os.path.join(output_folder, "Pair_Plot_Reviews.png")
    plt.savefig(full_path)

    # Scatterplot to compare  # of Reviews and # of Current Players
    plt.figure(figsize=(4, 3))
    sns.scatterplot(df_clean, x="TotalReviews", y="Current Players")

    plt.xlabel("Number of OpenCritic Reviews")
    plt.ylabel("Current Players")
    plt.title("Current Players vs Number of Reviews")

    full_path = os.path.join(output_folder, "Scatter_ReviewCount_CurrentPlayers.png")
    plt.savefig(full_path)

    correlation_totalreviews_currentplayers = df_discounted[["TotalReviews", "Current Players"]].corr().iloc[0, 1]
    print(
        f"Correlation between the total OpenCritic reviews and the current number of players: {correlation_totalreviews_currentplayers}")

    Price = df_clean["Current Price (USD)"].fillna(0)
    Score = df_clean["TopCriticScore"].fillna(0)

    df_clean["Value"] = (Score * df_clean["Popularity_Factor"]) / (Price + 200)

    best_overall_games = df_clean.sort_values("Value", ascending=False).head(5)
    worst_games = df_clean.sort_values("Value", ascending=True).head(5)

    print("Top 5 best value games:")
    best_overall_games[["game name", "Current Price (USD)", "TopCriticScore", "Popularity_Factor", "Value"]]

    print("Bottom 5 value games:")
    worst_games[["game name", "Current Price (USD)", "TopCriticScore", "Popularity_Factor", "Value"]]

    Price = df_paid["Current Price (USD)"].fillna(0)
    Score = df_paid["TopCriticScore"].fillna(0)

    df_paid["Value"] = ((Score * df_paid["Popularity_Factor"]) / (Price + 200))

    best_paid_games = df_paid.sort_values("Value", ascending=False).head(5)

    print("Top 5 best paid value games:")
    best_paid_games[["game name", "Current Price (USD)", "TopCriticScore", "Popularity_Factor", "Value"]]

    Price = df_free["Current Price (USD)"].fillna(0)
    Score = df_free["TopCriticScore"].fillna(0)

    df_free["Value"] = ((Score * df_free["Popularity_Factor"]) / (Price + 200))

    best_free_games = df_free.sort_values("Value", ascending=False).head(5)

    print("Top 5 best free games:")
    best_free_games[["game name", "Current Price (USD)", "TopCriticScore", "Popularity_Factor", "Value"]]

    plt.figure(figsize=(7, 5))
    columns = ["TopCriticScore", "MedianCriticScore", "PercentRecommended", "TotalReviews", "Current Players",
               "Peak Players", "Current Price (USD)"]
    sns.heatmap(df_clean[columns].corr(), annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Matrix of Game Stats")
    plt.xticks(rotation=45)

    full_path = os.path.join(output_folder, "Heat_Map.png")
    plt.savefig(full_path)

    plt.figure(figsize=(4, 3))
    sns.histplot(df_clean["Popularity_Factor"], bins=30, kde=True)
    plt.title("Popularity Factor Histogram - (Current/Peak)")
    plt.xlabel("Popularity Factor")
    plt.ylabel("Count")

    full_path = os.path.join(output_folder, "PopularityFactor_Count.png")
    plt.savefig(full_path)

    # Pair plot for comparison of free vs paid
    df_temporary = df_clean.copy()
    df_temporary["Game Type"] = df_temporary["Free game?"].map({True: "Free", False: "Paid"})

    columns = ["TopCriticScore", "PercentRecommended", "TotalReviews", "Popularity_Factor"]
    sns.pairplot(df_temporary, vars=columns, hue="Game Type", diag_kind="kde", corner=False, palette="viridis")

    plt.suptitle("Pair Plot: Free vs Paid", y=1.02)

    full_path = os.path.join(output_folder, "Pair_Plot_Free_vs_Paid.png")
    plt.savefig(full_path)

### Simple function to run the program assuming a set number of games ###
def run(games: int = 100):
    dataFrame = collect_top_steamcharts_games(games)
    dataFrame_appended = include_opencritic_data(dataFrame, games)
    save_csv(dataFrame_appended, path="data/most_popular_steam_games.csv")