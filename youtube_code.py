import pandas as pd
from datetime import datetime
from googleapiclient.discovery import build

API_KEY     = "YOUR_API_KEY_HERE"  # Replace with your YouTube Data API key
MAX_RESULTS = 50
OUTPUT_FILE = "youtube_luxury_handbags_extended.csv"

bag_queries = {
    "Chanel Classic Flap": [
        "Chanel Classic Flap review",
        "Chanel Classic Flap unboxing",
        "Chanel Classic Flap worth it",
        "Chanel flap bag 2024",
        "Chanel flap bag 2025",
        "Chanel Classic Flap price increase",
    ],
    "Hermes Birkin": [
        "Hermes Birkin review",
        "Hermes Birkin unboxing",
        "Hermes Birkin worth it",
        "how to buy Hermes Birkin",
        "Birkin bag 2024",
        "Birkin bag 2025",
    ],
    "Hermes Kelly": [
        "Hermes Kelly review",
        "Hermes Kelly unboxing",
        "Hermes Kelly worth it",
        "Hermes Kelly bag 2024",
        "Hermes Kelly bag 2025",
        "Hermes Kelly vs Birkin",
    ],
    "Dior Saddle Bag": [
        "Dior Saddle Bag review",
        "Dior Saddle Bag unboxing",
        "Dior Saddle Bag worth it",
        "Dior Saddle Bag 2024",
        "Dior Saddle Bag 2025",
        "Dior bag review",
    ],
    "Bottega Veneta Pouch": [
        "Bottega Veneta Pouch review",
        "Bottega Veneta Pouch unboxing",
        "Bottega Veneta bag review",
        "Bottega Veneta 2024",
        "Bottega Veneta 2025",
        "Bottega Veneta worth it",
    ],
    "Louis Vuitton Capucines": [
        "Louis Vuitton Capucines review",
        "Louis Vuitton Capucines unboxing",
        "LV Capucines worth it",
        "Louis Vuitton Capucines 2024",
        "Louis Vuitton Capucines 2025",
        "Capucines bag review",
    ],
}

# ── API SETUP ─────────────────────────────────────────────────────────────────
youtube = build("youtube", "v3", developerKey=API_KEY, static_discovery=False)

def search_videos(query: str, max_results: int = MAX_RESULTS) -> list[str]:
    response = youtube.search().list(
        q=query,
        part="id",
        type="video",
        maxResults=max_results,
        order="relevance",
        publishedAfter="2023-01-01T00:00:00Z",  # from 2023 onwards
    ).execute()
    return [item["id"]["videoId"] for item in response.get("items", [])]

def get_video_stats(video_ids: list[str]) -> list[dict]:
    if not video_ids:
        return []
    results = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i+50]
        response = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(chunk),
        ).execute()
        for item in response.get("items", []):
            snippet    = item.get("snippet", {})
            statistics = item.get("statistics", {})
            results.append({
                "video_id":      item["id"],
                "title":         snippet.get("title"),
                "channel":       snippet.get("channelTitle"),
                "published_at":  snippet.get("publishedAt"),
                "view_count":    int(statistics.get("viewCount",    0)),
                "like_count":    int(statistics.get("likeCount",    0)),
                "comment_count": int(statistics.get("commentCount", 0)),
                "url":           f"https://www.youtube.com/watch?v={item['id']}",
            })
    return results

def main():
    all_results = []

    for bag_name, queries in bag_queries.items():
        print(f"\n{'='*55}\nScraping: {bag_name}\n{'='*55}")
        bag_video_ids = set()

        for query in queries:
            print(f"  Searching: '{query}'")
            ids = search_videos(query)
            bag_video_ids.update(ids)
            print(f"  Found {len(ids)} videos")

        print(f"  Fetching stats for {len(bag_video_ids)} unique videos...")
        stats = get_video_stats(list(bag_video_ids))

        for s in stats:
            s["bag_query"]  = bag_name
            s["scraped_at"] = datetime.utcnow().strftime("%Y-%m-%d")

        all_results.extend(stats)
        print(f"  ✓ {len(stats)} videos for '{bag_name}'")

    if not all_results:
        print("No data collected.")
        return

    df = pd.DataFrame(all_results)
    df["published_at"] = pd.to_datetime(df["published_at"])
    df = df[df["published_at"] >= "2023-01-01"]  # filter from 2023
    df.sort_values(["bag_query", "published_at"], ascending=[True, False], inplace=True)
    df.drop_duplicates(subset=["video_id"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved {len(df)} videos → '{OUTPUT_FILE}'")
    print(df.groupby("bag_query")[["view_count", "like_count"]].agg(["count", "mean"]).round(0))

if __name__ == "__main__":
    main()