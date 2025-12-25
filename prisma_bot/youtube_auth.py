#!/usr/bin/env python3
"""
One-time script to get YouTube refresh token.

Run this locally:
    python youtube_auth.py

It will open a browser, you log in with your Google account,
and it will print the refresh token to add to .env
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

# Your OAuth credentials (set these in .env or as environment variables)
CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")

# Scopes needed (includes upload!)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly"
]

def main():
    print("=" * 50)
    print("YouTube OAuth Setup")
    print("=" * 50)
    print()

    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET first!")
        print()
        print("Add to your .env file:")
        print("YOUTUBE_CLIENT_ID=your-client-id")
        print("YOUTUBE_CLIENT_SECRET=your-client-secret")
        return

    # Create OAuth flow
    client_config = {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    print("Opening browser for Google login...")
    print("Log in with the account that owns the YouTube channel.")
    print()

    # Run local server to handle OAuth callback
    credentials = flow.run_local_server(port=8080)

    print()
    print("=" * 50)
    print("SUCCESS! Add this to your .env file:")
    print("=" * 50)
    print()
    print(f"YOUTUBE_CLIENT_ID={CLIENT_ID}")
    print(f"YOUTUBE_CLIENT_SECRET={CLIENT_SECRET}")
    print(f"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}")
    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
