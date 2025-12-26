"""
Gmail API integration for OTP retrieval
Requires user consent via Google OAuth
"""

import os
import re
import base64
import json
import webbrowser
from typing import Optional
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes - only read access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailOTPReader:
    """Read OTP codes from Gmail using Gmail API"""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize Gmail OTP Reader
        
        Args:
            credentials_file: Path to OAuth2 credentials JSON file (from Google Cloud Console)
            token_file: Path to store/load OAuth2 token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self.logger = None  # Will be set by caller
        self._last_html_body = None  # Store HTML body for better OTP extraction
    
    def set_logger(self, logger):
        """Set logger instance"""
        self.logger = logger
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2
        User will be prompted to authorize access in browser
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                if self.logger:
                    self.logger.info(f"Loaded existing token from {self.token_file}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not load existing token: {str(e)}")
                creds = None
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                if self.logger:
                    self.logger.info("Token expired, attempting to refresh...")
                try:
                    creds.refresh(Request())
                    if self.logger:
                        self.logger.info("Token refreshed successfully")
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Failed to refresh token: {str(e)}")
                        self.logger.info("Will need to re-authenticate")
                    creds = None
            
            if not creds:
                # Check if credentials file exists
                credentials_path = os.path.abspath(self.credentials_file)
                if not os.path.exists(self.credentials_file):
                    if self.logger:
                        self.logger.error(
                            f"❌ Gmail credentials file not found: {credentials_path}\n"
                            "\n📋 To set up Gmail API:\n"
                            "1. Go to https://console.cloud.google.com/\n"
                            "2. Create a project (or select existing)\n"
                            "3. Enable Gmail API\n"
                            "4. Create OAuth 2.0 credentials (Desktop app)\n"
                            "5. Download credentials and save as 'credentials.json' in the greenhouse_automation folder\n"
                            "\nSee GMAIL_SETUP.md for detailed instructions."
                        )
                    return False
                
                if self.logger:
                    self.logger.info(f"📁 Using credentials from: {credentials_path}")
                    self.logger.info("🌐 Starting OAuth flow...")
                    self.logger.info("   A browser window should open automatically.")
                    self.logger.info("   If it doesn't open, check the URL printed below and open it manually.")
                
                try:
                    # Create the OAuth flow
                    if self.logger:
                        self.logger.info("   Creating OAuth flow...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    
                    if self.logger:
                        self.logger.info("   Starting OAuth flow...")
                        self.logger.info("   This will:")
                        self.logger.info("   1. Start a local server to receive the OAuth callback")
                        self.logger.info("   2. Open your browser automatically")
                        self.logger.info("   3. Ask you to authorize the application")
                        self.logger.info("")
                        self.logger.info("   ⏳ Please wait for the browser to open...")
                    
                    # run_local_server will:
                    # 1. Get authorization URL
                    # 2. Start local server
                    # 3. Open browser automatically
                    # 4. Wait for user to complete authorization
                    # 5. Return credentials
                    creds = flow.run_local_server(
                        port=0,
                        prompt='consent'  # Force consent screen
                    )
                    
                    if self.logger:
                        self.logger.info("")
                        self.logger.info("✅ OAuth authorization completed successfully!")
                        self.logger.info("   Token has been saved for future use.")
                        self.logger.info("   You won't need to authorize again unless the token expires.")
                except FileNotFoundError:
                    if self.logger:
                        self.logger.error(
                            f"❌ Credentials file not found: {credentials_path}\n"
                            "Please ensure the file exists and the path is correct."
                        )
                    return False
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"❌ OAuth flow failed: {str(e)}")
                        self.logger.error(f"Error type: {type(e).__name__}")
                        import traceback
                        self.logger.error(f"Full error details:\n{traceback.format_exc()}")
                    return False
            
            # Save credentials for next time
            try:
                token_path = os.path.abspath(self.token_file)
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                if self.logger:
                    self.logger.info(f"✅ Gmail API credentials saved to {token_path}")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not save token: {str(e)}")
        
        # Build Gmail service
        try:
            if self.logger:
                self.logger.info("Building Gmail API service...")
            self.service = build('gmail', 'v1', credentials=creds)
            if self.logger:
                self.logger.info("✅ Gmail API authenticated successfully")
            return True
        except HttpError as e:
            if self.logger:
                self.logger.error(f"❌ Gmail API HTTP error: {str(e)}")
                if e.resp.status == 403:
                    self.logger.error("Access forbidden. Please check:")
                    self.logger.error("1. Gmail API is enabled in Google Cloud Console")
                    self.logger.error("2. OAuth consent screen is properly configured")
                    self.logger.error("3. Your account has access to the project")
            return False
        except Exception as e:
            if self.logger:
                self.logger.error(f"❌ Failed to build Gmail service: {str(e)}")
                self.logger.error(f"Error type: {type(e).__name__}")
                import traceback
                self.logger.error(f"Full error details:\n{traceback.format_exc()}")
            return False
    
    def get_latest_email(self, from_email: Optional[str] = None, subject_contains: Optional[str] = None, max_age_minutes: int = 10) -> Optional[dict]:
        """
        Get the latest email matching criteria
        
        Args:
            from_email: Filter by sender email (optional)
            subject_contains: Filter by subject contains text (optional)
            max_age_minutes: Only get emails from last N minutes (default: 10)
        
        Returns:
            dict: Email data with 'id', 'snippet', 'body', 'subject', 'from', 'date'
            None: If no email found
        """
        if not self.service:
            if self.logger:
                self.logger.error("Gmail service not initialized. Call authenticate() first.")
            return None
        
        try:
            # Build query
            query_parts = []
            
            # Time filter - only recent emails
            after_date = (datetime.now() - timedelta(minutes=max_age_minutes)).strftime('%Y/%m/%d')
            query_parts.append(f"after:{after_date}")
            
            if from_email:
                query_parts.append(f"from:{from_email}")
            
            if subject_contains:
                query_parts.append(f'subject:"{subject_contains}"')
            
            query = " ".join(query_parts)
            
            if self.logger:
                self.logger.info(f"Searching Gmail with query: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=1
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                if self.logger:
                    self.logger.info("No matching emails found")
                return None
            
            # Get the latest message
            message_id = messages[0]['id']
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract email data
            payload = message.get('payload', {})
            headers = payload.get('headers', [])
            
            # Extract body (this also stores HTML in self._last_html_body)
            body_text = self._extract_body(payload)
            html_body = self._last_html_body  # Get stored HTML
            
            email_data = {
                'id': message_id,
                'snippet': message.get('snippet', ''),
                'body': body_text,
                'html_body': html_body,  # Include HTML body for better OTP extraction
                'subject': self._get_header(headers, 'Subject'),
                'from': self._get_header(headers, 'From'),
                'date': self._get_header(headers, 'Date')
            }
            
            if self.logger:
                self.logger.info(f"Found email from {email_data['from']} with subject: {email_data['subject']}")
            
            return email_data
            
        except HttpError as e:
            if self.logger:
                self.logger.error(f"Gmail API error while fetching email: {str(e)}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error fetching email: {str(e)}")
            return None
    
    def _extract_body(self, payload: dict) -> str:
        """Extract email body from payload, preserving HTML for better OTP extraction"""
        body = ""
        html_body = ""
        
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html':
                    data = part['body'].get('data')
                    if data:
                        html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        # Keep HTML for better extraction, but also create plain text version
                        if not body:
                            body = re.sub(r'<[^>]+>', '', html_body)
        else:
            # Simple message
            if payload['mimeType'] == 'text/plain':
                data = payload['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                data = payload['body'].get('data')
                if data:
                    html_body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    body = re.sub(r'<[^>]+>', '', html_body)
        
        # Store HTML body for OTP extraction (codes in h1 tags, etc.)
        self._last_html_body = html_body if html_body else None
        
        return body
    
    def _get_header(self, headers: list, name: str) -> str:
        """Get header value by name"""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return ""
    
    def extract_otp(self, email_body: str, email_subject: str = "", html_body: Optional[str] = None) -> Optional[str]:
        """
        Extract OTP code from email body/subject using regex patterns
        
        Args:
            email_body: Email body text (plain text)
            email_subject: Email subject (optional, also searched)
            html_body: HTML body (optional, for better extraction from tags)
        
        Returns:
            str: OTP code if found, None otherwise
        """
        # First, try to extract from HTML tags (h1, h2, strong, etc.) if available
        if html_body:
            # Look for codes in h1 tags (common pattern: <h1>CODE</h1>)
            # Use [A-Za-z0-9] to match both uppercase and lowercase
            h1_patterns = [
                r'<h1[^>]*>([A-Za-z0-9]{4,8})</h1>',  # <h1>CODE</h1>
                r'<h2[^>]*>([A-Za-z0-9]{4,8})</h2>',  # <h2>CODE</h2>
                r'<strong[^>]*>([A-Za-z0-9]{4,8})</strong>',  # <strong>CODE</strong>
                r'<b[^>]*>([A-Za-z0-9]{4,8})</b>',  # <b>CODE</b>
                r'<span[^>]*style[^>]*font-size[^>]*>([A-Za-z0-9]{4,8})</span>',  # Large font span
            ]
            
            for pattern in h1_patterns:
                matches = re.findall(pattern, html_body, re.IGNORECASE)
                if matches:
                    otp = matches[0]  # Preserve original case
                    if 4 <= len(otp) <= 8 and (otp.isalnum() or otp.isdigit()):
                        if self.logger:
                            self.logger.info(f"Extracted OTP from HTML tag: {otp} (preserving case)")
                        return otp
        
        # Also check the stored HTML body if available
        if self._last_html_body:
            h1_patterns = [
                r'<h1[^>]*>([A-Za-z0-9]{4,8})</h1>',
                r'<h2[^>]*>([A-Za-z0-9]{4,8})</h2>',
                r'<strong[^>]*>([A-Za-z0-9]{4,8})</strong>',
                r'<b[^>]*>([A-Za-z0-9]{4,8})</b>',
            ]
            
            for pattern in h1_patterns:
                matches = re.findall(pattern, self._last_html_body, re.IGNORECASE)
                if matches:
                    otp = matches[0]  # Preserve original case
                    if 4 <= len(otp) <= 8 and (otp.isalnum() or otp.isdigit()):
                        if self.logger:
                            self.logger.info(f"Extracted OTP from stored HTML: {otp} (preserving case)")
                        return otp
        
        # Combine body and subject for searching
        text = f"{email_subject} {email_body}"
        
        # Common OTP patterns:
        # - 8-character code: ABC12345, 12345678 (alphanumeric or numeric)
        # - 6-digit code: 123456
        # - 4-digit code: 1234
        # - With separators: 123-456, 123 456, ABC-1234
        # - With labels: "Your code is 123456", "OTP: 123456", "Code: 123456"
        # - Greenhouse specific: "Your verification code is 123456", "8-character code"
        
        patterns = [
            r'(?:verification|verification code|code|otp|one-time|one time|security code|8-character)[\s:]*[is]*[\s:]*([A-Za-z0-9]{4,8})',  # Labeled codes (alphanumeric, 4-8 chars, case-sensitive)
            r'\b([A-Za-z0-9]{8})\b',  # 8-character standalone (alphanumeric, case-sensitive)
            r'\b(\d{8})\b',  # 8-digit standalone
            r'\b([A-Za-z0-9]{6})\b',  # 6-character standalone (alphanumeric, case-sensitive)
            r'\b(\d{6})\b',  # 6-digit standalone
            r'\b(\d{4})\b',  # 4-digit standalone (less specific, try after 6-digit)
            r'([A-Za-z0-9]{3}[\s-]?[A-Za-z0-9]{3})',  # 6-character with separator (case-sensitive)
            r'(\d{3}[\s-]?\d{3})',  # 6-digit with separator
            r'(\d{2}[\s-]?\d{2}[\s-]?\d{2})',  # 6-digit with multiple separators
        ]
        
        # Try patterns in order
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Get the first match, clean it up
                otp = matches[0]  # Preserve original case
                # Remove separators
                otp = re.sub(r'[\s-]', '', otp)
                # Validate length (4-8 characters, alphanumeric)
                if 4 <= len(otp) <= 8 and (otp.isalnum() or otp.isdigit()):
                    if self.logger:
                        self.logger.info(f"Extracted OTP: {otp} using pattern: {pattern} (preserving case)")
                    return otp
        
        if self.logger:
            self.logger.warning("Could not extract OTP from email")
        return None
    
    def get_otp_from_latest_email(self, from_email: Optional[str] = None, subject_contains: Optional[str] = None, max_age_minutes: int = 10) -> Optional[str]:
        """
        Get OTP from the latest email (convenience method)
        
        Args:
            from_email: Filter by sender email (e.g., 'noreply@greenhouse.io')
            subject_contains: Filter by subject (e.g., 'verification', 'code')
            max_age_minutes: Only check emails from last N minutes
        
        Returns:
            str: OTP code if found, None otherwise
        """
        email = self.get_latest_email(from_email, subject_contains, max_age_minutes)
        if not email:
            return None
        
        # Extract OTP, passing HTML body if available
        html_body = email.get('html_body')
        otp = self.extract_otp(email['body'], email['subject'], html_body=html_body)
        return otp

