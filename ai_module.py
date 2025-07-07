# ai_integration/ai_module.py
import os
import json
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()


# from anthropic import Anthropic # Uncomment this line if you decide to use Claude

class AITaskManagement:
    """
    Handles all AI-powered task management features, including context processing,
    task prioritization, deadline suggestions, categorization, and task enhancement.
    """
    def __init__(self, api_choice='openai'):
        """
        Initializes the AI client based on the chosen API.
        Defaults to 'openai'. Can be 'claude' or 'lm_studio'.
        """
        self.api_choice = api_choice
        self.client = self._initialize_llm_client()

    def _initialize_llm_client(self):
        """
        Initializes the appropriate LLM client (OpenAI, Claude, or LM Studio).
        Reads API keys/base URLs from environment variables.
        """
        if self.api_choice == 'openai':
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("Warning: OPENAI_API_KEY not found in environment variables. OpenAI client may not work.")
            return OpenAI(api_key=api_key)
        elif self.api_choice == 'claude':
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("Warning: ANTHROPIC_API_KEY not found in environment variables. Claude client may not work.")
            # If using Anthropic, uncomment the line below and ensure 'anthropic' package is installed.
            # return Anthropic(api_key=api_key)
            print("Claude client not fully implemented in this example, requires 'anthropic' package and specific API calls.")
            return None # Placeholder, implement actual Claude client if used
        elif self.api_choice == 'lm_studio':
            # LM Studio typically runs a local server compatible with OpenAI's API.
            # The base URL is usually http://localhost:1234/v1.
            lm_studio_base_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
            # For LM Studio, the API key can be any string as it's a local server.
            return OpenAI(base_url=lm_studio_base_url, api_key="lm-studio-key")
        else:
            raise ValueError("Invalid API choice. Choose 'openai', 'claude', or 'lm_studio'.")

    def _call_llm(self, prompt: str, model_name: str = "gpt-3.5-turbo", max_tokens: int = 500) -> dict:
        """
        Helper method to make a call to the initialized LLM client.
        It expects the LLM to return a JSON string and attempts to parse it.
        """
        try:
            if self.client is None:
                print("LLM client not initialized. Cannot make API call.")
                return {}

            if self.api_choice in ['openai', 'lm_studio']:
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are a smart task management assistant. Provide responses in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}, # Instruct LLM to return JSON
                    temperature=0.7, # Controls randomness of response
                    max_tokens=max_tokens # Maximum number of tokens to generate
                )
                # Parse the JSON string from the LLM's response
                return json.loads(response.choices[0].message.content)
            elif self.api_choice == 'claude':
                # This section would contain the specific API call for Anthropic Claude.
                # Example (requires 'anthropic' package):
                # client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
                # response = client.messages.create(
                #     model="claude-3-opus-20240229", # Or other Claude model
                #     max_tokens=max_tokens,
                #     messages=[
                #         {"role": "user", "content": prompt}
                #     ]
                # )
                # return json.loads(response.content) # Assuming JSON content
                print("Claude API call not implemented in this example.")
                return {}
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from LLM response: {e}. Raw content: {response.choices[0].message.content if response else 'N/A'}")
            return {"error": "JSON decoding failed", "details": str(e)}
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return {"error": str(e)}

    def process_daily_context(self, context_content: str) -> dict:
        """
        Analyzes daily context (messages, emails, notes) to extract key information
        like entities, potential tasks, urgent keywords, and overall sentiment.
        """
        prompt = f"""
        Analyze the following daily context and extract key entities, potential tasks, urgent keywords, and general sentiment.
        Summarize the context concisely, highlighting any commitments or important information.
        Format the output as a JSON object with keys: "entities" (list of strings), "potential_tasks" (list of strings), "urgent_keywords" (list of strings), "sentiment" (string, e.g., 'positive', 'neutral', 'negative'), "summary" (string).

        Daily Context:
        {context_content}
        """
        # Using a generally faster model for context processing
        insights = self._call_llm(prompt, model_name="gpt-3.5-turbo", max_tokens=300)
        return insights if insights else {}

    def get_task_suggestions(self, task_details: dict, daily_context_data: list, user_preferences: dict, current_task_load: int) -> dict:
        """
        Generates AI-powered task suggestions, including prioritization, deadline recommendations,
        smart categorization, and enhanced task descriptions based on provided context and user data.
        """
        task_title = task_details.get('title', '')
        task_description = task_details.get('description', '')
        task_category = task_details.get('category', 'Uncategorized')

        context_summary_text = "No daily context available."
        if daily_context_data:
            # Combine and summarize context for the LLM to provide a holistic view
            combined_context = "\n".join([f"Source: {c['source_type']}: {c['content']}" for c in daily_context_data])
            context_summary_prompt = f"""Summarize the following daily context in a concise manner, highlighting any urgent matters, commitments, or schedule conflicts.
            Context:
            {combined_context}
            """
            summary_response = self._call_llm(context_summary_prompt, model_name="gpt-3.5-turbo", max_tokens=150)
            context_summary_text = summary_response.get('summary', combined_context[:200] + "...") # Fallback if summary fails

        # Construct a detailed prompt for the LLM to generate comprehensive suggestions
        prompt = f"""
        Given the following task details, daily context, user preferences, and current task load, provide AI-powered suggestions.
        The output should be a JSON object with the following keys:
        - "priority_score": An integer from 1 to 100 (100 being highest priority), reflecting urgency and importance.
        - "deadline": A suggested deadline in YYYY-MM-DD HH:MM:SS format, or null if no clear deadline can be inferred.
        - "suggested_category": A concise suggested category or tag for the task (e.g., 'Work', 'Personal', 'Finance', 'Health', 'Shopping').
        - "enhanced_description": An improved and more detailed task description, incorporating relevant context-aware details.
        - "recommendations": A list of short, actionable recommendations or sub-tasks related to the main task.

        Task Title: {task_title}
        Task Description: {task_description}
        Existing Category: {task_category}

        Daily Context Summary:
        {context_summary_text}

        User Preferences: {json.dumps(user_preferences)}
        Current Task Load: {current_task_load} pending tasks

        Consider the following when generating suggestions:
        - **Urgency:** Look for keywords like "urgent", "deadline", "ASAP", dates, or implied timeframes in context.
        - **Importance:** Identify key entities, people, or projects mentioned.
        - **Complexity:** Estimate effort based on description.
        - **Workload:** Suggest realistic deadlines given the current task load.
        - **Contextual Relevance:** Integrate details from the daily context into the enhanced description.
        - **Categorization:** Suggest a category that best fits the task and context.
        - **Default Deadline:** If no clear deadline is inferred, suggest a reasonable default, like 3 days from now, at a standard end-of-day time (e.g., 5 PM).
        """
        # Using a more capable model for detailed suggestions
        suggestions = self._call_llm(prompt, model_name="gpt-4o-mini", max_tokens=400)

        # --- Post-processing and Validation of AI Output ---
        # Ensure priority_score is an integer and within valid range
        if suggestions and 'priority_score' in suggestions:
            try:
                suggestions['priority_score'] = int(suggestions['priority_score'])
                suggestions['priority_score'] = max(1, min(100, suggestions['priority_score'])) # Clamp between 1 and 100
            except (ValueError, TypeError):
                suggestions['priority_score'] = 50 # Default if AI gives invalid number

        # Parse and validate deadline, provide a default if needed
        if suggestions and 'deadline' in suggestions and suggestions['deadline']:
            try:
                # Attempt to parse the deadline string into a datetime object
                suggestions['deadline'] = datetime.strptime(suggestions['deadline'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                print(f"Warning: Could not parse AI suggested deadline: {suggestions['deadline']}. Setting a default.")
                suggestions['deadline'] = None # Set to None if parsing fails
        else:
            suggestions['deadline'] = None # Ensure it's None if AI didn't provide one

        # If no deadline was provided or parsed, set a sensible default (e.g., 3 days from now, 5 PM)
        if suggestions and suggestions['deadline'] is None:
            default_deadline = datetime.now() + timedelta(days=3)
            # Set time to 5 PM (17:00:00) for a consistent default
            suggestions['deadline'] = default_deadline.replace(hour=17, minute=0, second=0, microsecond=0)

        # Ensure recommendations is a list
        if suggestions and 'recommendations' in suggestions and not isinstance(suggestions['recommendations'], list):
            suggestions['recommendations'] = []

        # Return structured suggestions with sensible defaults for any missing AI output
        return {
            "priority_score": suggestions.get("priority_score", 50),
            "deadline": suggestions.get("deadline"),
            "suggested_category": suggestions.get("suggested_category", task_category),
            "enhanced_description": suggestions.get("enhanced_description", task_description),
            "recommendations": suggestions.get("recommendations", []),
            "ai_raw_response": suggestions # Keep raw AI response for debugging
        }

# Initialize the AI manager globally or as needed.
# This ensures the LLM client is set up when the module is imported.
# You can change 'openai' to 'claude' or 'lm_studio' based on your preference and setup.
# For a production Django app, you might pass this choice via settings or a factory.
# ai_manager = AITaskManagement(api_choice=os.getenv("AI_API_CHOICE", "openai"))
# For simplicity in this example, we'll initialize it when needed in views.