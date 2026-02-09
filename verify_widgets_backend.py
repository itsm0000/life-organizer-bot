import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notion_integration import get_upcoming_deadlines, get_completed_today

class TestWidgetsBackend(unittest.TestCase):
    
    @patch('notion_integration.get_active_items')
    def test_get_upcoming_deadlines(self, mock_get_active):
        # Mock active items with dates
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        next_week = today + timedelta(days=7)
        past = today - timedelta(days=2)
        
        mock_get_active.return_value = [
            {
                "id": "1",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Task Tomorrow"}}]},
                    "Date": {"date": {"start": tomorrow.strftime("%Y-%m-%d")}}
                }
            },
            {
                "id": "2",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Task Next Week"}}]},
                    "Due Date": {"date": {"start": next_week.strftime("%Y-%m-%d")}}
                }
            },
            {
                "id": "3",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Task No Date"}}]}
                }
            },
            {
                "id": "4",
                "properties": {
                    "Name": {"title": [{"text": {"content": "Task Past"}}]},
                    "Deadline": {"date": {"start": past.strftime("%Y-%m-%d")}}
                }
            }
        ]
        
        deadlines = get_upcoming_deadlines(limit=5)
        
        # Should return 3 items (Past is excluded if < -1 days? Logic says >= -1)
        # Past (2 days ago) = -2 days. So it should be excluded.
        # Wait, logic says `days_left >= -1`. -2 < -1, so excluded.
        
        self.assertEqual(len(deadlines), 2)
        self.assertEqual(deadlines[0]["title"], "Task Tomorrow")
        self.assertEqual(deadlines[1]["title"], "Task Next Week")
        
        print("\nDeadlines Test Passed:")
        for d in deadlines:
            print(f"- {d['title']} ({d['days_left']} days left)")

    @patch('notion_integration.notion')
    def test_get_completed_today(self, mock_notion):
        # Mock Notion query response
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        mock_notion.request.return_value = {
            "results": [
                {
                    "id": "101",
                    "last_edited_time": f"{today_str}T10:00:00.000Z",
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Completed Task 1"}}]},
                        "Category": {"select": {"name": "Work"}}
                    }
                },
                {
                    "id": "102",
                    "last_edited_time": "2023-01-01T10:00:00.000Z", # Old task
                    "properties": {
                        "Name": {"title": [{"text": {"content": "Old Task"}}]},
                        "Category": {"select": {"name": "Personal"}}
                    }
                }
            ]
        }
        
        completed = get_completed_today()
        
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0]["title"], "Completed Task 1")
        
        print("\nCompleted Today Test Passed:")
        for c in completed:
            print(f"- {c['title']} ({c['category']})")

if __name__ == '__main__':
    unittest.main()
