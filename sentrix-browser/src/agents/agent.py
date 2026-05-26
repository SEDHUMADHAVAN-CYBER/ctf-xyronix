"""
Sentrix Browser AI Agent Module
Handles AI-powered decision making and task execution using Ollama
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from ollama import Client
from ..config import get_settings


class SentrixAgent:
    """AI Agent for autonomous web navigation and task completion"""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = Client(host=self.settings.ollama_host)
        self.conversation_history: List[Dict] = []
        
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI agent"""
        return """You are Sentrix, an advanced AI browser agent. Your purpose is to help users complete tasks by autonomously navigating websites, extracting information, and performing actions.

Capabilities:
- Navigate to URLs and browse websites
- Click buttons, fill forms, and interact with web elements
- Extract and summarize information from web pages
- Schedule and execute recurring tasks
- Connect to Gmail and other services securely

Guidelines:
1. Always be precise in your actions
2. Verify information before reporting
3. Handle errors gracefully
4. Respect user privacy and security
5. Provide clear, concise summaries of completed tasks

When given a task, break it down into steps and execute them systematically."""

    async def chat(self, message: str, context: str = "") -> str:
        """Send a message to the AI and get a response"""
        self.conversation_history.append({
            'role': 'user',
            'content': f"Context: {context}\n\nUser: {message}" if context else f"User: {message}"
        })
        
        messages = [
            {'role': 'system', 'content': self._get_system_prompt()},
            *self.conversation_history
        ]
        
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.settings.browser_model,
            messages=messages
        )
        
        assistant_message = response['message']['content']
        self.conversation_history.append({
            'role': 'assistant',
            'content': assistant_message
        })
        
        return assistant_message
    
    async def analyze_page(self, page_content: str, url: str) -> Dict[str, Any]:
        """Analyze a web page and extract relevant information"""
        prompt = f"""Analyze this web page and provide:
1. Page purpose and main content
2. Key interactive elements (buttons, forms, links)
3. Relevant data points
4. Suggested next actions

URL: {url}
Content: {page_content[:5000]}"""  # Limit content to avoid token limits
        
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.settings.navigation_model,
            messages=[
                {'role': 'system', 'content': 'You are a web page analyzer. Extract structured information from web pages.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        
        return {
            'analysis': response['message']['content'],
            'url': url
        }
    
    async def plan_task(self, task_description: str) -> List[Dict[str, str]]:
        """Create a step-by-step plan for completing a task"""
        prompt = f"""Create a detailed step-by-step plan to complete this task:
{task_description}

Format the response as a JSON array of steps, where each step has:
- action: The action to perform (navigate, click, fill, extract, etc.)
- target: The element selector or URL
- description: Human-readable description of the step

Example:
[
  {{"action": "navigate", "target": "https://example.com", "description": "Go to example.com"}},
  {{"action": "click", "target": "#login-btn", "description": "Click login button"}}
]"""
        
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.settings.browser_model,
            messages=[
                {'role': 'system', 'content': 'You are a task planner. Create executable plans for web automation.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        
        # Try to parse as JSON
        try:
            content = response['message']['content']
            # Extract JSON from response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            if start_idx >= 0 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                plan = json.loads(json_str)
                return plan
        except Exception as e:
            # Return a simple plan if JSON parsing fails
            return [
                {"action": "navigate", "target": "about:blank", "description": "Start task execution"},
                {"action": "analyze", "target": "current", "description": "Analyze current situation"}
            ]
    
    async def extract_data(self, page_content: str, query: str) -> str:
        """Extract specific data from page content based on a query"""
        prompt = f"""Extract the following information from this web page content:

Query: {query}
Content: {page_content[:5000]}

Provide only the requested information in a clear, concise format."""
        
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.settings.browser_model,
            messages=[
                {'role': 'system', 'content': 'You are a data extraction specialist. Extract precise information from text.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        
        return response['message']['content']
    
    async def summarize_task_result(self, task_description: str, results: List[Dict]) -> str:
        """Summarize the results of a completed task"""
        prompt = f"""Summarize the results of this completed task:

Task: {task_description}
Results: {json.dumps(results, indent=2)[:3000]}

Provide a clear summary of what was accomplished, key findings, and any important notes."""
        
        response = await asyncio.to_thread(
            self.client.chat,
            model=self.settings.browser_model,
            messages=[
                {'role': 'system', 'content': 'You are a summarization expert. Create clear, concise summaries.'},
                {'role': 'user', 'content': prompt}
            ]
        )
        
        return response['message']['content']
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
