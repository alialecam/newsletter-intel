"""Gmail API integration for fetching newsletter emails."""

import os
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes - readonly access to messages
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

# Paths
CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"
TOKEN_PATH = CREDENTIALS_DIR / "token.json"
CLIENT_SECRET_PATH = CREDENTIALS_DIR / "client_secret.json"


class GmailFetcher:
    """Fetches newsletter emails from Gmail using OAuth2."""

    def __init__(self, config: dict):
        """
        Initialize the Gmail fetcher.

        Args:
            config: Configuration dict with gmail settings
        """
        self.config = config
        self.gmail_config = config.get("gmail", {})
        self.sender_query = self.gmail_config.get("sender_query", "")
        self.label = self.gmail_config.get("label", "newsletters")
        self.service = None

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.

        Returns:
            True if authentication successful, False otherwise
        """
        creds = None

        # Load existing token if available
        if TOKEN_PATH.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

        # Refresh or get new credentials if needed
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None

            if not creds:
                if not CLIENT_SECRET_PATH.exists():
                    print(f"Error: {CLIENT_SECRET_PATH} not found.")
                    print("Please download OAuth credentials from Google Cloud Console.")
                    print("1. Go to https://console.cloud.google.com/apis/credentials")
                    print("2. Create OAuth 2.0 Client ID (Desktop app)")
                    print("3. Download and save as credentials/client_secret.json")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(CLIENT_SECRET_PATH), SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for future runs
            CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        self.service = build("gmail", "v1", credentials=creds)
        return True

    def _get_label_id(self, label_name: str) -> Optional[str]:
        """
        Get the Gmail label ID for a given label name.

        Args:
            label_name: Name of the label to find

        Returns:
            Label ID if found, None otherwise
        """
        try:
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            for label in labels:
                if label["name"].lower() == label_name.lower():
                    return label["id"]

            return None
        except HttpError as e:
            print(f"Error fetching labels: {e}")
            return None

    def fetch_emails(
        self, since_date: Optional[datetime] = None, max_results: int = 100
    ) -> list[dict]:
        """
        Fetch newsletter emails using dual-source approach.

        Fetches from:
        1. Emails matching the sender query
        2. Any emails in the configured label/folder

        Results are deduplicated by message ID.

        Args:
            since_date: Only fetch emails after this date (default: 3 days ago)
            max_results: Maximum number of emails to fetch per query

        Returns:
            List of email dicts with id, subject, from, date, body, links
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        if since_date is None:
            cadence_days = self.config.get("schedule", {}).get("cadence_days", 3)
            since_date = datetime.now() - timedelta(days=cadence_days)

        # Format date for Gmail query
        date_str = since_date.strftime("%Y/%m/%d")
        
        all_message_ids = set()
        
        # Query 1: Fetch by sender filter
        if self.sender_query:
            sender_query = f"({self.sender_query}) after:{date_str}"
            sender_ids = self._fetch_message_ids(sender_query, max_results)
            all_message_ids.update(sender_ids)
            print(f"Found {len(sender_ids)} emails from sender filter")

        # Query 2: Fetch by label
        label_id = self._get_label_id(self.label)
        if label_id:
            label_query = f"after:{date_str}"
            label_ids = self._fetch_message_ids(
                label_query, max_results, label_ids=[label_id]
            )
            all_message_ids.update(label_ids)
            print(f"Found {len(label_ids)} emails in '{self.label}' label")
        else:
            print(f"Warning: Label '{self.label}' not found in Gmail")

        print(f"Total unique emails after deduplication: {len(all_message_ids)}")

        # Fetch full message content for each unique ID
        emails = []
        for msg_id in all_message_ids:
            email_data = self._fetch_message_content(msg_id)
            if email_data:
                emails.append(email_data)

        # Sort by date (newest first)
        emails.sort(key=lambda x: x.get("date", ""), reverse=True)

        return emails

    def _fetch_message_ids(
        self, query: str, max_results: int, label_ids: Optional[list] = None
    ) -> set[str]:
        """
        Fetch message IDs matching a query.

        Args:
            query: Gmail search query
            max_results: Maximum number of results
            label_ids: Optional list of label IDs to filter by

        Returns:
            Set of message IDs
        """
        message_ids = set()

        try:
            request_params = {
                "userId": "me",
                "q": query,
                "maxResults": max_results,
            }
            if label_ids:
                request_params["labelIds"] = label_ids

            results = self.service.users().messages().list(**request_params).execute()
            messages = results.get("messages", [])

            for msg in messages:
                message_ids.add(msg["id"])

            # Handle pagination if needed
            while "nextPageToken" in results and len(message_ids) < max_results:
                request_params["pageToken"] = results["nextPageToken"]
                results = self.service.users().messages().list(**request_params).execute()
                messages = results.get("messages", [])
                for msg in messages:
                    message_ids.add(msg["id"])

        except HttpError as e:
            print(f"Error fetching messages: {e}")

        return message_ids

    def _fetch_message_content(self, message_id: str) -> Optional[dict]:
        """
        Fetch full content of a single message.

        Args:
            message_id: Gmail message ID

        Returns:
            Dict with email data or None if error
        """
        try:
            message = (
                self.service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )

            headers = message.get("payload", {}).get("headers", [])
            
            # Extract headers
            subject = ""
            from_addr = ""
            date_str = ""
            
            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                if name == "subject":
                    subject = value
                elif name == "from":
                    from_addr = value
                elif name == "date":
                    date_str = value

            # Extract body
            body_html, body_text = self._extract_body(message.get("payload", {}))

            return {
                "id": message_id,
                "subject": subject,
                "from": from_addr,
                "date": date_str,
                "body_html": body_html,
                "body_text": body_text,
                "snippet": message.get("snippet", ""),
            }

        except HttpError as e:
            print(f"Error fetching message {message_id}: {e}")
            return None

    def _extract_body(self, payload: dict) -> tuple[str, str]:
        """
        Extract HTML and text body from message payload.

        Args:
            payload: Gmail message payload

        Returns:
            Tuple of (html_body, text_body)
        """
        html_body = ""
        text_body = ""

        def decode_body(data: str) -> str:
            """Decode base64url encoded body."""
            try:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            except Exception:
                return ""

        def process_part(part: dict):
            """Recursively process message parts."""
            nonlocal html_body, text_body

            mime_type = part.get("mimeType", "")
            body = part.get("body", {})
            data = body.get("data", "")

            if mime_type == "text/html" and data:
                html_body = decode_body(data)
            elif mime_type == "text/plain" and data:
                text_body = decode_body(data)

            # Process nested parts
            for subpart in part.get("parts", []):
                process_part(subpart)

        # Check if body is directly in payload
        body = payload.get("body", {})
        if body.get("data"):
            mime_type = payload.get("mimeType", "")
            decoded = decode_body(body["data"])
            if mime_type == "text/html":
                html_body = decoded
            else:
                text_body = decoded

        # Process multipart messages
        for part in payload.get("parts", []):
            process_part(part)

        return html_body, text_body


def setup_gmail_oauth():
    """Interactive setup helper for Gmail OAuth."""
    print("=" * 60)
    print("Gmail OAuth Setup")
    print("=" * 60)
    print()
    print("To fetch emails from Gmail, you need to set up OAuth credentials:")
    print()
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project (or select existing)")
    print("3. Enable the Gmail API:")
    print("   - APIs & Services > Library > Search 'Gmail API' > Enable")
    print("4. Create OAuth credentials:")
    print("   - APIs & Services > Credentials > Create Credentials")
    print("   - Choose 'OAuth client ID'")
    print("   - Application type: 'Desktop app'")
    print("   - Download the JSON file")
    print(f"5. Save the file as: {CLIENT_SECRET_PATH}")
    print()
    print("After placing the file, run this script again to authenticate.")
    print()
    
    if CLIENT_SECRET_PATH.exists():
        print("client_secret.json found! Attempting authentication...")
        fetcher = GmailFetcher({"gmail": {"label": "newsletters"}})
        if fetcher.authenticate():
            print("Authentication successful!")
            return True
        else:
            print("Authentication failed.")
            return False
    else:
        print(f"Waiting for {CLIENT_SECRET_PATH}...")
        return False


if __name__ == "__main__":
    setup_gmail_oauth()
