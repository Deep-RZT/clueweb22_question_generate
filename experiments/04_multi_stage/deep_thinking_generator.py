#!/usr/bin/env python
# deep_thinking_generator.py - Deep Thinking vs Standard Generation Comparison

"""
Demonstration of generating energy domain queries using two different methods:
1. Deep Thinking Method - Uses multi-round thinking and refinement
2. Standard Method - Uses direct single-round generation
"""

import os
import json
import re
from dotenv import load_dotenv
import anthropic
from datetime import datetime
from energy_query_generator import QueryRequirement, Difficulty, Category
from config import Config

# Load environment variables
load_dotenv()

class DeepThinkingGenerator:
    """Generator using deep thinking method"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.CLAUDE_API_KEY
        if not self.api_key:
            raise ValueError("API key is required. Set CLAUDE_API_KEY environment variable or pass it directly.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate_with_deep_thinking(self, requirement):
        """Generate high-quality queries using multi-round thinking"""
        # Step 1: Domain understanding and analysis
        understanding_prompt = f"""You are an expert in energy research. I need to generate high-quality research questions based on the following requirements:

Difficulty Level: {requirement.difficulty.value}
Category: {requirement.category.value}
Primary Subdomain: {requirement.primary_subdomain}
Secondary Subdomains: {', '.join(requirement.secondary_subdomains) if requirement.secondary_subdomains else 'None'}

Before generating questions, please think deeply about:
1. What are the cutting-edge research frontiers in these domains?
2. What key challenges and opportunities exist in these fields?
3. What important connections exist between these domains?
4. What types of questions would demonstrate depth and breadth in these areas?

Please provide your thinking process but do not generate specific questions yet."""

        # Call API for understanding and thinking
        understanding_response = self.client.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=Config.MAX_TOKENS,
            temperature=0.5,  # Lower temperature for consistency
            system="You are an expert energy researcher with deep domain knowledge. Provide thoughtful analysis of energy research domains.",
            messages=[
                {"role": "user", "content": understanding_prompt}
            ]
        )
        
        thinking_result = understanding_response.content[0].text
        
        # Step 2: Generate initial questions based on thinking
        generation_prompt = f"""Based on your previous thinking:

{thinking_result}

Now, please generate {requirement.count} high-quality research questions that meet the following criteria:

Difficulty Level: {requirement.difficulty.value}
Category: {requirement.category.value}
Primary Subdomain: {requirement.primary_subdomain}
Secondary Subdomains: {', '.join(requirement.secondary_subdomains) if requirement.secondary_subdomains else 'None'}

Remember:
- Questions should be clear, specific, and deep
- Questions should have research value, not simple fact queries
- Questions should demonstrate understanding of the relevant domains

List only the questions themselves, no explanations."""

        # Call API to generate initial questions
        generation_response = self.client.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            system="You are an expert energy researcher. Generate high-quality research questions based on your domain knowledge.",
            messages=[
                {"role": "user", "content": generation_prompt}
            ]
        )
        
        initial_questions = generation_response.content[0].text
        
        # Step 3: Refine and improve questions
        refinement_prompt = f"""Please review and refine the following research questions:

{initial_questions}

The goal is to make these questions:
1. More precise and clear
2. With better research depth and breadth
3. Better at testing the respondent's analytical and synthesis abilities
4. Maintaining appropriate difficulty level ({requirement.difficulty.value})

Provide the improved final version of the questions. List only the improved questions, no explanation of improvements."""

        # Call API to refine questions
        refinement_response = self.client.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=Config.MAX_TOKENS,
            temperature=0.5,  # Lower temperature for consistency
            system="You are an expert research question designer focused on quality and precision.",
            messages=[
                {"role": "user", "content": refinement_prompt}
            ]
        )
        
        final_questions = refinement_response.content[0].text
        
        # Parse generated questions
        questions = self._parse_questions(final_questions)
        
        # Save thinking process and intermediate results
        self._save_thinking_process(requirement, thinking_result, initial_questions, final_questions)
        
        return questions, {
            "thinking_process": thinking_result,
            "initial_questions": initial_questions,
            "final_questions": final_questions
        }
    
    def _parse_questions(self, text):
        """Parse generated question text"""
        questions = []
        
        # Split by line
        lines = text.strip().split('\n')
        current_question = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a numbered question
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^Q\d+[\.\)]', line):
                # Save previous question
                if current_question:
                    # Clean up numbering
                    clean_question = re.sub(r'^\d+[\.\)]\s*', '', current_question.strip())
                    clean_question = re.sub(r'^Q\d+[\.\)]\s*', '', clean_question)
                    questions.append(clean_question)
                
                # Start new question
                current_question = line
            else:
                # Continue current question
                current_question += " " + line
        
        # Add last question
        if current_question:
            clean_question = re.sub(r'^\d+[\.\)]\s*', '', current_question.strip())
            clean_question = re.sub(r'^Q\d+[\.\)]\s*', '', clean_question)
            questions.append(clean_question)
        
        return questions
    
    def _save_thinking_process(self, requirement, thinking, initial, final):
        """Save thinking process and intermediate results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.OUTPUT_DIR}/deep_thinking_process_{requirement.difficulty.value}_{requirement.primary_subdomain}_{timestamp}.json"
        
        data = {
            "requirement": {
                "difficulty": requirement.difficulty.value,
                "category": requirement.category.value,
                "primary_subdomain": requirement.primary_subdomain,
                "secondary_subdomains": requirement.secondary_subdomains,
                "count": requirement.count
            },
            "thinking_process": thinking,
            "initial_questions": initial,
            "final_questions": final,
            "timestamp": datetime.now().isoformat()
        }
        
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

