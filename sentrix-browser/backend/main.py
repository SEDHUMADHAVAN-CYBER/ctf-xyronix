"""
Sentrix Browser - Agent Core Engine
Local-first agentic browser automation with Ollama integration
"""

import asyncio
import json
import hashlib
import secrets
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import httpx

# Security Configuration
API_KEY_HEADER = APIKeyHeader(name="X-Sentrix-Token")
SENTRIX_HOME = Path.home() / ".sentrix"
TOKEN_FILE = SENTRIX_HOME / "execution_token"

def get_or_create_token() -> str:
    """Generate or retrieve the secure execution token"""
    SENTRIX_HOME.mkdir(parents=True, exist_ok=True)
    
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    
    token = secrets.token_hex(32)
    TOKEN_FILE.write_text(token)
    TOKEN_FILE.chmod(0o600)  # Secure permissions
    return token

EXECUTION_TOKEN = get_or_create_token()

# Database Setup
DB_PATH = SENTRIX_HOME / "tasks.db"

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize the task database"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                objective TEXT NOT NULL,
                status TEXT DEFAULT 'queued',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_at TIMESTAMP,
                result TEXT,
                error TEXT
            )
        """)
        conn.commit()

# Pydantic Models
class TaskRequest(BaseModel):
    objective: str
    scheduled_at: Optional[str] = None

class TaskResponse(BaseModel):
    id: int
    objective: str
    status: str
    created_at: str
    scheduled_at: Optional[str]
    result: Optional[str]

class ChatMessage(BaseModel):
    message: str
    url: Optional[str] = None

class ActionResult(BaseModel):
    success: bool
    action: str
    result: str
    next_state: Optional[str] = None

# Vision-Tree DOM Compression
DOM_COMPRESSION_SCRIPT = """
(function() {
    const interactableElements = ['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'];
    const meaningfulTags = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'SPAN', 'DIV'];
    
    function compressNode(node, idCounter) {
        const result = [];
        
        function walk(element, depth = 0) {
            if (!element || element.nodeType !== 1) return;
            
            const tag = element.tagName;
            const text = element.textContent?.trim().slice(0, 100);
            const attrs = {};
            
            if (interactableElements.includes(tag)) {
                attrs['id'] = idCounter[0]++;
                attrs['type'] = tag.toLowerCase();
                if (element.href) attrs['href'] = element.href;
                if (element.value) attrs['value'] = element.value;
                if (element.placeholder) attrs['placeholder'] = element.placeholder;
                
                result.push({
                    id: attrs['id'],
                    tag: tag.toLowerCase(),
                    text: text || element.innerText?.trim().slice(0, 50),
                    ...attrs
                });
            } else if (meaningfulTags.includes(tag) && text) {
                result.push({
                    tag: tag.toLowerCase(),
                    text: text
                });
            }
            
            Array.from(element.children).forEach(child => walk(child, depth + 1));
        }
        
        walk(element);
        return result;
    }
    
    return JSON.stringify(compressNode(document.body, [1]));
})();
"""

class SentrixAgent:
    """Core agent engine for reasoning and acting"""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.model = "llama3.2"  # Default model, configurable
        
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        """Generate response using local Ollama instance"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False
            }
            
            try:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                return response.json()["response"]
            except Exception as e:
                raise HTTPException(status_code=503, detail=f"Ollama service unavailable: {str(e)}")
    
    async def parse_page_layout(self, page) -> Dict[str, Any]:
        """Compress DOM into vision-tree format"""
        compressed = await page.evaluate(DOM_COMPRESSION_SCRIPT)
        return json.loads(compressed) if compressed else []
    
    async def reason_and_act(self, objective: str, page_state: List[Dict], history: List[str]) -> ActionResult:
        """ReAct loop: Reason about state and determine next action"""
        
        system_prompt = """You are Sentrix, an autonomous browser agent. 
        Analyze the current page layout and determine the next action to achieve the objective.
        Available actions: CLICK(id), TYPE(id, text), NAVIGATE(url), SCROLL(direction), EXTRACT(selector)
        Respond ONLY with a JSON object: {"reasoning": "...", "action": "ACTION_TYPE", "target": "id_or_value", "result": "description"}"""
        
        context = f"""
        Objective: {objective}
        Current Page Elements: {json.dumps(page_state[:20])}  # Limit context
        Previous Actions: {json.dumps(history[-5:])}
        
        What is the next action?
        """
        
        response = await self.generate_response(context, system_prompt)
        
        try:
            # Parse the agent's decision
            import re
            json_match = re.search(r'\{[^}]*\}', response, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                return ActionResult(
                    success=True,
                    action=decision.get("action", "UNKNOWN"),
                    result=decision.get("reasoning", ""),
                    next_state=decision.get("target")
                )
            else:
                return ActionResult(success=False, action="PARSE_ERROR", result=response)
        except Exception as e:
            return ActionResult(success=False, action="ERROR", result=str(e))
    
    async def execute_task(self, objective: str, playwright_browser, max_steps: int = 20) -> str:
        """Execute a complete task using ReAct loop"""
        context = playwright_browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        history = []
        result_log = []
        
        try:
            for step in range(max_steps):
                # Get current page state
                page_state = await self.parse_page_layout(page)
                
                # Reason and decide next action
                decision = await self.reason_and_act(objective, page_state, history)
                
                if not decision.success:
                    result_log.append(f"Step {step + 1}: Failed - {decision.result}")
                    break
                
                # Execute the action
                action_result = await self._execute_action(page, decision.action, decision.next_state)
                history.append(f"{decision.action}: {decision.next_state}")
                result_log.append(f"Step {step + 1}: {action_result}")
                
                # Check if objective is complete
                if "COMPLETE" in action_result or "SUCCESS" in action_result:
                    return "\n".join(result_log)
                
                await asyncio.sleep(0.5)  # Stabilization delay
            
            return f"Task completed after {max_steps} steps:\n" + "\n".join(result_log)
            
        except Exception as e:
            return f"Task failed: {str(e)}"
        finally:
            await context.close()
    
    async def _execute_action(self, page, action_type: str, target: str) -> str:
        """Execute a specific browser action"""
        try:
            if action_type == "NAVIGATE":
                await page.goto(target)
                return f"Navigated to {target}"
            
            elif action_type == "CLICK":
                element_id = int(target)
                # In real implementation, map ID to actual selector
                await page.click(f'[data-sentrix-id="{element_id}"]')
                return f"Clicked element {element_id}"
            
            elif action_type == "TYPE":
                parts = target.split(",", 1)
                element_id = int(parts[0].strip())
                text = parts[1].strip() if len(parts) > 1 else ""
                await page.fill(f'[data-sentrix-id="{element_id}"]', text)
                return f"Typed '{text}' into element {element_id}"
            
            elif action_type == "EXTRACT":
                content = await page.inner_text(target)
                return f"Extracted: {content[:200]}"
            
            elif action_type == "SCROLL":
                if target.lower() == "down":
                    await page.evaluate("window.scrollBy(0, window.innerHeight)")
                elif target.lower() == "up":
                    await page.evaluate("window.scrollBy(0, -window.innerHeight)")
                return f"Scrolled {target}"
            
            else:
                return f"Unknown action: {action_type}"
                
        except Exception as e:
            return f"Action failed: {str(e)}"

# FastAPI Application
app = FastAPI(title="Sentrix Browser Agent Core", version="1.0.0")

# Initialize components
agent = SentrixAgent()
init_database()

# Security dependency
async def verify_token(x_token: str = Security(API_KEY_HEADER)):
    if x_token != EXECUTION_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid execution token")
    return x_token

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "token_active": True}

