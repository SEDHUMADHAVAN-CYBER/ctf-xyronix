"""
Sentrix Browser - Background Scheduler Service
Handles scheduled tasks and background automation
"""

import asyncio
from datetime import datetime
from pathlib import Path
import sqlite3
from contextlib import contextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

SENTRIX_HOME = Path.home() / ".sentrix"
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

class SentrixScheduler:
    """Background task scheduler for automated browser tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.agent_core_url = "http://127.0.0.1:8765"
        
    async def execute_scheduled_task(self, task_id: int, objective: str):
        """Execute a scheduled task in headless mode"""
        import httpx
        
        # Update status to running
        with get_db() as conn:
            conn.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                ("running", task_id)
            )
            conn.commit()
        
        try:
            # Call the agent core to execute the task
            async with httpx.AsyncClient(timeout=300.0) as client:
                response = await client.post(
                    f"{self.agent_core_url}/execute",
                    json={"objective": objective, "url": "https://www.google.com"},
                    headers={"X-Sentrix-Token": self._get_token()}
                )
                
                result = response.json()
                
                # Update task status
                with get_db() as conn:
                    if result.get("success"):
                        conn.execute(
                            "UPDATE tasks SET status = ?, result = ? WHERE id = ?",
                            ("completed", result.get("result"), task_id)
                        )
                    else:
                        conn.execute(
                            "UPDATE tasks SET status = ?, error = ? WHERE id = ?",
                            ("failed", str(result), task_id)
                        )
                    conn.commit()
                    
        except Exception as e:
            with get_db() as conn:
                conn.execute(
                    "UPDATE tasks SET status = ?, error = ? WHERE id = ?",
                    ("failed", str(e), task_id)
                )
                conn.commit()
    
    def _get_token(self) -> str:
        """Retrieve execution token"""
        token_file = SENTRIX_HOME / "execution_token"
        if token_file.exists():
            return token_file.read_text().strip()
        return ""
    
    def schedule_task(self, task_id: int, objective: str, scheduled_at: str):
        """Schedule a task for future execution"""
        try:
            run_time = datetime.fromisoformat(scheduled_at)
            
            trigger = DateTrigger(run_date=run_time)
            
            self.scheduler.add_job(
                self.execute_scheduled_task,
                trigger=trigger,
                args=[task_id, objective],
                id=f"task_{task_id}"
            )
            
            print(f"Scheduled task {task_id} for {run_time}")
            
        except Exception as e:
            print(f"Failed to schedule task {task_id}: {e}")
    
    def load_pending_tasks(self):
        """Load all pending tasks from database and schedule them"""
        with get_db() as conn:
            rows = conn.execute(
                "SELECT id, objective, scheduled_at FROM tasks WHERE status = 'queued' AND scheduled_at IS NOT NULL"
            ).fetchall()
            
            for row in rows:
                self.schedule_task(row["id"], row["objective"], row["scheduled_at"])
    
    def start(self):
        """Start the scheduler"""
        self.load_pending_tasks()
        self.scheduler.start()
        print("Sentrix Scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()

# Standalone scheduler service
if __name__ == "__main__":
    scheduler = SentrixScheduler()
    
    try:
        scheduler.start()
        # Keep running
        while True:
            asyncio.run(asyncio.sleep(60))
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("Scheduler stopped")
