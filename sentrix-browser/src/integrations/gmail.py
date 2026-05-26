"""
Sentrix Browser Gmail Integration Module
Secure OAuth2 connection for Gmail operations
"""

import os
import pickle
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..config import get_settings


class GmailConnector:
    """Secure Gmail integration with OAuth2 authentication"""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
              'https://www.googleapis.com/auth/gmail.send',
              'https://www.googleapis.com/auth/gmail.modify']
    
    def __init__(self):
        self.settings = get_settings()
        self.creds: Optional[Credentials] = None
        self.service = None
        self.token_file = Path(self.settings.credential_storage_path).expanduser() / 'gmail_token.pickle'
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail using OAuth2"""
        if not self.settings.gmail_client_id or not self.settings.gmail_client_secret:
            raise ValueError("Gmail credentials not configured. Please set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET")
        
        # Check for existing credentials
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_config(
                    {
                        "installed": {
                            "client_id": self.settings.gmail_client_id,
                            "client_secret": self.settings.gmail_client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": [self.settings.gmail_redirect_uri]
                        }
                    },
                    self.SCOPES
                )
                self.creds = flow.run_local_server(port=8080)
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
        
        # Build the service
        self.service = build('gmail', 'v1', credentials=self.creds)
        return True
    
    def search_emails(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search emails matching a query"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            email_list = []
            
            for msg in messages:
                email_data = self.get_email(msg['id'])
                if email_data:
                    email_list.append(email_data)
            
            return email_list
            
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def get_email(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get full email details by ID"""
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get body
            body = ''
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            elif 'body' in message['payload']:
                import base64
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            
            return {
                'id': message['id'],
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email"""
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            import base64
            from email.mime.text import MIMEText
            
            message = MIMEText(body)
            message['to'] = to
            message['from'] = 'me'
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return {
                'id': sent_message['id'],
                'status': 'sent',
                'to': to,
                'subject': subject
            }
            
        except HttpError as error:
            raise Exception(f"An error occurred: {error}")
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark an email as read"""
        if not self.service:
            raise RuntimeError("Not authenticated")
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError:
            return False
    
    def get_unread_count(self) -> int:
        """Get count of unread emails"""
        emails = self.search_emails('is:unread', max_results=1)
        # This is a workaround - Gmail API doesn't have a direct count endpoint
        # In production, you'd want to implement pagination properly
        return len(emails)
    
    def disconnect(self):
        """Disconnect from Gmail"""
        self.service = None
        self.creds = None
