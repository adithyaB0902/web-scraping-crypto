import os
import time
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def get_top_cryptos(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://coinmarketcap.com/")

    wait = WebDriverWait(driver, 20)
    try:
        # Wait for the main table container by class name or more reliable container
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.cmc-table")))
        # Then wait until at least 10 rows inside the table body are present
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.cmc-table tbody tr")))
    except Exception as e:
        print(f"Error waiting for table: {e}")
        print("Page snapshot (first 500 chars):")
        print(driver.page_source[:500])
        driver.quit()
        return pd.DataFrame()

    rows = driver.find_elements(By.CSS_SELECTOR, "table.cmc-table tbody tr")[:10]
    crypto_data = []

    for idx, row in enumerate(rows):
        try:
            cols = row.find_elements(By.TAG_NAME, 'td')
            # Adjust column indexes based on current site structure
            name = cols[2].find_element(By.TAG_NAME, 'p').text
            price = cols[3].text
            change_24h = cols[4].text
            market_cap = cols[7].text
            crypto_data.append({
                "Name": name,
                "Price": price,
                "24h Change": change_24h,
                "Market Cap": market_cap
            })
        except Exception as e:
            print(f"Skipping row {idx} due to error: {e}")
            continue

    driver.quit()
    return pd.DataFrame(crypto_data)

def save_to_csv(df, filename="data/crypto_prices.csv"):
    os.makedirs("data", exist_ok=True)
    df["Timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if os.path.exists(filename):
        old = pd.read_csv(filename)
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(filename, index=False)
    print(f"✅ Data saved successfully to {filename}")

def main():
    print("Fetching real-time cryptocurrency data from CoinMarketCap...")
    data = get_top_cryptos(headless=True)

    if data.empty:
        print("⚠️ No data found. Check selectors or your internet connection.")
    else:
        print(data)
        save_to_csv(data)

        try:
            data["24h Change %"] = data["24h Change"].str.replace("%", "").astype(float)
            top_gainers = data[data["24h Change %"] > 5]
            if not top_gainers.empty:
                print("\n🚀 Top 24h Gainers:")
                print(top_gainers[["Name", "Price", "24h Change"]])
            else:
                print("\nNo coin gained above +5% in the last 24h.")
        except Exception as e:
            print(f"Filtering skipped due to parsing error: {e}")

if __name__ == "__main__":
    main()