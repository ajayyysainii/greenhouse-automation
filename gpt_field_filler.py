"""GPT-based field filler for Greenhouse automation
Automatically generates answers for fields not present in input.json
"""

import json
from typing import Optional, Dict, Any
try:
    import openai
except ImportError:
    openai = None

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
        
        # Set API key
        if api_key:
            openai.api_key = api_key
        
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
            
            # Call GPT API
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
    
    def _create_context_summary(self, context_data: Dict[str, Any]) -> str:
        """Create a readable context summary from input.json data"""
        
        summary_parts = []
        
        # Basic info
        if context_data.get("firstName") and context_data.get("lastName"):
            summary_parts.append(f"Name: {context_data['firstName']} {context_data['lastName']}")
        
        if context_data.get("email"):
            summary_parts.append(f"Email: {context_data['email']}")
        
        if context_data.get("phone"):
            summary_parts.append(f"Phone: {context_data['phone']}")
        
        if context_data.get("locationCity"):
            summary_parts.append(f"Location: {context_data['locationCity']}")
        
        # Education
        if context_data.get("education"):
            edu_list = []
            for edu in context_data["education"]:
                school = edu.get("school", "")
                degree = edu.get("degree", "")
                end_year = edu.get("endYear", "")
                edu_list.append(f"{degree} from {school} (graduating {end_year})")
            if edu_list:
                summary_parts.append(f"Education: {', '.join(edu_list)}")
        
        # Work authorization
        if context_data.get("workAuthorized"):
            summary_parts.append(f"Work Authorization: {context_data['workAuthorized']}")
        
        if context_data.get("requireSponsorship"):
            summary_parts.append(f"Requires Sponsorship: {context_data['requireSponsorship']}")
        
        # Demographics
        if context_data.get("gender"):
            summary_parts.append(f"Gender: {context_data['gender']}")
        
        if context_data.get("veteranStatus"):
            summary_parts.append(f"Veteran Status: {context_data['veteranStatus']}")
        
        # Links
        links = []
        if context_data.get("linkedinProfile"):
            links.append(f"LinkedIn: {context_data['linkedinProfile']}")
        if context_data.get("website"):
            links.append(f"Website: {context_data['website']}")
        if links:
            summary_parts.append(", ".join(links))
        
        # Any other relevant fields
        for key in ["hourlyExpectations", "openToRelocate", "internshipDates"]:
            if context_data.get(key):
                friendly_key = key.replace("_", " ").title()
                summary_parts.append(f"{friendly_key}: {context_data[key]}")
        
        return "\n".join(summary_parts)
    
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
