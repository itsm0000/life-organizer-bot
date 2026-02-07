import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
LIFE_AREAS_DB_ID = os.getenv("LIFE_AREAS_DB_ID")

notion = Client(auth=NOTION_TOKEN)

def debug_active_items():
    print(f"Querying DB: {LIFE_AREAS_DB_ID}")
    
    # 1. Get ALL items (no filter) to see everything
    try:
        response = notion.databases.query(database_id=LIFE_AREAS_DB_ID)
        results = response.get("results", [])
        print(f"Total items found: {len(results)}")
        
        for i, page in enumerate(results):
            props = page["properties"]
            
            # Extract basic info
            title = "Untitled"
            if props.get("Name", {}).get("title"):
                title = props["Name"]["title"][0]["text"]["content"]
            
            status = props.get("Status", {}).get("select", {}).get("name", "No Status")
            category = props.get("Category", {}).get("select", {}).get("name", "No Category")
            priority = props.get("Priority", {}).get("select", {}).get("name", "No Priority")
            
            print(f"{i+1}. '{title}' | Status: '{status}' | Category: '{category}' | Priority: '{priority}'")
            
            # Check specifically for Skincare Routine
            if "skincare" in title.lower():
                print(f"   >>> FOUND TARGET: '{title}'")
                print(f"   >>> ID: {page['id']}")
                print(f"   >>> Raw Status: {props.get('Status')}")
                
    except Exception as e:
        print(f"Error querying Notion: {e}")

if __name__ == "__main__":
    debug_active_items()
