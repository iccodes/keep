# Google Tasks Todo - Ulauncher Extension

Add todo items to Google Tasks directly from Ulauncher using OAuth2 authentication.

## Installation

1. Clone or download this extension to your Ulauncher extensions directory
2. Install the required Python packages:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
   ```

## Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Tasks API:
   - Go to "APIs & Services" > "Library"
   - Search for "Tasks API" and enable it
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application" as the application type
   - Download the credentials.json file
5. Place the credentials.json file in `~/.config/ulauncher_tasks/credentials.json`

## Extension Configuration

In Ulauncher preferences, configure the extension with:
- **Credentials File Path**: Path to your downloaded credentials.json file
- **Token Storage Path**: Where to store OAuth2 tokens (defaults to `~/.cache/ulauncher_tasks`)
- **Task List ID**: Optional - specify a particular task list ID (uses default list if empty)

## Usage

1. Open Ulauncher
2. Type `task` (or your configured keyword)
3. Type your task
4. Press Enter to add it to Google Tasks

## First-Time Authentication

On first use, the extension will:
1. Open your default web browser
2. Ask you to log in to Google
3. Request permission to access your Google Tasks
4. Store the OAuth2 token securely for future use

## Security Features

- **OAuth2 Authentication**: Uses Google's secure OAuth2 flow instead of app passwords
- **Limited Scopes**: Only requests access to Google Tasks (not your entire Google account)
- **Secure Token Storage**: OAuth2 tokens are stored with restricted file permissions
- **Input Sanitization**: All user inputs are sanitized and length-limited
- **Minimal Logging**: No sensitive information is logged

## Features

- Add tasks directly to Google Tasks
- OAuth2 authentication (no app passwords required)
- Automatic token refresh
- Uses default task list or specify custom list
- Simple keyword-based interface
- Secure credential management

## Requirements

- Python 3.6+
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- Google account
- Google Cloud Console project with Tasks API enabled

## Troubleshooting

- **"OAuth2 credentials required"**: Download credentials.json from Google Cloud Console
- **"Google Tasks API not available"**: Install required packages with pip
- **Authentication fails**: Delete token.json and re-authenticate
- **No task list available**: Check that you have at least one task list in Google Tasks

## OAuth2 vs App Passwords

This extension uses OAuth2 authentication, which is more secure than app passwords because:
- Limited scope access (only Google Tasks)
- Tokens can be revoked from Google Account settings
- No need to store passwords
- Follows Google's recommended authentication practices