@app.post("/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest, token: str = Depends(verify_token)):
    """Create a new automation task"""
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tasks (objective, scheduled_at) VALUES (?, ?)",
            (task.objective, task.scheduled_at)
        )
        conn.commit()
        task_id = cursor.lastrowid
        
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        
        return TaskResponse(
            id=row["id"],
            objective=row["objective"],
            status=row["status"],
            created_at=row["created_at"],
            scheduled_at=row["scheduled_at"]
        )

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, token: str = Depends(verify_token)):
    """Get task status"""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return TaskResponse(
            id=row["id"],
            objective=row["objective"],
            status=row["status"],
            created_at=row["created_at"],
            scheduled_at=row["scheduled_at"],
            result=row["result"]
        )

@app.post("/chat")
async def chat_with_agent(message: ChatMessage, token: str = Depends(verify_token)):
    """Chat interface for direct agent interaction"""
    system_prompt = """You are Sentrix, an AI browser assistant. 
    Help users navigate websites and complete tasks. 
    Provide clear, actionable responses."""
    
    context = f"Current URL: {message.url}\nUser: {message.message}"
    response = await agent.generate_response(context, system_prompt)
    
    return {"response": response, "timestamp": datetime.now().isoformat()}

@app.post("/execute")
async def execute_immediate(objective: str, url: str, token: str = Depends(verify_token)):
    """Execute a task immediately on a specific URL"""
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            # Navigate to initial URL
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(url)
            
            result = await agent.execute_task(objective, browser)
            
            return {"success": True, "result": result}
        finally:
            await browser.close()

if __name__ == "__main__":
    import uvicorn
    print(f"Sentrix Agent Core starting...")
    print(f"Execution Token: {EXECUTION_TOKEN[:8]}...")
    print(f"Database: {DB_PATH}")
    uvicorn.run(app, host="127.0.0.1", port=8765)
