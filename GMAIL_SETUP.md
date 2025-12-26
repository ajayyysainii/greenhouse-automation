# Gmail API Setup Guide

This guide will help you set up Gmail API integration for automatic OTP retrieval.

## Prerequisites

- A Google account
- Python packages: `google-api-python-client`, `google-auth-oauthlib`, `google-auth-httplib2`

## Step 1: Install Dependencies

```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Step 2: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Note your project name

## Step 3: Enable Gmail API

1. In your Google Cloud project, go to **APIs & Services** > **Library**
2. Search for "Gmail API"
3. Click on **Gmail API** and click **Enable**

## Step 4: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen:
   - Choose **External** (unless you have a Google Workspace account)
   - Fill in required fields:
     - App name: "Greenhouse Automation" (or any name)
     - User support email: Your email (e.g., indoethnichub@gmail.com)
     - Developer contact: Your email
   - Click **Save and Continue**
   - Add scopes: `https://www.googleapis.com/auth/gmail.readonly`
   - Click **Save and Continue**
   - **IMPORTANT**: Add test users (your Gmail account) if in testing mode
     - Click **+ ADD USERS**
     - Enter your Gmail address (e.g., indoethnichub@gmail.com)
     - Click **ADD**
     - You can add multiple test users if needed
   - Click **Save and Continue**
   - Review and click **Back to Dashboard**

4. Create OAuth client ID:
   - Application type: **Desktop app**
   - Name: "Greenhouse Automation Client" (or any name)
   - Click **Create**

5. Download the credentials:
   - Click the download icon (⬇️) next to your OAuth client
   - Save the file as `credentials.json` in the `greenhouse_automation` directory

## Step 5: First-Time Authentication

When you run the automation with Gmail OTP enabled for the first time:

1. A browser window will open automatically
2. Sign in with your Google account (the one that receives OTP emails)
3. Review the permissions (Gmail read-only access)
4. Click **Allow** or **Continue**
5. You may see a warning about the app not being verified - click **Advanced** > **Go to [Your App] (unsafe)**
6. The authentication token will be saved to `token.json`

**Note:** The token is saved locally and will be reused for future runs. You only need to authenticate once.

## Step 6: Enable Gmail OTP in Your Code

### Option 1: Using `run_automation` function

```python
from greenhouse_automation import run_automation

input_data = {
    # ... your application data ...
}

result = run_automation(
    input_data,
    enable_gmail_otp=True,
    gmail_credentials_file='credentials.json',
    gmail_token_file='token.json'
)
```

### Option 2: Using `GreenhouseAutomation` class directly

```python
from greenhouse_automation import GreenhouseAutomation, GreenhouseApplicationInput

automation = GreenhouseAutomation(
    enable_gmail_otp=True,
    gmail_credentials_file='credentials.json',
    gmail_token_file='token.json'
)

application_input = GreenhouseApplicationInput.from_dict(input_data)
result = automation.run(application_input)
```

## How It Works

1. When you submit the Greenhouse application form, Greenhouse may send an OTP to your email
2. The automation detects the OTP input field
3. It authenticates with Gmail API (if not already done)
4. It searches for the latest email containing "verification" in the subject (or any recent email)
5. It extracts the OTP code using regex patterns
6. It automatically fills the OTP field and submits

## OTP Extraction Patterns

The system recognizes OTP codes in various formats:
- 6-digit codes: `123456`
- 4-digit codes: `1234`
- With separators: `123-456`, `123 456`
- With labels: "Your code is 123456", "OTP: 123456", "Verification code: 123456"

## Troubleshooting

### "Credentials file not found"
- Make sure `credentials.json` is in the `greenhouse_automation` directory
- Or specify the correct path in `gmail_credentials_file` parameter

### "Gmail API authentication failed"
- Check that Gmail API is enabled in your Google Cloud project
- Verify that `credentials.json` is valid
- Try deleting `token.json` and re-authenticating

### "Could not retrieve OTP from Gmail"
- Check that the email has arrived (wait a few seconds)
- Verify that your Gmail account has access to the emails
- Check that the email subject/body contains a recognizable OTP pattern
- Increase `max_age_minutes` in the code if emails are older

### "OTP field found but Gmail OTP reader not enabled"
- Make sure `enable_gmail_otp=True` is set when creating `GreenhouseAutomation`
- Verify that Gmail API packages are installed

## Security Notes

- **Read-only access**: The app only requests read-only access to Gmail
- **Local storage**: Credentials and tokens are stored locally on your machine
- **User consent**: You must explicitly authorize the app to access your Gmail
- **Token security**: Keep `token.json` and `credentials.json` secure and don't share them

## Revoking Access

If you want to revoke Gmail API access:

1. Go to [Google Account Settings](https://myaccount.google.com/permissions)
2. Find "Greenhouse Automation" (or your app name)
3. Click **Remove Access**

Or delete the `token.json` file to force re-authentication.

