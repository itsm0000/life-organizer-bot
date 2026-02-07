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


MANAGEMENT_PROMPT = """You are an AI assistant. Determine if the user wants to manage existing tasks/items.

Management actions:
- delete: remove an item ("delete the skincare task", "remove gym")
- update_priority: change priority ("make Java high priority", "set vitamins to low")
- complete: mark as done ("mark gym as done", "finished the exam prep")
- query: list/show items ("what tasks in Health?", "show my shopping list")
- none: not a management command - user wants to ADD something new

Respond ONLY with valid JSON:
{
  "intent": "delete" | "update_priority" | "complete" | "query" | "none",
  "target": "search term to find the item (extract key words)",
  "category": "category name if querying by category, else null",
  "new_priority": "High" | "Medium" | "Low" (only for update_priority, else null)
}"""


async def parse_management_intent(message_text: str) -> dict:
    """
    Determine if user wants to manage existing tasks
    Returns intent type and target item
    """
    if not GROQ_API_KEY:
        return {"intent": "none"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": MANAGEMENT_PROMPT},
                        {"role": "user", "content": message_text}
                    ],
                    "temperature": 0.1,  # Low temp for consistent parsing
                    "max_tokens": 200
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"Management parse error: {response.status_code}")
                return {"intent": "none"}
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Strip markdown if present
            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                content = "\n".join(lines)
            
            result = json.loads(content)
            return result
            
    except Exception as e:
        print(f"Management parse error: {e}")
        return {"intent": "none"}


async def ai_match_task(user_request: str, tasks: list) -> dict:
    """
    Use AI to semantically match user's request to the best task from the list.
    Returns the matched task or None if no match found.
    """
    if not GROQ_API_KEY or not tasks:
        return None
    
    # Build a list of tasks with indices for AI to pick from
    task_list = ""
    task_map = {}
    for i, task in enumerate(tasks):
        props = task.get("properties", {})
        title = "Untitled"
        if props.get("Name", {}).get("title"):
            title = props["Name"]["title"][0].get("text", {}).get("content", "Untitled")
        category = props.get("Category", {}).get("select", {}).get("name", "Unknown")
        priority = props.get("Priority", {}).get("select", {}).get("name", "Medium")
        
        task_list += f"{i+1}. {title} (Category: {category}, Priority: {priority})\n"
        task_map[i+1] = task
    
    prompt = f"""The user wants to manage a task. Here are their available tasks:

{task_list}

User's request: "{user_request}"

Which task number (1-{len(tasks)}) is the user most likely referring to?
If no task matches well, respond with 0.

Respond with ONLY a JSON object:
{{"task_number": <number>, "confidence": "high" | "medium" | "low"}}"""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You match user requests to task items. Be accurate."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 100
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"AI match error: {response.status_code}")
                return None
            
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            
            # Strip markdown if present
            if content.startswith("```"):
                lines = content.split("\n")
                lines = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
                content = "\n".join(lines)
            
            result = json.loads(content)
            task_num = result.get("task_number", 0)
            confidence = result.get("confidence", "low")
            
            print(f"AI matched task #{task_num} with {confidence} confidence")
            
            if task_num > 0 and task_num in task_map:
                return task_map[task_num]
            return None
            
    except Exception as e:
        print(f"AI match error: {e}")
        return None


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
    
    # Check if API key is set
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is not set!")
        return {
            "category": "Ideas",
            "type": "Idea",
            "priority": "Low",
            "title": message_text[:50],
            "summary": message_text,
            "suggested_action": "GROQ_API_KEY not configured - review manually"
        }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": CATEGORIZATION_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                print(f"Groq API error: {response.status_code} - {response.text}")
            
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


async def analyze_image(image_bytes: bytes, caption: str = "") -> dict:
    """
    Analyze an image using Groq's Llama 3.2 Vision model
    
    Args:
        image_bytes: Raw image bytes
        caption: Optional text caption from user
    
    Returns:
        dict: Analysis results with description, category, and title
    """
    import base64
    from io import BytesIO
    
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY is not set!")
        return {
            "description": caption or "Image (API key not configured)",
            "category": "Ideas",
            "suggested_title": "Image",
            "priority": "Low",
            "suggested_action": "Review manually"
        }
    
    # Compress image to stay under Groq's 4MB base64 limit
    try:
        from PIL import Image
        
        # Open image
        img = Image.open(BytesIO(image_bytes))
        print(f"Original image: {img.size}, mode: {img.mode}")
        
        # Convert to RGB if necessary (PNG with alpha, etc)
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')
        
        # Resize if too large (max 1024 on longest side for Groq)
        max_size = 1024
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            print(f"Resized image to {new_size}")
        
        # Compress to JPEG
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        compressed_bytes = buffer.getvalue()
        
        print(f"Compressed: {len(image_bytes)} -> {len(compressed_bytes)} bytes")
        image_base64 = base64.b64encode(compressed_bytes).decode("utf-8")
        
    except Exception as e:
        print(f"Image compression failed: {e}")
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    
    print(f"Base64 size: {len(image_base64)} chars (~{len(image_base64) / 1024 / 1024:.2f}MB)")
    
    # Build prompt for vision model
    vision_prompt = """Analyze this image and provide:
1. A brief description of what's in the image
2. The most appropriate category from: Health, Study, Personal Projects, Skills, Creative, Shopping, Ideas
3. A suggested title (max 5 words)
4. Priority: High, Medium, or Low
5. A suggested action

Respond in JSON format:
{
    "description": "brief description",
    "category": "category name",
    "suggested_title": "short title",
    "priority": "priority level",
    "suggested_action": "what to do next"
}"""

    if caption:
        vision_prompt += f"\n\nUser's caption: {caption}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": vision_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500
                },
                timeout=60.0  # Vision can take longer
            )
            
            if response.status_code != 200:
                print(f"Vision API error: {response.status_code} - {response.text}")
                # Fallback to caption-based categorization
                if caption:
                    result = await categorize_message(f"Image with caption: {caption}", has_image=True)
                    return {
                        "description": caption,
                        "category": result["category"],
                        "suggested_title": result["title"],
                        "priority": result["priority"],
                        "suggested_action": result["suggested_action"]
                    }
                return {
                    "description": "Image (vision analysis failed)",
                    "category": "Ideas",
                    "suggested_title": "Image",
                    "priority": "Low",
                    "suggested_action": "Review manually"
                }
            
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Strip markdown code blocks if present
            content = content.strip()
            if content.startswith("```"):
                # Remove opening code fence
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]  # Remove first line
                if lines[-1].strip() == "```":
                    lines = lines[:-1]  # Remove last line
                content = "\n".join(lines)
            
            # Also try to find JSON object in the text
            if not content.startswith("{"):
                # Look for JSON object in the response
                import re
                json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group()
            
            # Parse JSON from response
            result = json.loads(content)
            return result
            
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        # Try to extract info from non-JSON response
        return {
            "description": content if 'content' in dir() else "Image analysis",
            "category": "Ideas",
            "suggested_title": caption[:50] if caption else "Image",
            "priority": "Low",
            "suggested_action": "Review manually"
        }
    except Exception as e:
        print(f"Vision error: {e}")
        # Fallback
        if caption:
            result = await categorize_message(f"Image: {caption}", has_image=True)
            return {
                "description": caption,
                "category": result["category"],
                "suggested_title": result["title"],
                "priority": result["priority"],
                "suggested_action": result.get("suggested_action", "Review")
            }
        return {
            "description": f"Image (error: {str(e)[:50]})",
            "category": "Ideas",
            "suggested_title": "Image",
            "priority": "Low",
            "suggested_action": "Review manually"
        }
