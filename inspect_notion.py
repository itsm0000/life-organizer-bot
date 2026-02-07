import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

try:
    notion = Client(auth=os.getenv("NOTION_TOKEN"))
    print("Notion client created.")
    print(f"Type of notion.databases: {type(notion.databases)}")
    print("Attributes of notion.databases:")
    print("Attributes of notion (client):")
    print(dir(notion))

    # Try raw request workaround with different paths
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    if db_id:
        paths_to_try = [
            f"databases/{db_id}/query",
            f"/databases/{db_id}/query",
            f"v1/databases/{db_id}/query",
        ]
        
        for path in paths_to_try:
            print(f"Testing path: '{path}'...")
            try:
                response = notion.request(
                    path=path,
                    method="POST",
                    body={}
                )
                print(f"SUCCESS with path '{path}'! Keys: {list(response.keys())}")
                break
            except Exception as e:
                print(f"Failed with path '{path}': {e}")
    else:
        print("No DB ID found.")

except Exception as e:
    print(f"Error: {e}")
