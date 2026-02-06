"""
AI Categorizer using Gemini Flash
Analyzes messages and categorizes them into life areas
"""
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))


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

Respond in JSON format:
{
  "category": "category_name",
  "type": "type_name",
  "priority": "priority_level",
  "title": "short title (max 50 chars)",
  "summary": "brief summary of the content",
  "suggested_action": "what the user should do with this (optional)"
}

Message to analyze:
"""


async def categorize_message(message_text, has_image=False, has_file=False):
    """
    Categorize a message using Gemini Flash
    
    Args:
        message_text: The text content
        has_image: Whether message includes an image
        has_file: Whether message includes a file
    
    Returns:
        dict: Categorization results
    """
    prompt = CATEGORIZATION_PROMPT + f"\n{message_text}"
    
    if has_image:
        prompt += "\n\n[Note: This message includes an image]"
    if has_file:
        prompt += "\n\n[Note: This message includes a file/document]"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        import json
        result = json.loads(response.text)
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
    Analyze an image using Gemini Vision
    
    Args:
        image_data: Image bytes or PIL Image
        caption: Optional text caption
    
    Returns:
        str: Description of the image and suggested category
    """
    prompt = f"""Analyze this image and determine what it's about.
    
    Caption (if provided): {caption}
    
    Respond in JSON format:
    {{
      "description": "what's in the image",
      "category": "Health/Study/Personal Projects/Skills/Creative/Shopping/Ideas",
      "suggested_title": "short title for this item"
    }}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[prompt, image_data],
            config=types.GenerateContentConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        import json
        return json.loads(response.text)
    
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return {
            "description": "Image analysis failed",
            "category": "Ideas",
            "suggested_title": caption[:50] if caption else "Image"
        }
