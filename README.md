# Google Keep Todo - Ulauncher Extension

Add todo items to Google Keep directly from Ulauncher.

## Installation

1. Clone or download this extension to your Ulauncher extensions directory
2. Install the required Python package:
   ```bash
   pip install gkeepapi
   ```
3. In Ulauncher preferences, configure the extension with:
   - Your Google email address
   - A Google App Password (generate from your Google Account settings)

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

## Features

- Add todo items directly to Google Keep
- Simple keyword-based interface
- Secure authentication using App Passwords

## Requirements

- Python 3.6+
- gkeepapi library
- Google account with App Password enabled# keep
