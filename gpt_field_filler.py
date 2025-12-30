"""GPT-based field filler for Greenhouse automation
Automatically generates answers for fields not present in input.json
"""

import json
import os
from typing import Optional, Dict, Any
try:
    import openai
    # Try to import OpenAI client (new API v1.0+)
    try:
        from openai import OpenAI
        OPENAI_NEW_API = True
    except ImportError:
        OPENAI_NEW_API = False
except ImportError:
    openai = None
    OPENAI_NEW_API = False

try:
    from .utils import Logger
except ImportError:
    from utils import Logger


class GPTFieldFiller:
    """Uses GPT to generate answers for fields not in input.json"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize GPT field filler
        
        Args:
            api_key: OpenAI API key (if None, will use OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
        """
        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        
        self.logger = Logger()
        self.model = model
        
        # Get API key from parameter, environment, or use default
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        # Initialize OpenAI client based on API version
        if OPENAI_NEW_API:
            # New API (v1.0+)
            self.client = OpenAI(api_key=self.api_key)
            self.use_new_api = True
        else:
            # Old API (v0.x)
            openai.api_key = self.api_key
            self.client = None
            self.use_new_api = False
        
        self.logger.info(f"✅ GPT Field Filler initialized with model: {model}")
    
    def get_answer(self, question: str, context_data: Dict[str, Any]) -> str:
        """
        Generate an answer for a question using GPT based on context data
        
        Args:
            question: The field label/question to answer
            context_data: User data from input.json for context
            
        Returns:
            Generated answer as string
        """
        try:
            # Create context summary from input.json
            context = self._create_context_summary(context_data)
            
            # Create prompt for GPT
            prompt = self._create_prompt(question, context)
            
            self.logger.info(f"🤖 Generating answer for: {question}")
            
            # Call GPT API (support both old and new API styles)
            if self.use_new_api:
                # New API (v1.0+)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. Provide concise, professional answers based on the candidate's information. Keep answers brief and relevant."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                answer = response.choices[0].message.content.strip()
            else:
                # Old API (v0.x)
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. Provide concise, professional answers based on the candidate's information. Keep answers brief and relevant."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300
                )
                answer = response.choices[0].message.content.strip()
            self.logger.success(f"✅ Generated answer: {answer[:100]}...")
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Failed to generate answer for '{question}'", e)
            # Return a safe default
            return "Yes"
    
    def select_from_dropdown(self, field_label: str, available_options: list, context_data: Dict[str, Any]) -> str:
        """
        Select the most appropriate option from a dropdown list using GPT
        
        Args:
            field_label: The field label/question
            available_options: List of available dropdown options
            context_data: User data from input.json for context
            
        Returns:
            Selected option text (should match one of the available_options)
        """
        try:
            if not available_options:
                self.logger.warning(f"No options available for dropdown: {field_label}")
                return ""
            
            # Create context summary from input.json
            context = self._create_context_summary(context_data)
            
            # Create specialized prompt for dropdown selection
            options_text = "\n".join([f"- {opt}" for opt in available_options])
            
            prompt = f"""You are helping a candidate fill out a job application form.

Candidate Information:
{context}

Field/Question: {field_label}

Available Options:
{options_text}

IMPORTANT: You MUST select ONE option from the list above. Your response should be EXACTLY one of the options listed (match the text exactly, including capitalization and punctuation). Do not provide explanations, just return the exact option text.

Based on the candidate's information, which option should be selected?

Selected Option:"""
            
            self.logger.info(f"🤖 Asking GPT to select from dropdown: {field_label}")
            self.logger.info(f"   Available options: {', '.join(available_options[:5])}{'...' if len(available_options) > 5 else ''}")
            
            # Call GPT API
            if self.use_new_api:
                # New API (v1.0+)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. You must select options exactly as they appear in the dropdown list. Return only the exact option text, nothing else."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more consistent selection
                    max_tokens=100
                )
                answer = response.choices[0].message.content.strip()
            else:
                # Old API (v0.x)
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. You must select options exactly as they appear in the dropdown list. Return only the exact option text, nothing else."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more consistent selection
                    max_tokens=100
                )
                answer = response.choices[0].message.content.strip()
            
            # Clean up the answer - remove any quotes, extra whitespace, etc.
            answer = answer.strip().strip('"').strip("'").strip()
            
            self.logger.success(f"✅ GPT selected: {answer}")
            
            return answer
            
        except Exception as e:
            self.logger.error(f"Failed to select from dropdown for '{field_label}'", e)
            # Return first option as fallback
            return available_options[0] if available_options else ""
    
    def should_check_checkbox(self, checkbox_label: str, context_data: Dict[str, Any]) -> bool:
        """
        Determine if a checkbox should be checked based on candidate information
        
        Args:
            checkbox_label: The label/text associated with the checkbox
            context_data: User data from input.json for context
            
        Returns:
            True if checkbox should be checked, False otherwise
        """
        try:
            # Create context summary from input.json
            context = self._create_context_summary(context_data)
            
            # Create prompt for checkbox decision
            prompt = f"""You are helping a candidate fill out a job application form.

Candidate Information:
{context}

Checkbox Question/Label: {checkbox_label}

Based on the candidate's information above, determine if this checkbox should be checked.
- Answer with ONLY "yes" or "no" (lowercase)
- If the checkbox is asking about something the candidate has/agrees with, answer "yes"
- If the checkbox is asking about something the candidate doesn't have/disagrees with, answer "no"
- If the information is not available, make a reasonable professional inference

Should this checkbox be checked? (yes/no):"""
            
            self.logger.info(f"🤖 Determining checkbox state for: {checkbox_label}")
            
            # Call GPT API
            if self.use_new_api:
                # New API (v1.0+)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. Answer only with 'yes' or 'no' for checkbox questions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more consistent decisions
                    max_tokens=10
                )
                answer = response.choices[0].message.content.strip().lower()
            else:
                # Old API (v0.x)
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant filling out job application forms. Answer only with 'yes' or 'no' for checkbox questions."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Lower temperature for more consistent decisions
                    max_tokens=10
                )
                answer = response.choices[0].message.content.strip().lower()
            
            # Parse answer
            should_check = answer.startswith('yes') or answer == 'y' or answer == 'true' or answer == '1'
            
            self.logger.success(f"✅ Checkbox '{checkbox_label}': {'CHECKED' if should_check else 'UNCHECKED'}")
            
            return should_check
            
        except Exception as e:
            self.logger.error(f"Failed to determine checkbox state for '{checkbox_label}'", e)
            # Default to unchecked for safety
            return False
    
    def _create_context_summary(self, context_data: Dict[str, Any]) -> str:
        """Create a readable context summary from input.json data"""
        
        summary_parts = []
        
        # Basic info
        if context_data.get("firstName") and context_data.get("lastName"):
            summary_parts.append(f"Name: {context_data['firstName']} {context_data['lastName']}")
        
        if context_data.get("preferredFirstName"):
            summary_parts.append(f"Preferred Name: {context_data['preferredFirstName']}")
        
        if context_data.get("email"):
            summary_parts.append(f"Email: {context_data['email']}")
        
        if context_data.get("phone"):
            summary_parts.append(f"Phone: {context_data['phone']}")
        
        if context_data.get("locationCity"):
            summary_parts.append(f"Location: {context_data['locationCity']}")
        
        if context_data.get("country"):
            summary_parts.append(f"Country: {context_data['country']}")
        
        # Education
        if context_data.get("education"):
            edu_list = []
            for edu in context_data["education"]:
                school = edu.get("school", "")
                degree = edu.get("degree", "")
                discipline = edu.get("discipline", "")
                start_year = edu.get("startYear", "")
                end_year = edu.get("endYear", "")
                edu_str = f"{degree}"
                if discipline:
                    edu_str += f" in {discipline}"
                edu_str += f" from {school}"
                if start_year:
                    edu_str += f" ({start_year}"
                if end_year:
                    if start_year:
                        edu_str += f"-{end_year})"
                    else:
                        edu_str += f" (graduating {end_year})"
                elif start_year:
                    edu_str += ")"
                edu_list.append(edu_str)
            if edu_list:
                summary_parts.append(f"Education: {', '.join(edu_list)}")
        
        # Employment/Work Experience
        if context_data.get("employment"):
            emp_list = []
            for emp in context_data["employment"]:
                company = emp.get("company", "")
                title = emp.get("title", "")
                start_month = emp.get("startMonth", "")
                start_year = emp.get("startYear", "")
                end_month = emp.get("endMonth", "")
                end_year = emp.get("endYear", "")
                current_role = emp.get("currentRole", False)
                emp_str = f"{title} at {company}"
                if start_year:
                    emp_str += f" ({start_month} {start_year}" if start_month else f" ({start_year}"
                if current_role:
                    emp_str += " - Present)"
                elif end_year:
                    emp_str += f" - {end_month} {end_year})" if end_month else f" - {end_year})"
                elif start_year:
                    emp_str += ")"
                emp_list.append(emp_str)
            if emp_list:
                summary_parts.append(f"Work Experience: {', '.join(emp_list)}")
        
        # Work authorization
        if context_data.get("workAuthorized"):
            summary_parts.append(f"Work Authorization: {context_data['workAuthorized']}")
        
        if context_data.get("requireSponsorship"):
            summary_parts.append(f"Requires Sponsorship: {context_data['requireSponsorship']}")
        
        # Work preferences
        if context_data.get("languages"):
            summary_parts.append(f"Languages: {', '.join(context_data['languages'])}")
        
        if context_data.get("employmentTypes"):
            summary_parts.append(f"Employment Types: {context_data['employmentTypes']}")
        
        if context_data.get("willingToRelocate"):
            summary_parts.append(f"Willing to Relocate: {context_data['willingToRelocate']}")
        
        if context_data.get("openToRelocate"):
            summary_parts.append(f"Open to Relocate: {context_data['openToRelocate']}")
        
        # Demographics
        if context_data.get("gender"):
            summary_parts.append(f"Gender: {context_data['gender']}")
        
        if context_data.get("veteranStatus"):
            summary_parts.append(f"Veteran Status: {context_data['veteranStatus']}")
        
        # Links
        links = []
        if context_data.get("linkedinProfile"):
            links.append(f"LinkedIn: {context_data['linkedinProfile']}")
        if context_data.get("githubProfile"):
            links.append(f"GitHub: {context_data['githubProfile']}")
        if context_data.get("website"):
            links.append(f"Website: {context_data['website']}")
        if context_data.get("portfolio"):
            links.append(f"Portfolio: {context_data['portfolio']}")
        if links:
            summary_parts.append(", ".join(links))
        
        # Company-specific questions
        for key in ["hourlyExpectations", "internshipDates", "referredByEmployee", "referrerName"]:
            if context_data.get(key):
                # Convert camelCase to Title Case
                import re
                friendly_key = re.sub(r'([A-Z])', r' \1', key).strip().title()
                summary_parts.append(f"{friendly_key}: {context_data[key]}")
        
        return "\n".join(summary_parts) if summary_parts else "No additional context available."
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create GPT prompt for answering the question"""
        
        prompt = f"""You are helping a candidate fill out a job application form.

