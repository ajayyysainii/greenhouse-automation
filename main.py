import json
import sys
from typing import Dict

# Handle both relative and absolute imports
try:
    from .greenhouse_automation import run_automation
except ImportError:
    from greenhouse_automation import run_automation


def validate_input_data(data: Dict) -> None:
    """Validate required input data fields."""
    required_fields = [
        "firstName", "lastName", "email", "resumePath", "jobUrl"
    ]
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required fields for Greenhouse automation: {', '.join(missing_fields)}")


def run_greenhouse_automation(input_data: Dict) -> Dict:
    """Run the Greenhouse automation with provided input data."""
    validate_input_data(input_data)
    result = run_automation(input_data)
    return result


def main():
    """Main entry point for standalone execution (e.g., for testing)."""
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r') as f:
                input_data = json.load(f)
        else:
            print("Usage: python main.py <input_file.json>")
            print("Or provide JSON via stdin")
            input_data = json.load(sys.stdin)

        print(f"[LOG] Input data received: {json.dumps(input_data, indent=2)}")
        # Run automation
        result = run_greenhouse_automation(input_data)
        # Output result
        print(f"\n[RESULT] {json.dumps(result, indent=2)}")
        sys.exit(0 if result.get("status") == "success" else 1)
    except Exception as e:
        error_result = {"status": "error", "message": f"Fatal error: {str(e)}"}
        print(f"\n[ERROR] {json.dumps(error_result, indent=2)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

