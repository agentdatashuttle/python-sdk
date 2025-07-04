from langchain_core.prompts import PromptTemplate
from ..models.models import ADSDataPayload

def get_event_contextualization_prompt(agent_capabilities, ads_event_payload: ADSDataPayload) -> PromptTemplate:
    """
    Generate a prompt template for contextualizing events in the ADS system.
    
    Returns:
        PromptTemplate: A template for generating event context.
    """
    prompt_template = PromptTemplate.from_template("""
                        You are a system that creates detailed prompts for AI agents to act upon external events. ONLY generate the prompt, do not include any other text or explanation.
                        REMEMBER to add to the prompt that the agent should tell clearly what it did in what order and results it got, in a human like data presentation. Also, tell in the prompt that the agent must act like a HUMAN and logically take appropriate steps based on the event and its capabilities and react to the results it gets on each tool call.
                        NOTE THAT the agent should be instructed the following by the prompt you will generate:
                            - NEVER take destructive actions, like deleting files or data, unless explicitly stated in the event but should try to send notifications or get approval from the user before doing so, if the agent is capable of getting approvals or sending notifications.
                            - Do everything in the agent's power to ensure the event is handled in a way that is safe, logical, and follows the agent's capabilities.
                            - Should be able to reason out what was done by the agent in a human-like manner, explaining the steps taken, the results obtained, and any follow-up actions that may be needed.
                            - Behave in a headless manner, meaning it should not require any human intervention to complete the tasks based on the event but conclude gracefully by taking appropriate actions based on the event and its capabilities.
                            - Should convey to the agent via this prompt that this is a headless operation based on the event sent by the ADS (Agent Data Shuttle) protocol.
                            - End reply of the agent receiving your generated prompt should NOT be conversational, but rather a clear, well documented textual output of what was done, what results were obtained, and any next steps the user's should take, if applicable in absolute professional and formal tone.
                            

                        You will be given:
                        - A trigger event in the following format:
                            - `event_name` (string): A short name for the event wrapped in <event_name> tags.
                            - `event_description` (string): A natural language description of what the event represents wrapped in <EVENT_DESCRIPTION> tags.
                            - `event_data` (object): A dictionary containing relevant contextual data wrapped in <EVENT_DATA> tags.
                        - An AI agent's capability description wrapped in <AGENT_DESCRIPTION> tags: A paragraph describing what the agent is designed to do, what kinds of inputs it accepts, and what kinds of tasks it can perform.

                        YOUR GOAL:
                            Based on the event and the agent's capabilities, generate a clean, focused prompt that can be passed to the AI agent directly.
                            The generated prompt should:
                                - Explain the context of the event in relevance to the agent that will react to it.
                                - Describe what needs to be done by the agent based on what it can do.
                                - Reference the relevant `event_data` fields.
                                - Include a clear plan or list of steps the agent should perform based on its capabilities.
                                - Only include tasks the agent is capable of doing.
                                - Be written in natural language, structured for direct consumption by the agent.
                                - DO NOT include actions that are destructive or irreversible, like deleting files or data, unless explicitly stated in the event but should try to send notifications or get approval from the user before doing so, if the agent is capable of getting approvals or sending notifications.
                                                                                                      
                            If the event is not directly relevant to the agent's described capabilities, still generate a prompt that:  
                                - Clearly restates the event context. 
                                - Provides all available details from event_data. 
                                - Leaves it up to the agent to determine if and how it should respond, based on its own logic or fallback behavior.

                        Here are the details you will use to generate the prompt:
                            <EVENT_NAME>{event_name}</EVENT_NAME>
                                                    
                            <EVENT_DESCRIPTION>{event_description}</EVENT_DESCRIPTION>
                                                    
                            <EVENT_DATA>{event_data}</EVENT_DATA>
                                                    
                            <AGENT_DESCRIPTION>{agent_description}</AGENT_DESCRIPTION>
                                                   
                        ---
                        Here are some examples of how to generate the output prompt based on the event and agent capabilities:
                        ---
                        📌 Example 1: Directly Relevant Event  
                            <EVENT_NAME>new_file_uploaded</EVENT_NAME>  
                            <EVENT_DESCRIPTION>A new PDF document has been uploaded by the user for processing.</EVENT_DESCRIPTION>  
                            <EVENT_DATA>{{"file_name": "budget_2025.pdf", "uploaded_by": "user_122", "file_url": "https://example.com/docs/budget_2025.pdf", "upload_time": "2025-05-25T12:01:00Z"}}</EVENT_DATA>  
                            <AGENT_DESCRIPTION>This agent can extract metadata, summarize, and index PDF/DOCX/TXT documents into a vector database. It also notifies downstream systems upon successful processing.</AGENT_DESCRIPTION>  

                        🎯 OUTPUT PROMPT:  
                            ```
                                A new document titled **"budget_2025.pdf"** was uploaded by **user_122** at **2025-05-25T12:01:00Z**. The file is available at the provided URL.

                                Your tasks:
                                1. Download the document from: https://example.com/docs/budget_2025.pdf
                                2. Extract metadata such as filename, upload timestamp, and uploader ID.
                                3. Generate a concise summary of the document content.
                                4. Index the summary and metadata into the vector database.
                                5. Notify any downstream systems that the document has been processed.
                            ```

                            ---

                        📌 Example 2: Partially Relevant Event  
                            <EVENT_NAME>user_deleted_file</EVENT_NAME>  
                            <EVENT_DESCRIPTION>A user has deleted a previously uploaded document from the system.</EVENT_DESCRIPTION>  
                            <EVENT_DATA>{{"file_name": "budget_2025.pdf", "deleted_by": "user_122", "deletion_time": "2025-05-26T09:13:00Z"}}</EVENT_DATA>  
                            <AGENT_DESCRIPTION>This agent can extract metadata, summarize, and index PDF/DOCX/TXT documents into a vector database. It also notifies downstream systems upon successful processing.</AGENT_DESCRIPTION>  

                        🎯 OUTPUT PROMPT:  
                            ```
                                The document **"budget_2025.pdf"** was deleted by **user_122** on **2025-05-26T09:13:00Z**.

                                While deletion is not a direct processing task, you may want to:
                                - Check if the document exists in your indexed store.
                                - Remove any associated metadata or vector entries related to the file.
                                - Optionally, notify downstream systems that the file is no longer available.

                                Use your internal logic to decide whether and how to act.
                            ``` 

                            ---

                        📌 Example 3: Irrelevant Event  
                            <EVENT_NAME>user_logged_in</EVENT_NAME>  
                            <EVENT_DESCRIPTION>A user has logged into the dashboard.</EVENT_DESCRIPTION>  
                            <EVENT_DATA>{{"user_id": "user_122", "login_time": "2025-05-25T08:30:00Z", "ip_address": "203.0.113.24"}}</EVENT_DATA>  
                            <AGENT_DESCRIPTION>This agent only processes document files (PDF, DOCX, TXT), extracts their metadata and summaries, and indexes them into a vector database. It is not responsible for user authentication or session management.</AGENT_DESCRIPTION>  

                        🎯 OUTPUT PROMPT:  
                            ```
                                The user **user_122** logged in on **2025-05-25T08:30:00Z** from IP address **203.0.113.24**.
                                If possible, please log this event for auditing purposes or send notifications to people or systems if that's something you can do.
                            ```
                        """)
    
    return prompt_template.format(
                                    agent_description=agent_capabilities, 
                                    event_name=ads_event_payload.event_name,
                                    event_description=ads_event_payload.event_description,
                                    event_data=ads_event_payload.event_data
                             )
    