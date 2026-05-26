"""
Sentrix Browser Task Executor Module
Executes AI-generated plans and manages task completion
"""

import asyncio
from typing import Optional, List, Dict, Any
from ..core.browser import SentrixBrowser
from ..agents.agent import SentrixAgent
from ..config import get_settings


class TaskExecutor:
    """Executes tasks autonomously using AI guidance"""
    
    def __init__(self, browser: SentrixBrowser, agent: SentrixAgent):
        self.browser = browser
        self.agent = agent
        self.settings = get_settings()
        self.current_task = None
        self.task_results = []
        
    async def execute_task(self, task_description: str) -> Dict[str, Any]:
        """Execute a complete task from description"""
        self.current_task = task_description
        self.task_results = []
        
        # Generate plan
        plan = await self.agent.plan_task(task_description)
        self.task_results.append({
            'stage': 'planning',
            'plan': plan
        })
        
        # Execute each step
        for i, step in enumerate(plan):
            try:
                result = await self._execute_step(step)
                self.task_results.append({
                    'stage': 'execution',
                    'step_number': i + 1,
                    'step': step,
                    'result': result,
                    'status': 'success'
                })
            except Exception as e:
                self.task_results.append({
                    'stage': 'execution',
                    'step_number': i + 1,
                    'step': step,
                    'error': str(e),
                    'status': 'failed'
                })
                # Continue with next steps if possible
                continue
        
        # Summarize results
        summary = await self.agent.summarize_task_result(task_description, self.task_results)
        
        return {
            'task': task_description,
            'summary': summary,
            'results': self.task_results,
            'completed': True
        }
    
    async def _execute_step(self, step: Dict[str, str]) -> Any:
        """Execute a single step from the plan"""
        action = step.get('action', '').lower()
        target = step.get('target', '')
        description = step.get('description', '')
        
        if action == 'navigate':
            return await self._navigate(target)
        elif action == 'click':
            return await self._click(target)
        elif action == 'fill' or action == 'type':
            value = step.get('value', '')
            return await self._fill(target, value)
        elif action == 'extract':
            query = step.get('query', 'Extract relevant information')
            return await self._extract(query)
        elif action == 'analyze':
            return await self._analyze()
        elif action == 'wait':
            timeout = int(step.get('timeout', 1000))
            return await self._wait(timeout)
        elif action == 'scroll':
            direction = step.get('direction', 'down')
            return await self._scroll(direction)
        else:
            return {'action': action, 'status': 'unknown_action'}
    
    async def _navigate(self, url: str) -> Dict:
        """Navigate to a URL"""
        page = await self.browser.navigate(url)
        await asyncio.sleep(1)  # Wait for page load
        return {
            'action': 'navigate',
            'url': url,
            'title': await page.title() if page else 'Unknown'
        }
    
    async def _click(self, selector: str) -> Dict:
        """Click an element"""
        await self.browser.wait_for_selector(selector)
        await self.browser.click(selector)
        await asyncio.sleep(0.5)
        return {
            'action': 'click',
            'selector': selector,
            'status': 'clicked'
        }
    
    async def _fill(self, selector: str, value: str) -> Dict:
        """Fill an input field"""
        await self.browser.wait_for_selector(selector)
        await self.browser.fill(selector, value)
        return {
            'action': 'fill',
            'selector': selector,
            'value': value,
            'status': 'filled'
        }
    
    async def _extract(self, query: str) -> Dict:
        """Extract information from current page"""
        content = await self.browser.get_text()
        extracted = await self.agent.extract_data(content, query)
        return {
            'action': 'extract',
            'query': query,
            'data': extracted
        }
    
    async def _analyze(self) -> Dict:
        """Analyze current page"""
        content = await self.browser.get_content()
        url = self.browser.page.url if self.browser.page else 'unknown'
        analysis = await self.agent.analyze_page(content, url)
        return {
            'action': 'analyze',
            'analysis': analysis
        }
    
    async def _wait(self, timeout: int) -> Dict:
        """Wait for specified milliseconds"""
        await asyncio.sleep(timeout / 1000)
        return {
            'action': 'wait',
            'timeout': timeout,
            'status': 'waited'
        }
    
    async def _scroll(self, direction: str) -> Dict:
        """Scroll the page"""
        script = f"window.scrollBy(0, {500 if direction == 'down' else -500})"
        await self.browser.evaluate(script)
        return {
            'action': 'scroll',
            'direction': direction,
            'status': 'scrolled'
        }
