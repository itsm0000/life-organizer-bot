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
}

# Animated gradient GIFs for more visual appeal
PRIORITY_COVERS = {
    "High": "https://media.giphy.com/media/l0HlBO7eyXzSZkJri/giphy.gif",  # Animated purple
    "Medium": "https://media.giphy.com/media/3o7TKSjRrfIPjeYFEc/giphy.gif",  # Animated gradient
    "Low": "https://media.giphy.com/media/xTiTnxpQ3ghPiB2Hp6/giphy.gif",  # Soft animated
}

# Fallback to static Unsplash if GIFs cause issues
PRIORITY_COVERS_STATIC = {
    "High": "https://images.unsplash.com/photo-1557682250-33bd709cbe85?w=1200",
    "Medium": "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=1200",
    "Low": "https://images.unsplash.com/photo-1558591710-4b4a1ae0f04d?w=1200",
}


def migrate_life_areas(use_animated=True):
    """Update all Life Areas pages with icons and covers"""
    db_id = os.getenv("LIFE_AREAS_DB_ID")
    
    covers = PRIORITY_COVERS if use_animated else PRIORITY_COVERS_STATIC
    
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
        
        # Get category and priority
        category = props.get("Category", {}).get("select", {})
        category_name = category.get("name", "Other") if category else "Other"
        
        priority = props.get("Priority", {}).get("select", {})
        priority_name = priority.get("name", "Medium") if priority else "Medium"
        
        # Determine icon and cover
        icon_emoji = CATEGORY_ICONS.get(category_name, "📌")
        cover_url = covers.get(priority_name, covers["Medium"])
        
        try:
            notion.pages.update(
                page_id=page_id,
                icon={"type": "emoji", "emoji": icon_emoji},
                cover={"type": "external", "external": {"url": cover_url}}
            )
            print(f"✅ {icon_emoji} {title} [{priority_name}]")
            updated += 1
        except Exception as e:
            print(f"❌ Failed: {title} - {e}")
    
    print(f"\n🎉 Updated {updated}/{len(pages)} pages!")


if __name__ == "__main__":
    import sys
    
    use_animated = "--static" not in sys.argv
    
    print("=" * 50)
    print("🎨 Notion Visual Migration Script")
    print("=" * 50)
    print(f"Mode: {'Animated GIF covers' if use_animated else 'Static image covers'}")
    print()
    
    migrate_life_areas(use_animated)
