"""
Sentrix Browser - Main Entry Point
AI-powered agentic browser with local Ollama integration
"""

import asyncio
import sys
from typing import Optional
from .config import get_settings, setup_directories
from .core.browser import SentrixBrowser
from .agents.agent import SentrixAgent
from .agents.executor import TaskExecutor
from .scheduler.scheduler import TaskScheduler
from .utils.security import get_security_manager


class Sentrix:
    """Main Sentrix Browser class - Unified interface for all functionality"""
    
    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[SentrixBrowser] = None
        self.agent: Optional[SentrixAgent] = None
        self.executor: Optional[TaskExecutor] = None
        self.scheduler: Optional[TaskScheduler] = None
        self.security = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all components"""
        if self._initialized:
            return
        
        # Setup directories
        setup_directories()
        
        # Initialize security
        self.security = get_security_manager(self.settings.encryption_key)
        
        # Initialize browser
        self.browser = SentrixBrowser()
        await self.browser.start()
        
        # Initialize AI agent
        self.agent = SentrixAgent()
        
        # Initialize task executor
        self.executor = TaskExecutor(self.browser, self.agent)
        
        # Initialize scheduler
        self.scheduler = TaskScheduler(self.execute_task)
        self.scheduler.start()
        
        self._initialized = True
    
    async def shutdown(self):
        """Shutdown all components gracefully"""
        if self.scheduler:
            self.scheduler.stop()
        if self.browser:
            await self.browser.stop()
        self._initialized = False
    
    async def chat(self, message: str) -> str:
        """Chat with the AI assistant"""
        if not self.agent:
            raise RuntimeError("Sentrix not initialized. Call initialize() first")
        
        return await self.agent.chat(message)
    
    async def execute_task(self, task_description: str) -> dict:
        """Execute a task autonomously"""
        if not self.executor:
            raise RuntimeError("Sentrix not initialized. Call initialize() first")
        
        return await self.executor.execute_task(task_description)
    
    async def navigate(self, url: str):
        """Navigate to a URL"""
        if not self.browser:
            raise RuntimeError("Sentrix not initialized. Call initialize() first")
        
        return await self.browser.navigate(url)
    
    async def schedule_task(self, description: str, schedule: str, priority: str = 'medium'):
        """Schedule a recurring task"""
        if not self.scheduler:
            raise RuntimeError("Sentrix not initialized. Call initialize() first")
        
        return self.scheduler.add_task(description, schedule, priority)
    
    def list_scheduled_tasks(self):
        """List all scheduled tasks"""
        if not self.scheduler:
            raise RuntimeError("Sentrix not initialized. Call initialize() first")
        
        return self.scheduler.list_tasks()
    
    async def connect_gmail(self):
        """Connect to Gmail (returns connector instance)"""
        from .integrations.gmail import GmailConnector
        
        gmail = GmailConnector()
        gmail.authenticate()
        return gmail


async def main():
    """Main entry point for Sentrix Browser"""
    print("=" * 60)
    print("  SENTRIX BROWSER - AI Agentic Browser")
    print("  Powered by Local Ollama Models")
    print("=" * 60)
    print()
    
    sentrix = Sentrix()
    
    try:
        # Initialize
        print("Initializing Sentrix Browser...")
        await sentrix.initialize()
        print("✓ Initialization complete")
        print()
        
        # Interactive mode
        print("Commands:")
        print("  /chat <message>     - Chat with AI")
        print("  /task <description> - Execute a task")
        print("  /navigate <url>     - Navigate to URL")
        print("  /schedule <desc> <schedule> - Schedule a task")
        print("  /tasks              - List scheduled tasks")
        print("  /gmail              - Connect to Gmail")
        print("  /quit               - Exit Sentrix")
        print()
        
        while True:
            try:
                user_input = input("Sentrix> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("Shutting down Sentrix Browser...")
                    break
                
                elif user_input.startswith('/chat '):
                    message = user_input[6:]
                    response = await sentrix.chat(message)
                    print(f"\nSentrix: {response}\n")
                
                elif user_input.startswith('/task '):
                    task_desc = user_input[6:]
                    print(f"Executing task: {task_desc}")
                    result = await sentrix.execute_task(task_desc)
                    print(f"\nTask Summary:\n{result['summary']}\n")
                
                elif user_input.startswith('/navigate '):
                    url = user_input[10:]
                    print(f"Navigating to: {url}")
                    await sentrix.navigate(url)
                    print("Navigation complete\n")
                
                elif user_input.startswith('/schedule '):
                    parts = user_input[10:].split(' ', 1)
                    if len(parts) < 2:
                        print("Usage: /schedule <description> <schedule>")
                        print("Example: /schedule 'Check emails' 'cron:0 9 * * *'")
                        continue
                    
                    desc, schedule = parts
                    task = await sentrix.schedule_task(desc, schedule)
                    print(f"Scheduled task: {task.task_id}")
                    print(f"Description: {task.description}")
                    print(f"Schedule: {task.trigger_type}:{task.trigger_value}\n")
                
                elif user_input == '/tasks':
                    tasks = sentrix.list_scheduled_tasks()
                    if not tasks:
                        print("No scheduled tasks\n")
                    else:
                        print("\nScheduled Tasks:")
                        for task in tasks:
                            status = "✓" if task.enabled else "✗"
                            print(f"  {status} [{task.task_id[:8]}] {task.description}")
                            print(f"      Schedule: {task.trigger_type}:{task.trigger_value}")
                            print(f"      Next run: {task.next_run}\n")
                
                elif user_input == '/gmail':
                    print("Connecting to Gmail...")
                    try:
                        gmail = await sentrix.connect_gmail()
                        print("✓ Gmail connected successfully")
                        
                        # Demo: Get unread count
                        unread = gmail.get_unread_count()
                        print(f"Unread emails: {unread}\n")
                    except Exception as e:
                        print(f"Gmail connection failed: {e}\n")
                
                else:
                    print(f"Unknown command: {user_input}")
                    print("Type /help for available commands\n")
                    
            except KeyboardInterrupt:
                print("\nInterrupted. Type /quit to exit.\n")
            except Exception as e:
                print(f"Error: {e}\n")
    
    finally:
        await sentrix.shutdown()
        print("Sentrix Browser closed.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
