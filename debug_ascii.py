"""
Cleanup and Debug Script (ASCII safe)
1. Archives ALL databases the bot can see (to clean up duplicates)
2. Tries to create a SINGLE database with one property
3. Prints the full response to see if properties were created
"""
import os
import json
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

def cleanup():
    print("Cleaning up old databases...")
    try:
        # Search for everything and filter for databases manually
        results = notion.search(query="")
        count = 0
        for item in results.get("results", []):
            if item["object"] == "database" and not item.get("in_trash"):
                title = item.get("title", [{}])[0].get("plain_text", "Untitled") if item.get("title") else "Untitled"
                print(f"Archiving: {title} ({item['id']})")
                notion.databases.update(database_id=item['id'], archived=True)
                count += 1
        print(f"Archived {count} databases.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def debug_create(parent_id):
    print("\nCreating Test Database...")
    try:
        # Minimal schema - Title 'Name' and RichText 'Notes'
        db = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "DEBUG_DB_MINIMAL"}}],
            properties={
                "Name": {"title": {}},
                "Notes": {"rich_text": {}}
            }
        )
        print(f"Created DB ID: {db['id']}")
        
        # Check properties immediately
        props = db.get('properties', {})
        print(f"Properties in CREATE response keys: {list(props.keys())}")
        
        # Verify via retrieve
        retrieved = notion.databases.retrieve(database_id=db['id'])
        r_props = retrieved.get('properties', {})
        print(f"Properties in RETRIEVE response keys: {list(r_props.keys())}")
        
        return db['id']
    except Exception as e:
        print(f"Error creating/retrieving DB: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    cleanup()
    
    print("\nFinding parent page...")
    search = notion.search(filter={"property": "object", "value": "page"})
    if not search["results"]:
        print("No parent page found!")
        return
        
    parent_page = search["results"][0]
    try:
        title = parent_page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
    except:
        title = "Unknown"
        
    print(f"Using Parent: {title} ({parent_page['id']})")
    
    debug_create(parent_page['id'])

if __name__ == "__main__":
    main()
