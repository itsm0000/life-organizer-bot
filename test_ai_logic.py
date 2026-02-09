
import os
import asyncio
from dotenv import load_dotenv
from ai_categorizer import categorize_message

load_dotenv()

async def test_ai():
    text = "I have a deadline in four hours to study and make the report and submit it."
    print(f"Testing text: {text}")
    print("Expecting ISO with Time (e.g. 2026-02-10T02:15:00)")
    
    result = await categorize_message(text)
    print("\nAI Result:")
    print(f"Due Date: {result.get('due_date')}")
    print(f"Full JSON: {result}")

if __name__ == "__main__":
    asyncio.run(test_ai())
