"""
Safe Cleanup Script
Archives ALL databases the bot can see.
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

def main():
    print("Final Cleanup...")
    try:
        # Search for everything
        results = notion.search(query="")
        count = 0
        for item in results.get("results", []):
            if item["object"] == "database" and not item.get("in_trash"):
                # Safe title extraction
                title = "Untitled"
                if item.get("title"):
                    title = item.get("title")[0].get("plain_text", "Untitled")
                
                print(f"Archiving: {title} ({item['id']})")
                notion.databases.update(database_id=item['id'], archived=True)
                count += 1
        print(f"Archived {count} databases.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
