
import os
import asyncio
from dotenv import load_dotenv
from ai_categorizer import categorize_message

load_dotenv()

async def test_ai():
    # Test case 1: No deadline mentioned
    text_no_date = "Create a tool to tag studio content"
    print(f"Testing text (No Date): {text_no_date}")
    
    result = await categorize_message(text_no_date)
    print("\nAI Result (Should have NO due_date):")
    print(f"Due Date: {result.get('due_date')}")
    print(f"Full JSON: {result}")
    
    print("-" * 30)

    # Test case 2: Explicit deadline
    text_with_date = "Submit report by tomorrow 5pm"
    print(f"Testing text (With Date): {text_with_date}")
    
    result_Date = await categorize_message(text_with_date)
    print("\nAI Result (Should have due_date):")
    print(f"Due Date: {result_Date.get('due_date')}")

    print("-" * 30)

    # Test case 3: Ambiguous action (Should be NULL date)
    text_ambiguous = "I need to start working on the project"
    print(f"Testing text (Ambiguous): {text_ambiguous}")
    
    result_ambiguous = await categorize_message(text_ambiguous)
    print("\nAI Result (Should have NO due_date):")
    print(f"Due Date: {result_ambiguous.get('due_date')}")

if __name__ == "__main__":
    asyncio.run(test_ai())
