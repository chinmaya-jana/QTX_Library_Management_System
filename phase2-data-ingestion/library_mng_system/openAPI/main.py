import argparse
import time
import requests
import json
from pprint import pprint
import os

BASE_URL = "https://openlibrary.org"

def get(endpoint: str, params: dict = None):
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        time.sleep(1)  # Rate limiting
        return response.json()
    except Exception as e:
        print(f"Failed to fetch {endpoint}: {e}")
        return {}

def main():
    parser = argparse.ArgumentParser(description="Inspect Open Library API fields.")
    parser.add_argument("--author", required=True, help="Author name to search for")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of works to inspect")
    parser.add_argument("--output", default="author_data.json", help="File to save the raw output")
    args = parser.parse_args()

    # Ensure output file is saved inside the openAPI folder (relative to this script)
    if not os.path.isabs(args.output):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(script_dir, args.output)
    else:
        output_path = args.output

    output_data = {}

    print("\n🔍 Searching for author...")
    search_data = get("/search/authors.json", params={"q": args.author})
    if not search_data.get("docs"):
        print("❌ No author found.")
        return

    author_doc = search_data["docs"][0]
    print(f"\n🔎 Author Search Result Keys:")
    pprint(author_doc.keys())

    output_data["author_search_result"] = author_doc

    author_key = author_doc.get("key")
    if not author_key:
        print("❌ Author key not found.")
        return

    print(f"\n📚 Fetching works for author key: {author_key}")
    works_data = get(f"/authors/{author_key}/works.json", params={"limit": args.limit})
    works = works_data.get("entries", [])

    if not works:
        print("❌ No works found.")
        return

    print(f"\n📘 Work Entry Keys (1st book):")
    pprint(works[0].keys())

    output_data["works_list"] = works

    first_work_key = works[0].get("key")
    if first_work_key:
        print(f"\n📖 Fetching full book details for: {first_work_key}")
        book_details = get(f"{first_work_key}.json")
        print("\n📄 Book Detail Keys:")
        pprint(book_details.keys())
        output_data["book_detail"] = book_details
    else:
        print("⚠️ No work key found in first entry.")

    # Save all raw data to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Raw API data saved to: {output_path}")

if __name__ == "__main__":
    main()
