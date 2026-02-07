"""List all databases to find ones with proper access"""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

print("Searching for all databases the integration can access...")

try:
    # Search without filter to get all objects
    results = notion.search(query="")
    
    print(f"\nFound {len(results['results'])} objects:\n")
    
    for item in results['results']:
        if item['object'] == 'database':
            db_id = item['id']
            title = item.get('title', [{}])[0].get('plain_text', 'Untitled') if item.get('title') else 'Untitled'
            props = list(item.get('properties', {}).keys())
            
            print(f"Database: {title}")
            print(f"  ID: {db_id}")
            print(f"  Properties: {props if props else 'NONE (no access)'}")
            print()
        
except Exception as e:
    print(f"ERROR: {e}")
