"""
Example: Running Greenhouse automation with Gmail OTP support
"""

import json
from greenhouse_automation import run_automation

# Load your input data
with open('input.json', 'r') as f:
    input_data = json.load(f)

# Run automation with Gmail OTP enabled
result = run_automation(
    input_data,
    enable_gmail_otp=True,  # Enable automatic OTP retrieval
    gmail_credentials_file='credentials.json',  # Path to OAuth2 credentials
    gmail_token_file='token.json'  # Path to store/load OAuth2 token
)

print(f"Automation result: {result['status']}")
if result['status'] == 'success':
    print("Application submitted successfully!")
else:
    print(f"Error: {result.get('message', 'Unknown error')}")

