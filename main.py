import logging
import os
import json
from pathlib import Path
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GOOGLE_TASKS_AVAILABLE = True
except ImportError:
    GOOGLE_TASKS_AVAILABLE = False

logger = logging.getLogger(__name__)

# OAuth2 scopes for Google Tasks API
SCOPES = ['https://www.googleapis.com/auth/tasks']


class OAuth2TokenManager:
    
    def __init__(self, credentials_path, token_storage_path):
        self.credentials_path = Path(credentials_path).expanduser()
        self.token_storage_path = Path(token_storage_path).expanduser()
        self.token_storage_path.mkdir(parents=True, exist_ok=True)
        self.token_file = self.token_storage_path / "token.json"
        
    def get_credentials(self):
        """Get valid OAuth2 credentials for Google Tasks API"""
        if not GOOGLE_TASKS_AVAILABLE:
            return None
            
        if not self.credentials_path.exists():
            logger.error(f"Credentials file not found: {self.credentials_path}")
            return None
            
        creds = None
        
        # Load existing token if available
        if self.token_file.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            except Exception as e:
                logger.error(f"Error loading existing credentials: {e}")
        
        # If no valid credentials, run OAuth2 flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logger.error(f"Error in OAuth2 flow: {e}")
                    return None
            
            # Save credentials for future use
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                os.chmod(self.token_file, 0o600)
            except Exception as e:
                logger.error(f"Error saving credentials: {e}")
        
        return creds


class GoogleTasksExtension(Extension):
    
    def __init__(self):
        super(GoogleTasksExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.service = None
        self.token_manager = None
        
    def _init_token_manager(self):
        if self.token_manager is None:
            credentials_path = self.preferences.get('credentials_path', '~/.config/ulauncher_tasks/credentials.json')
            token_storage_path = self.preferences.get('token_storage_path', '~/.cache/ulauncher_tasks')
            self.token_manager = OAuth2TokenManager(credentials_path, token_storage_path)
    
    def _sanitize_input(self, text):
        if not text:
            return ""
        return text.strip()[:1000]
    
    def get_tasks_service(self):
        """Get authenticated Google Tasks service"""
        if not GOOGLE_TASKS_AVAILABLE:
            return None
            
        if self.service is None:
            self._init_token_manager()
            creds = self.token_manager.get_credentials()
            
            if creds:
                try:
                    self.service = build('tasks', 'v1', credentials=creds)
                except Exception as e:
                    logger.error(f"Error building Tasks service: {e}")
                    return None
        
        return self.service
    
    def get_default_tasklist_id(self):
        """Get the default task list ID"""
        service = self.get_tasks_service()
        if not service:
            return None
            
        try:
            results = service.tasklists().list().execute()
            tasklists = results.get('items', [])
            if tasklists:
                return tasklists[0]['id']
        except Exception as e:
            logger.error(f"Error getting default tasklist: {e}")
        
        return None
    
    def add_task_to_google_tasks(self, task_text):
        """Add a task to Google Tasks"""
        service = self.get_tasks_service()
        if not service:
            return False, "Google Tasks service not available"
        
        sanitized_text = self._sanitize_input(task_text)
        if not sanitized_text:
            return False, "Invalid task text"
        
        # Get tasklist ID from preferences or use default
        tasklist_id = self.preferences.get('tasklist_id', '')
        if not tasklist_id:
            tasklist_id = self.get_default_tasklist_id()
            
        if not tasklist_id:
            return False, "No task list available"
        
        task = {
            'title': sanitized_text,
            'status': 'needsAction'
        }
        
        try:
            result = service.tasks().insert(tasklist=tasklist_id, body=task).execute()
            logger.info("Task added to Google Tasks successfully")
            return True, "Task added successfully"
        except Exception as e:
            logger.error(f"Error adding task to Google Tasks: {e}")
            return False, "Failed to add task"


class KeywordQueryEventListener(EventListener):
    
    def on_event(self, event, extension):
        items = []
        
        if not GOOGLE_TASKS_AVAILABLE:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Google Tasks API not available',
                description='Please install: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib',
                on_enter=CopyToClipboardAction('pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib')
            ))
            return RenderResultListAction(items)
        
        credentials_path = extension.preferences.get('credentials_path', '')
        if not credentials_path or not Path(credentials_path).expanduser().exists():
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='OAuth2 credentials required',
                description='Please download credentials.json from Google Cloud Console and set path in preferences',
                on_enter=HideWindowAction()
            ))
            return RenderResultListAction(items)
        
        query = event.get_argument() or ''
        
        if query:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=f'Add to Google Tasks: {query}',
                description='Press Enter to add this task to Google Tasks',
                on_enter=ItemEnterEvent(query)
            ))
        else:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Add task to Google Tasks',
                description='Type your task and press Enter',
                on_enter=HideWindowAction()
            ))
        
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    
    def on_event(self, event, extension):
        task_text = event.get_data()
        
        if task_text:
            success, message = extension.add_task_to_google_tasks(task_text)
            if success:
                logger.info("Task added successfully")
            else:
                logger.error("Failed to add task")
        
        return HideWindowAction()


if __name__ == '__main__':
    GoogleTasksExtension().run()