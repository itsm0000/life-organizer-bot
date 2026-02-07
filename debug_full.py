"""
Cleanup and Debug Script
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
    print("🧹 Cleaning up old databases...")
    try:
        results = notion.search(filter={"property": "object", "value": "database"})
        count = 0
        for db in results.get("results", []):
            if not db.get("in_trash"):
                print(f"Archiving: {db.get('title', [{}])[0].get('plain_text', 'Untitled')} ({db['id']})")
                notion.databases.update(database_id=db['id'], archived=True)
                count += 1
        print(f"✨ Archived {count} databases.")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def debug_create(parent_id):
    print("\n🧪 Creating Test Database...")
    try:
        # Minimal schema
        db = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_id},
            title=[{"type": "text", "text": {"content": "DEBUG_DB"}}],
            properties={
                "Name": {"title": {}},
                "TestCategory": {"select": {"options": [{"name": "A", "color": "red"}]}}
            }
        )
        print(f"Created DB ID: {db['id']}")
        
        # Check properties immediately from the response
        print(f"Properties in CREATE response: {list(db.get('properties', {}).keys())}")
        
        # Fetch it back to verify
        retrieved = notion.databases.retrieve(database_id=db['id'])
        print(f"Properties in RETRIEVE response: {list(retrieved.get('properties', {}).keys())}")
        
        return db['id']
    except Exception as e:
        print(f"❌ Error creating/retrieving DB: {e}")
        return None

def main():
    # 1. Cleanup
    cleanup()
    
    # 2. Get Parent Page
    print("\n🔍 Finding parent page...")
    search = notion.search(filter={"property": "object", "value": "page"})
    if not search["results"]:
        print("❌ No parent page found!")
        return
        
    parent_page = search["results"][0]
    parent_title = parent_page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
    print(f"Using Parent: {parent_title} ({parent_page['id']})")
    
    # 3. Debug Create
    db_id = debug_create(parent_page['id'])
    
    if db_id:
        print("\n✅ Debug run complete. Check the output above.")

if __name__ == "__main__":
    main()
