"""
Migration Script: Add visual styling to existing Notion pages
Run this once to update all existing Life Areas entries with icons and covers
"""
import os
import sys

# Fix Windows console encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

# Category-specific emoji icons
CATEGORY_ICONS = {
    "Health": "💪",
    "Study": "📚",
    "Work": "💼",
    "Ideas": "💡",
    "Shopping": "🛒",
    "Skills": "🎯",
    "Finance": "💰",
    "Social": "👥",
    "Personal": "🌟",
    "Personal Projects": "🚀",
}

# Category-specific cover images (Unsplash - reliable and matching content)
CATEGORY_COVERS = {
    "Health": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200",  # Fitness/wellness
    "Study": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=1200",  # Books/study
    "Work": "https://images.unsplash.com/photo-1497215842964-222b430dc094?w=1200",  # Modern office
    "Ideas": "https://images.unsplash.com/photo-1493612276216-ee3925520721?w=1200",  # Creative lightbulbs
    "Shopping": "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1200",  # Shopping bags
    "Skills": "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=1200",  # Learning/skills
    "Finance": "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=1200",  # Finance/money
    "Social": "https://images.unsplash.com/photo-1529156069898-49953e39b3ac?w=1200",  # Friends/social
    "Personal": "https://images.unsplash.com/photo-1516534775068-ba3e7458af70?w=1200",  # Personal growth
    "Personal Projects": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=1200",  # Projects/laptop
}

DEFAULT_COVER = "https://images.unsplash.com/photo-1557683316-973673baf926?w=1200"  # Purple gradient fallback


def migrate_life_areas():
    """Update all Life Areas pages with icons and category-matched covers"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    print(f"🔄 Fetching pages from Life Areas database...")
    
    response = notion.request(
        path=f"databases/{db_id}/query",
        method="POST",
        body={}
    )
    
    pages = response.get("results", [])
    print(f"📄 Found {len(pages)} pages to update\n")
    
    updated = 0
    for page in pages:
        page_id = page["id"]
        props = page.get("properties", {})
        
        # Get title
        title = "Untitled"
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0].get("text", {}).get("content", "Untitled")
        
        # Get category
        category = props.get("Category", {}).get("select", {})
        category_name = category.get("name", "Other") if category else "Other"
        
        # Determine icon and cover based on CATEGORY (not priority)
        icon_emoji = CATEGORY_ICONS.get(category_name, "📌")
        cover_url = CATEGORY_COVERS.get(category_name, DEFAULT_COVER)
        
        try:
            notion.pages.update(
                page_id=page_id,
                icon={"type": "emoji", "emoji": icon_emoji},
                cover={"type": "external", "external": {"url": cover_url}}
            )
            print(f"✅ {icon_emoji} {title} [{category_name}]")
            updated += 1
        except Exception as e:
            print(f"❌ Failed: {title} - {e}")
    
    print(f"\n🎉 Updated {updated}/{len(pages)} pages!")


if __name__ == "__main__":
    print("=" * 50)
    print("🎨 Notion Visual Migration Script")
    print("=" * 50)
    print("Mode: Category-matched covers")
    print()
    
    migrate_life_areas()
