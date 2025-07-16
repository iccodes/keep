import logging
import os
import json
import base64
from pathlib import Path
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

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecureTokenManager:
    
    def __init__(self, storage_path):
        self.storage_path = Path(storage_path).expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.token_file = self.storage_path / "tokens.enc"
        
    def _get_key(self, password):
        if not CRYPTO_AVAILABLE:
            return None
        salt = b'ulauncher_keep_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return Fernet(key)
    
    def store_token(self, token_data, password):
        if not CRYPTO_AVAILABLE:
            return False
        try:
            cipher = self._get_key(password)
            if cipher is None:
                return False
            encrypted_data = cipher.encrypt(json.dumps(token_data).encode())
            with open(self.token_file, 'wb') as f:
                f.write(encrypted_data)
            os.chmod(self.token_file, 0o600)
            return True
        except Exception as e:
            logger.error(f"Failed to store token: {e}")
            return False
    
    def load_token(self, password):
        if not CRYPTO_AVAILABLE or not self.token_file.exists():
            return None
        try:
            cipher = self._get_key(password)
            if cipher is None:
                return None
            with open(self.token_file, 'rb') as f:
                encrypted_data = f.read()
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
            return None


class GoogleKeepExtension(Extension):
    
    def __init__(self):
        super(GoogleKeepExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.keep = None
        self.authenticated = False
        self.token_manager = None
        
    def _init_token_manager(self):
        if self.token_manager is None:
            storage_path = self.preferences.get('token_storage_path', '~/.cache/ulauncher_keep')
            self.token_manager = SecureTokenManager(storage_path)
    
    def _sanitize_input(self, text):
        if not text:
            return ""
        return text.strip()[:500]
    
    def get_keep_instance(self):
        if not GKEEP_AVAILABLE:
            return None
            
        if self.keep is None:
            self.keep = gkeepapi.Keep()
            
        if not self.authenticated:
            email = self.preferences.get('google_email', '')
            password = self.preferences.get('app_password', '')
            
            if not email or not password:
                return None
                
            email = self._sanitize_input(email)
            if not email:
                return None
            
            self._init_token_manager()
            
            try:
                stored_token = self.token_manager.load_token(password)
                if stored_token and self.keep.resume(email, stored_token.get('master_token', '')):
                    self.authenticated = True
                    logger.info("Resumed session with stored token")
                else:
                    success = self.keep.login(email, password)
                    if success:
                        self.authenticated = True
                        master_token = self.keep.getMasterToken()
                        if master_token:
                            self.token_manager.store_token({'master_token': master_token}, password)
                        logger.info("Successfully authenticated with Google Keep")
                    else:
                        logger.error("Failed to authenticate with Google Keep")
            except Exception as e:
                logger.error(f"Authentication error occurred")
                    
        return self.keep if self.authenticated else None
        
    def add_todo_to_keep(self, todo_text):
        keep = self.get_keep_instance()
        if keep is None:
            return False, "Google Keep not available or not authenticated"
        
        sanitized_text = self._sanitize_input(todo_text)
        if not sanitized_text:
            return False, "Invalid todo text"
            
        try:
            note = keep.createNote('Todo', sanitized_text)
            keep.sync()
            logger.info("Todo added to Google Keep successfully")
            return True, "Todo added successfully"
        except Exception as e:
            logger.error("Error adding todo to Google Keep")
            return False, "Failed to add todo"


class KeywordQueryEventListener(EventListener):
    
    def on_event(self, event, extension):
        items = []
        
        if not GKEEP_AVAILABLE:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Google Keep API not available',
                description='Please install: pip install gkeepapi cryptography',
                on_enter=CopyToClipboardAction('pip install gkeepapi cryptography')
            ))
            return RenderResultListAction(items)
        
        if not CRYPTO_AVAILABLE:
            items.append(ExtensionResultItem(
                icon='images/icon.png',
                name='Cryptography library not available',
                description='Please install: pip install cryptography',
                on_enter=CopyToClipboardAction('pip install cryptography')
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
                logger.info("Todo added successfully")
            else:
                logger.error("Failed to add todo")
        
        return HideWindowAction()


if __name__ == '__main__':
    GoogleKeepExtension().run()