class StandardGenerator:
    """Generator using standard single-round method"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.CLAUDE_API_KEY
        if not self.api_key:
            raise ValueError("API key is required. Set CLAUDE_API_KEY environment variable or pass it directly.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def generate_standard(self, requirement):
        """Generate queries using single-round approach"""
        # Build standard prompt
        prompt = f"""Generate {requirement.count} high-quality energy domain research questions that meet the following criteria:

Difficulty Level: {requirement.difficulty.value}
Category: {requirement.category.value}
Primary Subdomain: {requirement.primary_subdomain}
Secondary Subdomains: {', '.join(requirement.secondary_subdomains) if requirement.secondary_subdomains else 'None'}

Questions should be:
- Clear and specific
- Have research value
- Match the specified difficulty ({requirement.difficulty.value})
- Cover the specified domains

List questions directly, one per line, numbered."""

        # Call API to generate questions
        response = self.client.messages.create(
            model=Config.MODEL_NAME,
            max_tokens=Config.MAX_TOKENS,
            temperature=Config.TEMPERATURE,
            system="You are an expert energy researcher. Generate high-quality research questions.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result = response.content[0].text
        
        # Parse generated questions
        questions = []
        
        # Split by line
        lines = result.strip().split('\n')
        current_question = ""
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a numbered question
            if re.match(r'^\d+[\.\)]', line) or re.match(r'^Q\d+[\.\)]', line):
                # Save previous question
                if current_question:
                    # Clean up numbering
                    clean_question = re.sub(r'^\d+[\.\)]\s*', '', current_question.strip())
                    clean_question = re.sub(r'^Q\d+[\.\)]\s*', '', clean_question)
                    questions.append(clean_question)
                
                # Start new question
                current_question = line
            else:
                # Continue current question
                current_question += " " + line
        
        # Add last question
        if current_question:
            clean_question = re.sub(r'^\d+[\.\)]\s*', '', current_question.strip())
            clean_question = re.sub(r'^Q\d+[\.\)]\s*', '', clean_question)
            questions.append(clean_question)
        
        return questions, result

def compare_generation_methods():
    """Compare the two generation methods"""
    import re
    
    print("Energy Query Generator - Deep Thinking vs Standard Generation Comparison\n")
    
    # Check API key
    if not Config.CLAUDE_API_KEY:
        print("Error: CLAUDE_API_KEY not set!")
        print("Please set your Claude API key in the .env file.")
        return
    
    try:
        # Create generator instances
        deep_generator = DeepThinkingGenerator()
        standard_generator = StandardGenerator()
        
        # Create test requirements
        test_requirements = [
            QueryRequirement(
                difficulty=Difficulty.MEDIUM,
                category=Category.CROSS_SUBDOMAIN,
                primary_subdomain="Renewable",
                secondary_subdomains=["Policy", "Economics"],
                count=2
            ),
            QueryRequirement(
                difficulty=Difficulty.HARD, 
                category=Category.CROSS_SUBDOMAIN,
                primary_subdomain="Environmental",
                secondary_subdomains=["Fossil_Fuels", "Policy"],
                count=2
            )
        ]
        
        # Compare results
        all_results = []
        
        for i, req in enumerate(test_requirements, 1):
            print(f"\nTest {i}: {req.difficulty.value} {req.category.value} - {req.primary_subdomain}")
            
            # Deep thinking method
            print("\nGenerating using deep thinking method...")
            deep_questions, deep_process = deep_generator.generate_with_deep_thinking(req)
            
            # Standard method
            print("Generating using standard method...")
            standard_questions, standard_output = standard_generator.generate_standard(req)
            
            print("\nResults comparison:")
            print(f"Deep thinking method generated {len(deep_questions)} questions")
            for j, q in enumerate(deep_questions, 1):
                print(f"  {j}. {q}")
            
            print(f"\nStandard method generated {len(standard_questions)} questions")
            for j, q in enumerate(standard_questions, 1):
                print(f"  {j}. {q}")
            
            # Save results
            result = {
                "requirement": {
                    "difficulty": req.difficulty.value,
                    "category": req.category.value,
                    "primary_subdomain": req.primary_subdomain,
                    "secondary_subdomains": req.secondary_subdomains,
                    "count": req.count
                },
                "deep_thinking": {
                    "questions": deep_questions,
                    "thinking_process": deep_process["thinking_process"],
                    "initial_questions": deep_process["initial_questions"],
                    "final_questions": deep_process["final_questions"]
                },
                "standard": {
                    "questions": standard_questions,
                    "output": standard_output
                }
            }
            
            all_results.append(result)
        
        # Save all comparison results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        output_file = f"{Config.OUTPUT_DIR}/method_comparison_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Comparison complete! Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    compare_generation_methods() 