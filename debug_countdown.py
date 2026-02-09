
from datetime import datetime, timedelta

def test_countdown():
    # Simulate Current Time: Feb 9, 22:16
    now_str = "2026-02-09T22:16:00"
    now = datetime.fromisoformat(now_str)
    
    # Simulate Task Deadline: Feb 10, 02:15 (From User Screenshot)
    # Notion usually returns ISO with 'T'
    deadline_str = "2026-02-10T02:15:00" 
    
    print(f"Now: {now}")
    print(f"Deadline: {deadline_str}")
    
    # Logic from bot.py
    try:
        if "T" in deadline_str:
            target_dt = datetime.fromisoformat(deadline_str).replace(tzinfo=None)
            diff = target_dt - now
            hours = int(diff.total_seconds() / 3600)
            days = diff.days # This is what notion_integration's days_left might be? 
            # Wait, notion_integration calculates days_left separately.
            
            # Replicating notion_integration 'days_left' logic
            # days_left = (target_date - now).days
            days_left = (target_dt - now).days
            
            print(f"Diff: {diff}")
            print(f"Hours: {hours}")
            print(f"Days Left (raw): {days_left}")
            
            time_left_str = "ERROR"
            
            if hours < 0:
                time_left_str = f"🔥 OVERDUE ({abs(hours)}h)"
            elif hours < 24:
                time_left_str = f"💣 {hours}h LEFT"
            else:
                time_left_str = f"{days_left} DAYS LEFT ({hours // 24}d)"
                
            print(f"Result String: {time_left_str}")
            
        else:
            print("No T in date")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_countdown()
