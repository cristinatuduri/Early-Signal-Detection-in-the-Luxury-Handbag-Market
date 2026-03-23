"""
eBay Sold Listings Scraper — Extended History (back to 2023)
Uses date range filtering to pull older sold listings.

Install: pip install selenium pandas webdriver-manager
"""

import time
import random
import re
import pandas as pd
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

bags = [
    "Chanel Classic Flap",
    "Hermes Birkin",
    "Hermes Kelly",
    "Dior Saddle Bag",
    "Bottega Veneta Pouch",
    "Louis Vuitton Capucines",
]

PAGES_PER_BAG = 15      
DELAY         = (3, 6)
OUTPUT_FILE   = "ebay_luxury_extended.csv"


def make_driver() -> webdriver.Chrome:
    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

def build_url(query: str, page: int) -> str:
    q = query.replace(" ", "+")
    return (
        f"https://www.ebay.com/sch/i.html?_nkw={q}"
        f"&LH_Sold=1&LH_Complete=1"
        f"&LH_ItemCondition=3000"   # pre-owned only
        f"&_sop=12"                 # sort by most recently sold
        f"&_pgn={page}&_ipg=48"
    )

def parse_price(text: str) -> float | None:
    text = text.replace(",", "")
    match = re.search(r"\d+\.?\d*", text)
    return float(match.group()) if match else None

def scrape_bag(driver: webdriver.Chrome, bag_name: str) -> list[dict]:
    results = []

    for page in range(1, PAGES_PER_BAG + 1):
        url = build_url(bag_name, page)
        print(f"  → Page {page}: {url}")
        driver.get(url)

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.s-card"))
            )
        except Exception:
            print("  !! Timed out.")
            break

        time.sleep(random.uniform(*DELAY))

        items = driver.find_elements(By.CSS_SELECTOR, "li.s-card")
        print(f"  Found {len(items)} cards")
        page_results = []

        for item in items:
            try:
                title = None
                for sel in ["[class*='s-card__title']", "[class*='card__title']"]:
                    try:
                        t = item.find_element(By.CSS_SELECTOR, sel).text.strip()
                        if t:
                            title = t
                            break
                    except Exception:
                        continue

                price = None
                try:
                    price_raw = item.find_element(By.CSS_SELECTOR, "[class*='card__price']").text.strip()
                    price = parse_price(price_raw)
                except Exception:
                    pass

                date = None
                try:
                    d = item.find_element(By.CSS_SELECTOR, ".s-card__caption").text.strip()
                    if d:
                        date = d.replace("Sold", "").strip()
                except Exception:
                    pass

                link = None
                try:
                    link = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                except Exception:
                    pass

                if not price or price < 1000:
                    continue

                page_results.append({
                    "bag_query":   bag_name,
                    "title":       title,
                    "sold_price":  price,
                    "sold_date":   date,
                    "listing_url": link,
                    "scraped_at":  datetime.utcnow().strftime("%Y-%m-%d"),
                })

            except Exception:
                continue

        results.extend(page_results)
        print(f"  ✓ {len(page_results)} valid listings | Running total: {len(results)}")

        if page_results:
            dates = [r['sold_date'] for r in page_results if r['sold_date']]
            if dates and all('2022' in d or '2021' in d or '2020' in d for d in dates):
                print("  Reached pre-2023 data — stopping.")
                break

        time.sleep(random.uniform(*DELAY))

    return results

def main():
    driver      = make_driver()
    all_results = []

    try:
        for bag in bags:
            print(f"\n{'='*55}\nScraping: {bag}\n{'='*55}")
            bag_results = scrape_bag(driver, bag)
            all_results.extend(bag_results)
            print(f"→ '{bag}' done: {len(bag_results)} listings")
            time.sleep(random.uniform(5, 10))
    finally:
        driver.quit()

    if not all_results:
        print("No data collected.")
        return

    df = pd.DataFrame(all_results)
    df['sold_date'] = pd.to_datetime(df['sold_date'], errors='coerce')
    df = df[df['sold_date'] >= '2023-01-01']  # keep from 2023 onwards
    df.drop_duplicates(subset=["listing_url"], inplace=True)
    df.sort_values(["bag_query", "sold_date"], ascending=[True, False], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved {len(df)} listings → '{OUTPUT_FILE}'")
    print(df.groupby('bag_query')['sold_date'].agg(['count', 'min', 'max']))

if __name__ == "__main__":
    main()