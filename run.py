#!/usr/bin/env python3
"""
Standalone script to run Greenhouse automation with GPT field filling.
Can be run directly: python3 run.py input.json

GPT will automatically fill any fields that are not in input.json.
Make sure to set OPENAI_API_KEY environment variable or it will be passed from .env file.
"""
import sys
import os
import json

# Load environment variables from .env file if it exists
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Add parent directory to path to allow imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from the current package
try:
    from greenhouse_automation.greenhouse_automation import run_automation
except ImportError:
    # Fallback: try importing directly if we're in the package directory
    from greenhouse_automation import run_automation


def main():
    """Main entry point with GPT support"""
    try:
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
            with open(input_file, 'r') as f:
                input_data = json.load(f)
            print(f"📄 Loaded input from: {input_file}")
        else:
            print("Usage: python run.py <input_file.json>")
            print("\nExample: python run.py input.json")
            print("\nMake sure OPENAI_API_KEY is set for GPT field filling.")
            sys.exit(1)

        # Get OpenAI API key from environment
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        
        if openai_api_key:
            print(f"✅ OpenAI API key found: {openai_api_key[:20]}...")
            print("🤖 GPT field filling is ENABLED")
        else:
            print("⚠️  No OPENAI_API_KEY found - GPT field filling will be DISABLED")
            print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        
        print(f"\n{'='*60}")
        print(f"Starting Greenhouse Automation")
        print(f"{'='*60}\n")
        
        # Run automation with GPT enabled
        result = run_automation(
            input_data=input_data,
            enable_gmail_otp=True,
            gmail_credentials_file="credentials.json",
            gmail_token_file="token.json",
            enable_gpt=True if openai_api_key else False,
            gpt_model="gpt-4",  # or "gpt-3.5-turbo" for faster/cheaper
            openai_api_key=openai_api_key
        )
        
        # Output result
        print(f"\n{'='*60}")
        print(f"RESULT: {result['status'].upper()}")
        print(f"{'='*60}")
        print(f"Message: {result['message']}")
        print(f"{'='*60}\n")
        
        sys.exit(0 if result.get("status") == "success" else 1)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: File not found - {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Invalid JSON in input file - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()



