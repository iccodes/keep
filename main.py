import logging
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

try:
    import gkeepapi
    GKEEP_AVAILABLE = True
except ImportError:
    GKEEP_AVAILABLE = False

logger = logging.getLogger(__name__)


class GoogleKeepExtension(Extension):
    
    def __init__(self):
        super(GoogleKeepExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.keep = None
        self.authenticated = False
        
    def get_keep_instance(self):
        if not GKEEP_AVAILABLE:
            return None
            
        if self.keep is None:
            self.keep = gkeepapi.Keep()
            
        if not self.authenticated:
            email = self.preferences.get('google_email', '')
            password = self.preferences.get('app_password', '')
            
            if email and password:
                try:
                    success = self.keep.login(email, password)
                    if success:
                        self.authenticated = True
                        logger.info("Successfully authenticated with Google Keep")
                    else:
                        logger.error("Failed to authenticate with Google Keep")
                except Exception as e:
                    logger.error(f"Authentication error: {e}")
                    
        return self.keep if self.authenticated else None
        
    def add_todo_to_keep(self, todo_text):
        keep = self.get_keep_instance()
        if keep is None:
            return False, "Google Keep not available or not authenticated"
            
        try:
            note = keep.createNote('Todo', todo_text)
            keep.sync()
            logger.info(f"Added todo to Google Keep: {todo_text}")
            return True, "Todo added successfully"
        except Exception as e:
            logger.error(f"Error adding todo to Google Keep: {e}")
            return False, f"Error: {str(e)}"


class KeywordQueryEventListener(EventListener):
    
    def on_event(self, event, extension):
        items = []
        
        if not GKEEP_AVAILABLE:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Google Keep API not available',
                description='Please install gkeepapi: pip install gkeepapi',
                on_enter=CopyToClipboardAction('pip install gkeepapi')
            ))
            return RenderResultListAction(items)
        
        email = extension.preferences.get('google_email', '')
        password = extension.preferences.get('app_password', '')
        
        if not email or not password:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Configuration required',
                description='Please set your Google email and app password in preferences',
                on_enter=HideWindowAction()
            ))
            return RenderResultListAction(items)
        
        query = event.get_argument() or ''
        
        if query:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name=f'Add to Google Keep: {query}',
                description='Press Enter to add this todo to Google Keep',
                on_enter=ItemEnterEvent(query)
            ))
        else:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Add todo to Google Keep',
                description='Type your todo item and press Enter',
                on_enter=HideWindowAction()
            ))
        
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):
    
    def on_event(self, event, extension):
        todo_text = event.get_data()
        
        if todo_text:
            success, message = extension.add_todo_to_keep(todo_text)
            if success:
                logger.info(f"Todo added successfully: {todo_text}")
            else:
                logger.error(f"Failed to add todo: {message}")
        
        return HideWindowAction()


if __name__ == '__main__':
    GoogleKeepExtension().run()