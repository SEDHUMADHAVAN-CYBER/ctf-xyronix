"""
Sentrix Browser Core Module
Main browser engine and session management
"""

import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from ..config import get_settings


class SentrixBrowser:
    """Core browser engine for Sentrix Browser"""
    
    def __init__(self):
        self.settings = get_settings()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._playwright = None
        
    async def start(self):
        """Initialize the browser instance"""
        self._playwright = await async_playwright().start()
        
        # Launch browser with appropriate settings
        self.browser = await self._playwright.chromium.launch(
            headless=self.settings.headless_mode,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        # Create browser context with anti-detection
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        self.page = await self.context.new_page()
        return self
    
    async def stop(self):
        """Close the browser and cleanup resources"""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def navigate(self, url: str) -> Page:
        """Navigate to a URL"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        response = await self.page.goto(url, timeout=self.settings.browser_timeout)
        return self.page
    
    async def get_content(self) -> str:
        """Get current page content"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await self.page.content()
    
    async def get_text(self) -> str:
        """Get visible text from current page"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await self.page.inner_text('body')
    
    async def screenshot(self, path: str = None) -> bytes:
        """Take a screenshot of the current page"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        screenshot = await self.page.screenshot(full_page=True, path=path)
        return screenshot
    
    async def click(self, selector: str):
        """Click an element on the page"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.click(selector, timeout=self.settings.browser_timeout)
    
    async def fill(self, selector: str, value: str):
        """Fill an input field"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.fill(selector, value, timeout=self.settings.browser_timeout)
    
    async def type_text(self, selector: str, text: str):
        """Type text into an input field"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        await self.page.type(selector, text, timeout=self.settings.browser_timeout)
    
    async def wait_for_selector(self, selector: str, timeout: int = None):
        """Wait for an element to appear"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        timeout = timeout or self.settings.browser_timeout
        await self.page.wait_for_selector(selector, timeout=timeout)
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in the page context"""
        if not self.page:
            raise RuntimeError("Browser not started")
        
        return await self.page.evaluate(script)
    
    async def get_cookies(self) -> List[Dict]:
        """Get all cookies"""
        if not self.context:
            raise RuntimeError("Browser not started")
        
        return await self.context.cookies()
    
    async def add_cookies(self, cookies: List[Dict]):
        """Add cookies to the browser context"""
        if not self.context:
            raise RuntimeError("Browser not started")
        
        await self.context.add_cookies(cookies)
    
    async def new_tab(self) -> Page:
        """Open a new tab"""
        if not self.context:
            raise RuntimeError("Browser not started")
        
        return await self.context.new_page()
    
    async def close_tab(self, page: Page = None):
        """Close a tab"""
        if page:
            await page.close()
        elif self.page:
            await self.page.close()
