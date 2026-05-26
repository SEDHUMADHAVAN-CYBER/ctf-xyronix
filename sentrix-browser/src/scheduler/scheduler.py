"""
Sentrix Browser Scheduler Module
Task scheduling and automated execution
"""

import asyncio
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from ..config import get_settings
import json
from pathlib import Path


class Task:
    """Represents a scheduled task"""
    
    def __init__(self, task_id: str, description: str, trigger_type: str, 
                 trigger_value: str, priority: str = 'medium', enabled: bool = True):
        self.task_id = task_id
        self.description = description
        self.trigger_type = trigger_type  # 'cron', 'interval', 'date'
        self.trigger_value = trigger_value
        self.priority = priority
        self.enabled = enabled
        self.created_at = datetime.now()
        self.last_run = None
        self.next_run = None
        self.execution_count = 0
        
    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'trigger_value': self.trigger_value,
            'priority': self.priority,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'execution_count': self.execution_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        task = cls(
            task_id=data['task_id'],
            description=data['description'],
            trigger_type=data['trigger_type'],
            trigger_value=data['trigger_value'],
            priority=data.get('priority', 'medium'),
            enabled=data.get('enabled', True)
        )
        task.created_at = datetime.fromisoformat(data['created_at'])
        task.last_run = datetime.fromisoformat(data['last_run']) if data.get('last_run') else None
        task.next_run = datetime.fromisoformat(data['next_run']) if data.get('next_run') else None
        task.execution_count = data.get('execution_count', 0)
        return task


class TaskScheduler:
    """Manages task scheduling and execution"""
    
    def __init__(self, executor_callback: Callable):
        self.settings = get_settings()
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Task] = {}
        self.executor_callback = executor_callback
        self.storage_file = Path("~/.sentrix/tasks.json").expanduser()
        
    def start(self):
        """Start the scheduler"""
        if self.settings.scheduler_enabled:
            self.scheduler.start()
            self._load_tasks()
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        self._save_tasks()
    
    def _load_tasks(self):
        """Load tasks from storage"""
        if self.storage_file.exists():
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for task_data in data:
                    task = Task.from_dict(task_data)
                    self.tasks[task.task_id] = task
                    if task.enabled:
                        self._schedule_task(task)
    
    def _save_tasks(self):
        """Save tasks to storage"""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_file, 'w') as f:
            json.dump([task.to_dict() for task in self.tasks.values()], f, indent=2)
    
    def _parse_trigger(self, trigger_type: str, trigger_value: str):
        """Parse trigger configuration"""
        if trigger_type == 'cron':
            # Format: "minute hour day month day_of_week" or standard cron
            parts = trigger_value.split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
        elif trigger_type == 'interval':
            # Format: "seconds=X" or "minutes=X" or "hours=X"
            if '=' in trigger_value:
                unit, value = trigger_value.split('=')
                value = int(value)
                if unit == 'seconds':
                    return IntervalTrigger(seconds=value)
                elif unit == 'minutes':
                    return IntervalTrigger(minutes=value)
                elif unit == 'hours':
                    return IntervalTrigger(hours=value)
        elif trigger_type == 'date':
            # Format: ISO datetime string
            run_time = datetime.fromisoformat(trigger_value)
            return DateTrigger(run_date=run_time)
        
        raise ValueError(f"Invalid trigger configuration: {trigger_type} - {trigger_value}")
    
    def _schedule_task(self, task: Task):
        """Schedule a task in the APScheduler"""
        try:
            trigger = self._parse_trigger(task.trigger_type, task.trigger_value)
            
            def task_wrapper():
                asyncio.create_task(self._execute_task(task))
            
            job = self.scheduler.add_job(
                task_wrapper,
                trigger=trigger,
                id=task.task_id,
                replace_existing=True
            )
            
            task.next_run = job.next_run_time
            
        except Exception as e:
            raise Exception(f"Failed to schedule task {task.task_id}: {str(e)}")
    
    async def _execute_task(self, task: Task):
        """Execute a scheduled task"""
        try:
            task.last_run = datetime.now()
            task.execution_count += 1
            
            result = await self.executor_callback(task.description)
            
            task.next_run = self.scheduler.get_job(task.task_id).next_run_time if self.scheduler.get_job(task.task_id) else None
            
            self._save_tasks()
            
            return result
        except Exception as e:
            print(f"Task {task.task_id} failed: {str(e)}")
            raise
    
    def add_task(self, description: str, schedule: str, priority: str = 'medium') -> Task:
        """Add a new scheduled task
        
        Args:
            description: Task description
            schedule: Schedule in format "type:value" 
                     Examples: "cron:0 9 * * *" (daily at 9am),
                              "interval:minutes=30" (every 30 minutes),
                              "date:2024-01-15T10:00:00" (specific time)
            priority: Task priority (low, medium, high)
        """
        import uuid
        
        if ':' not in schedule:
            raise ValueError("Schedule must be in format 'type:value'")
        
        trigger_type, trigger_value = schedule.split(':', 1)
        
        task_id = str(uuid.uuid4())
        task = Task(
            task_id=task_id,
            description=description,
            trigger_type=trigger_type,
            trigger_value=trigger_value,
            priority=priority
        )
        
        self.tasks[task_id] = task
        
        if task.enabled:
            self._schedule_task(task)
            self._save_tasks()
        
        return task
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.scheduler.remove_job(task_id, misfire_grace_time=None)
            self._save_tasks()
            return True
        return False
    
    def pause_task(self, task_id: str) -> bool:
        """Pause a task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.enabled = False
            self.scheduler.pause_job(task_id)
            self._save_tasks()
            return True
        return False
    
    def resume_task(self, task_id: str) -> bool:
        """Resume a paused task"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.enabled = True
            self._schedule_task(task)
            self._save_tasks()
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID"""
        return self.tasks.get(task_id)
    
    def list_tasks(self) -> List[Task]:
        """List all tasks"""
        return list(self.tasks.values())
    
    def get_next_run(self, task_id: str) -> Optional[datetime]:
        """Get next run time for a task"""
        job = self.scheduler.get_job(task_id)
        return job.next_run_time if job else None
