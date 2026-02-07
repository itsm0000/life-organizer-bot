"""
Debug Inline Database Creation
Tries to create an INLINE database to see if properties persist better.
"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

def main():
    print("Finding parent page...")
    search = notion.search(filter={"property": "object", "value": "page"})
    if not search["results"]:
        print("No parent page found!")
        return
        
    parent_page = search["results"][0]
    title = parent_page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")
    print(f"Using Parent: {title} ({parent_page['id']})")
    
    print("\nCreating Inline Test Database...")
    try:
        db = notion.databases.create(
            parent={"type": "page_id", "page_id": parent_page['id']},
            title=[{"type": "text", "text": {"content": "DEBUG_INLINE_DB"}}],
            properties={
                "Name": {"title": {}},
                "TestProp": {"rich_text": {}}
            },
            is_inline=True 
        )
        print(f"Created DB ID: {db['id']}")
        
        # Check properties
        props = db.get('properties', {})
        print(f"Properties in CREATE response keys: {list(props.keys())}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
