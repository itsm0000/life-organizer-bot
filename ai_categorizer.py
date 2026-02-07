"""
AI Categorizer using Groq (Llama 3)
Free and fast AI categorization for life organization
"""
import os
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


CATEGORIZATION_PROMPT = """You are an AI assistant helping someone with ADHD organize their life. 
Analyze the following message and categorize it.

Categories:
- Health: fitness, nutrition, skincare, sleep, medical
- Study: university courses, exams, assignments, learning materials
- Personal Projects: coding projects, side businesses, entrepreneurship
- Skills: learning new skills (instruments, chess, cooking, drawing, etc.)
- Creative: content creation, streaming, video editing, art, music
- Shopping: things to buy, product research
- Ideas: random thoughts, future possibilities, things to explore

Types:
- Task: something to do
- Goal: something to achieve
- Idea: something to consider/explore
- Resource: useful information/link/reference

Priority (based on urgency/importance):
- High: university deadlines, health issues, critical tasks
- Medium: personal projects, skill development
- Low: ideas, shopping, exploration

Respond ONLY with valid JSON, no other text:
{
  "category": "category_name",
  "type": "type_name",
  "priority": "priority_level",
  "title": "short title (max 50 chars)",
  "summary": "brief summary of the content",
  "suggested_action": "what the user should do with this (optional)"
}"""


async def categorize_message(message_text, has_image=False, has_file=False):
    """
    Categorize a message using Groq's Llama 3
    
    Args:
        message_text: The text content
        has_image: Whether message includes an image
        has_file: Whether message includes a file
    
    Returns:
        dict: Categorization results
    """
    user_message = message_text
    
    if has_image:
        user_message += "\n\n[Note: This message includes an image]"
    if has_file:
        user_message += "\n\n[Note: This message includes a file/document]"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [
                        {"role": "system", "content": CATEGORIZATION_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            result = json.loads(content)
            return result
    
    except Exception as e:
        print(f"Error in categorization: {e}")
        # Fallback categorization
        return {
            "category": "Ideas",
            "type": "Idea",
            "priority": "Low",
            "title": message_text[:50],
            "summary": message_text,
            "suggested_action": "Review and categorize manually"
        }


async def analyze_image(image_data, caption=""):
    """
    Analyze an image - placeholder for future implementation
    Note: Groq doesn't support vision yet, so we use caption-based categorization
    
    Args:
        image_data: Image bytes or PIL Image
        caption: Optional text caption
    
    Returns:
        dict: Analysis results
    """
    # For now, just categorize based on caption
    if caption:
        result = await categorize_message(f"Image with caption: {caption}", has_image=True)
        return {
            "description": caption,
            "category": result["category"],
            "suggested_title": result["title"]
        }
    
    return {
        "description": "Image without caption",
        "category": "Ideas",
        "suggested_title": "Image"
    }