Candidate Information:
{context}

Question/Field to answer: {question}

Based on the candidate's information above, provide a brief, professional answer to this question. 
- If it's a yes/no question, answer with just "Yes" or "No"
- If it's asking for specific information the candidate has, provide it
- If it's asking about something not in the candidate's info, make a reasonable professional inference
- Keep the answer concise (1-2 sentences max for text, single word for yes/no)
- Do not include explanations or additional commentary

Answer:"""
        
        return prompt
    
    def fill_missing_fields(self, current_data: Dict[str, Any], field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Fill missing fields in current_data using GPT
        
        Args:
            current_data: Current input.json data
            field_mapping: Dict mapping field names to their question/label
                          e.g., {"customField1": "Do you have experience with Python?"}
        
        Returns:
            Updated data dict with GPT-generated answers for missing fields
        """
        updated_data = current_data.copy()
        
        for field_name, question in field_mapping.items():
            # Check if field is already in data
            if field_name not in current_data or not current_data.get(field_name):
                # Generate answer using GPT
                answer = self.get_answer(question, current_data)
                updated_data[field_name] = answer
                self.logger.info(f"✅ Added field '{field_name}': {answer}")
        
        return updated_data


def example_usage():
    """Example of how to use GPTFieldFiller"""
    
    # Load input.json
    with open("input.json", "r") as f:
        input_data = json.load(f)
    
    # Initialize GPT filler (you can also pass api_key parameter)
    # Make sure OPENAI_API_KEY is set in environment
    filler = GPTFieldFiller(model="gpt-4")
    
    # Define fields that might be missing and their corresponding questions
    # These would be custom questions from the Greenhouse form
    field_questions = {
        "yearsOfExperience": "How many years of professional experience do you have?",
        "willingToRelocate": "Are you willing to relocate for this position?",
        "expectedSalary": "What is your expected salary range?",
        "startDate": "When can you start?",
        "programmingLanguages": "What programming languages are you proficient in?",
        "whyThisCompany": "Why do you want to work for our company?",
    }
    
    # Fill missing fields
    updated_data = filler.fill_missing_fields(input_data, field_questions)
    
    # Save updated data
    with open("input_with_gpt_answers.json", "w") as f:
        json.dump(updated_data, f, indent=4)
    
    print("✅ Updated input.json with GPT-generated answers")
    print(json.dumps(updated_data, indent=2))


if __name__ == "__main__":
    example_usage()
