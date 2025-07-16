# Google Keep Todo - Ulauncher Extension

Add todo items to Google Keep directly from Ulauncher.

## Installation

1. Clone or download this extension to your Ulauncher extensions directory
2. Install the required Python packages:
   ```bash
   pip install gkeepapi cryptography
   ```
3. In Ulauncher preferences, configure the extension with:
   - Your Google email address
   - A Google App Password (generate from your Google Account settings)
   - Optional: Custom token storage path (defaults to ~/.cache/ulauncher_keep)

## Usage

1. Open Ulauncher
2. Type `keep` (or your configured keyword)
3. Type your todo item
4. Press Enter to add it to Google Keep

## Authentication

This extension uses the unofficial `gkeepapi` library. You'll need to:

1. Go to your Google Account settings
2. Enable 2-factor authentication
3. Generate an App Password specifically for this extension
4. Use that App Password (not your regular Google password) in the extension preferences

## Security Features

- **Encrypted Token Storage**: Authentication tokens are encrypted using PBKDF2 with SHA-256
- **Input Sanitization**: All user inputs are sanitized and length-limited
- **Secure File Permissions**: Token files are created with 0600 permissions (user-only access)
- **Minimal Logging**: Sensitive information is not logged to prevent exposure
- **Token Reuse**: Encrypted tokens are reused to minimize authentication requests

## Features

- Add todo items directly to Google Keep
- Simple keyword-based interface
- Secure authentication using App Passwords
- Encrypted local token storage
- Input validation and sanitization

## Requirements

- Python 3.6+
- gkeepapi library
- cryptography library
- Google account with App Password enabled# keep
