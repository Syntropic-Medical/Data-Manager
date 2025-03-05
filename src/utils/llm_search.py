import json
import re
import datetime
import os
import requests
import time
from dotenv import load_dotenv

class ExternalLLMSearch:
    """Search assistant that uses Claude API rather than loading models locally"""
    def __init__(self, api_key=None, testing_mode=False):
        """
        Initialize the LLM search assistant using Claude API
        
        Args:
            api_key: API key for Claude (can be set via environment variable)
            testing_mode: If True, skip API initialization for testing
        """
        self.ready = False
        self.testing_mode = testing_mode
        
        if testing_mode:
            self.api_key = "test_api_key"
            self.ready = True
            return
            
        # Load environment variables from .env file
        load_dotenv()
        
        # Get API key from environment or parameter
        self.api_key = api_key or os.environ.get("CLAUDE_API_KEY")
        
        if not self.api_key:
            print("WARNING: Claude API key not provided. Set the CLAUDE_API_KEY environment variable.")
            return
            
        self.ready = True
    
    def _generate_prompt(self, user_query, current_date):
        prompt = f"""
        You are nimA, a helpful assistant specifically designed to help users with the Data Manager software. Your role is strictly limited to:
        1. Helping users navigate and use the software features
        2. Assisting with searching and finding entries in the database
        3. Explaining software functionality based on the current interface

        You should:
        - Only answer questions related to using the software or searching entries
        - Politely decline to answer personal questions or topics unrelated to the software
        - Keep responses focused on practical software usage
        - Be friendly but professional
        - Never mention or discuss source code or technical implementation details
        - When asked about how to use specific parts of the software, provide instructions based on the user interface elements
        - Never reference HTML, code, or implementation details in your responses
        - Use Markdown formatting in your responses for better readability (bold, italics, lists, etc.)
        - Use **bold** for important terms, headings, and UI elements
        - Use *italics* for emphasis
        - Use proper line breaks and paragraphs for clarity
        - Use numbered lists for sequential instructions
        - Use bullet points for non-sequential items

        For search queries, extract these parameters (only include relevant fields):
        - title: String to search in entry titles
        - author: Author name to filter by
        - tags: Tags to search for (comma-separated)
        - text: Text to search within entries
        - date_start: Start date in YYYY-MM-DD format
        - date_end: End date in YYYY-MM-DD format
        - hash_id: Hash ID to search for
        - explanation: A brief explanation of how you interpreted the query

        Here is the user's query:
        "{user_query}"


        Here is the current date:
        "{current_date}"

        If this is a search query, respond with a valid JSON object containing the search parameters and put a filed called 'is_usage_question' with a value of false.
        If this is a question about using the software, provide a helpful explanation focused on user interface and functionality and put a filed called 'is_usage_question' with a value of true and a filed called 'explanation' with a value of the explanation of why you can't help with the question.
        If this is an unrelated question, politely explain that you can only help with software usage and searches and put a filed called 'is_usage_question' with a value of true and a filed called 'explanation' with a value of the explanation of why you can't help with the question.

        NEVER EVER introduce yourself at the beginning of your response.
        """
        return prompt
    
    def extract_search_params(self, user_query):
        """Extract search parameters from a natural language query using Claude API."""
        if not self.ready:
            print("Claude API not initialized. Cannot process query.")
            return None
            
        # If in testing mode, return mock search parameters
        if self.testing_mode:
            # Create simplified mock search parameters based on the query
            mock_params = {"text": "", "author": "", "date_from": None, "date_to": None}
            
            # Extract basic parameters from the query
            if "about" in user_query.lower():
                text_parts = user_query.lower().split("about")
                if len(text_parts) > 1:
                    mock_params["text"] = text_parts[1].split("from")[0].strip()
            
            if "by" in user_query.lower():
                author_parts = user_query.lower().split("by")
                if len(author_parts) > 1:
                    mock_params["author"] = author_parts[1].split("about")[0].strip()
            
            # Handle date ranges
            if "last week" in user_query.lower():
                today = datetime.datetime.now()
                mock_params["date_from"] = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
                mock_params["date_to"] = today.strftime("%Y-%m-%d")
                
            return mock_params
            
        # Regular processing with Claude API
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        prompt = self._generate_prompt(user_query, current_date)
        
        try:
            # Claude API specific headers
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"  # Use the appropriate version
            }
            
            # Claude API payload format
            payload = {
                "model": "claude-3-haiku-20240307",  # or another Claude model
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            print("Sending request to Claude API...")
            response = requests.post(
                "https://api.anthropic.com/v1/messages",  # Claude API endpoint
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"API error: {response.status_code}, {response.text}")
                return None
            
            result = response.json()
            
            # Extract content from Claude response format
            if "content" in result and len(result["content"]) > 0:
                # Claude's response format has a content array
                response_text = ""
                for content_block in result["content"]:
                    if content_block["type"] == "text":
                        response_text += content_block["text"]
            else:
                print("Unexpected Claude API response format")
                return None
            
            print(f"Claude response: {response_text}")
            
            # Extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    search_params = json.loads(json_str)
                    self._process_relative_dates(search_params)
                    return search_params
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {str(e)}")
                    fixed_json = self._fix_json(json_str)
                    if fixed_json:
                        search_params = fixed_json
                        self._process_relative_dates(search_params)
                        return search_params
            
            # If we couldn't extract valid JSON, fall back to our keyword extraction
            print("Could not extract valid JSON from Claude response")
            return None
        
        except Exception as e:
            print(f"Error querying Claude API: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _fallback_extraction(self, user_query):
        """Simple fallback keyword extraction when LLM is unavailable"""
        print("Using fallback keyword extraction")
        
        # Check if this is a question about software usage rather than a search
        usage_keywords = ["how to", "how do i", "help me", "guide", "instructions", "tutorial", 
                         "explain", "what is", "where is", "can't find", "don't understand"]
        
        for keyword in usage_keywords:
            if keyword in user_query.lower():
                # Generate a helpful response for common usage questions
                response = self._generate_usage_help(user_query)
                return {
                    "explanation": response,
                    "is_usage_question": True,
                    "query": user_query
                }
        
        search_params = {
            "explanation": "I'm using basic keyword matching to understand your query."
        }
        
        # Very basic extraction for text search
        words = user_query.split()
        common_words = ["find", "search", "show", "me", "entries", "with", "about", 
                         "that", "have", "containing", "get", "list", "display", "i", 
                         "want", "need", "looking", "for", "related", "to", "the", "all"]
        
        terms = [word for word in words if word.lower() not in common_words and len(word) > 3]
        if terms:
            search_params["text"] = " ".join(terms[:3])
        
        return search_params
    
    def _generate_usage_help(self, query):
        """Generate helpful responses for common usage questions"""
        query = query.lower()
        
        # Common usage patterns and responses
        if any(term in query for term in ["add entry", "create entry", "new entry", "insert entry"]):
            return """**How to Add a New Entry:**

1. Click on the **Insert Entry** button in the navigation bar
2. Fill in the required fields in the form:
   - Title
   - Tags
   - Any relevant details
3. You can also upload files related to the entry
4. Click **Submit** to save your entry"""
        
        elif any(term in query for term in ["search", "find entry", "look for"]):
            return """**How to Search for Entries:**

1. Go to the **Search Entries** page from the navigation bar
2. You can search by:
   - Author
   - Tags
   - Text content
3. Enter your search terms in the appropriate field
4. Click **Search** to view results

You can also use me to search by typing natural language queries like *"find entries about experiments from last month"*."""
        
        elif any(term in query for term in ["edit entry", "update entry", "modify entry"]):
            return """**How to Edit an Entry:**

1. First find the entry using the search function
2. Click on the entry to view its details
3. Click the **Edit** button
4. Make your changes in the form
5. Click **Save** to update the entry"""
        
        elif any(term in query for term in ["delete entry", "remove entry"]):
            return """**How to Delete an Entry:**

1. First find the entry using the search function
2. Click on the entry to view its details
3. Click the **Delete** button
4. Confirm the deletion when prompted

*Note: This action cannot be undone.*"""
        
        elif any(term in query for term in ["user management", "add user", "manage users"]):
            return """**User Management (Admin Only):**

1. Click on the **Admin** dropdown in the navigation bar
2. Select **User Management**
3. From there, you can:
   - Add new users
   - Edit existing users
   - Delete users

*This feature is only available to administrators.*"""
        
        elif any(term in query for term in ["backup", "restore", "export"]):
            return """**Backup and Restore (Admin Only):**

1. Click on the **Admin** dropdown in the navigation bar
2. Select **Backup**
3. You can:
   - Create a new backup of the database
   - Restore from a previous backup

*This feature is only available to administrators.*"""
        
        elif any(term in query for term in ["orders", "order management"]):
            return """**How to Manage Orders:**

1. Click on the **Resources** dropdown in the navigation bar
2. Select **Orders**
3. You can:
   - View existing orders
   - Create new orders by clicking **New Order**
   - Update the status of orders
   - Edit or delete orders you've created"""
        
        elif any(term in query for term in ["protocols", "view protocols"]):
            return """**How to View Protocols:**

1. Click on the **Resources** dropdown in the navigation bar
2. Select **Protocols**
3. Browse the list of available protocols
4. Click on a protocol to view details
5. Use the **Download** button to download a protocol"""
        
        elif any(term in query for term in ["conditions", "templates", "condition templates"]):
            return """**How to Access Condition Templates:**

1. Click on the **Resources** dropdown in the navigation bar
2. Select **Conditions Templates**
3. Browse available templates
4. You can view and manage condition templates for your entries"""
        
        elif any(term in query for term in ["profile", "account", "password"]):
            return """**How to Access Your Profile:**

1. Click on your **username** in the top-right corner of the page
2. Select **Profile** from the dropdown menu
3. You can:
   - Update your profile information
   - Change your password
   - View your activity history"""
        
        elif any(term in query for term in ["logout", "sign out"]):
            return """**How to Log Out:**

1. Click on your **username** in the top-right corner of the page
2. Select **Logout** from the dropdown menu
3. You will be signed out and returned to the login page"""
        
        else:
            return """**Welcome to Data Manager Help!**

I'm here to help you use the Data Manager software. You can ask me:

- How to perform specific tasks like adding entries
- How to search for entries
- How to manage your account
- How to use any feature of the software

I can also help you search for entries using natural language queries like *"find experiments from last week"*."""
    
    def _process_relative_dates(self, search_params):
        """Process relative date references in the search parameters"""
        today = datetime.datetime.now()
        
        # Process date_start
        if "date_start" in search_params and not re.match(r'^\d{4}-\d{2}-\d{2}$', search_params["date_start"]):
            date_start = search_params["date_start"].lower()
            
            if "month" in date_start and "ago" in date_start:
                months = int(re.search(r'(\d+)', date_start).group(1)) if re.search(r'(\d+)', date_start) else 1
                search_params["date_start"] = (today - datetime.timedelta(days=30*months)).strftime("%Y-%m-%d")
            elif "week" in date_start and "ago" in date_start:
                weeks = int(re.search(r'(\d+)', date_start).group(1)) if re.search(r'(\d+)', date_start) else 1
                search_params["date_start"] = (today - datetime.timedelta(weeks=weeks)).strftime("%Y-%m-%d")
            elif "day" in date_start and "ago" in date_start:
                days = int(re.search(r'(\d+)', date_start).group(1)) if re.search(r'(\d+)', date_start) else 1
                search_params["date_start"] = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            elif date_start == "yesterday":
                search_params["date_start"] = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_start == "last week":
                search_params["date_start"] = (today - datetime.timedelta(weeks=1)).strftime("%Y-%m-%d")
            elif date_start == "last month":
                search_params["date_start"] = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Process date_end similarly
        if "date_end" in search_params and not re.match(r'^\d{4}-\d{2}-\d{2}$', search_params["date_end"]):
            date_end = search_params["date_end"].lower()
            
            if "month" in date_end and "ago" in date_end:
                months = int(re.search(r'(\d+)', date_end).group(1)) if re.search(r'(\d+)', date_end) else 1
                search_params["date_end"] = (today - datetime.timedelta(days=30*months)).strftime("%Y-%m-%d")
            elif "week" in date_end and "ago" in date_end:
                weeks = int(re.search(r'(\d+)', date_end).group(1)) if re.search(r'(\d+)', date_end) else 1
                search_params["date_end"] = (today - datetime.timedelta(weeks=weeks)).strftime("%Y-%m-%d")
            elif "day" in date_end and "ago" in date_end:
                days = int(re.search(r'(\d+)', date_end).group(1)) if re.search(r'(\d+)', date_end) else 1
                search_params["date_end"] = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            elif date_end == "yesterday":
                search_params["date_end"] = (today - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_end == "today":
                search_params["date_end"] = today.strftime("%Y-%m-%d")
    
    def _fix_json(self, json_str):
        """Attempt to fix common JSON formatting issues"""
        try:
            # Fix unquoted keys
            fixed_json = re.sub(r'(\w+):', r'"\1":', json_str)
            # Remove trailing commas
            fixed_json = re.sub(r',\s*\}', '}', fixed_json)
            fixed_json = re.sub(r',\s*\]', ']', fixed_json)
            return json.loads(fixed_json)
        except:
            return None

def execute_llm_search(conn, search_params):
    """Execute a search based on parameters extracted by the search system"""
    # Check if this is a usage question rather than a search
    if search_params.get("is_usage_question"):
        # Return empty results for usage questions
        return []
    
    # Start with a basic query
    sql_command = 'SELECT * FROM entries WHERE '
    params = []
    conditions_added = False
    
    # Handle hash_id search (exact match)
    if search_params.get("hash_id"):
        sql_command += 'id_hash LIKE ? AND '
        params.append(f'%{search_params["hash_id"]}%')
        conditions_added = True
    
    # Handle author search (case-insensitive partial match)
    if search_params.get("author"):
        sql_command += 'LOWER(author) LIKE LOWER(?) AND '
        params.append(f'%{search_params["author"]}%')
        conditions_added = True
    
    # Group searches for the same term across multiple fields
    search_terms = set()
    if search_params.get("title"):
        # Split title into individual words for better matching
        search_terms.update(term.strip() for term in search_params["title"].split())
    if search_params.get("text"):
        search_terms.update(term.strip() for term in search_params["text"].split())
    if search_params.get("tags"):
        search_terms.update(tag.strip() for tag in search_params["tags"].split(','))
    
    # Add each search term with OR conditions across multiple fields
    for term in search_terms:
        if term and len(term) >= 3:  # Only search terms with 3 or more characters
            sql_command += '('
            # Try different variations of the term
            variations = [
                f'%{term}%',           # Basic contains
                f'%_{term}%',          # Part of underscore-separated word
                f'%{term}_%',          # Part of underscore-separated word
                f'%{term.lower()}%',   # Lowercase version
                f'%{term.upper()}%',   # Uppercase version
                f'%{term.title()}%'    # Title case version
            ]
            
            # Build the OR conditions for each field
            field_conditions = []
            for field in ['entry_name', 'extra_txt', 'tags', 'conditions']:
                for variation in variations:
                    field_conditions.append(f'{field} LIKE ?')
                    params.append(variation)
            
            sql_command += ' OR '.join(field_conditions)
            sql_command += ') AND '
            conditions_added = True
    
    # Handle date range
    if search_params.get("date_start"):
        sql_command += 'date >= ? AND '
        params.append(search_params["date_start"])
        conditions_added = True
    
    if search_params.get("date_end"):
        sql_command += 'date <= ? AND '
        params.append(search_params["date_end"])
        conditions_added = True
    
    # Finalize the SQL command
    if sql_command.endswith('AND '):
        sql_command = sql_command[:-5]
    elif not conditions_added:
        sql_command += '1=1'
    
    # Debug logging
    print("\nSearch parameters:", search_params)
    print("\nGenerated SQL:", sql_command)
    print("\nParameters:", params)
    
    # Execute the query
    cursor = conn.cursor()
    cursor.execute(sql_command, tuple(params))
    entries_list = cursor.fetchall()
    
    # Debug logging
    print(f"\nFound {len(entries_list)} results")
    if entries_list:
        print("First result entry_name:", entries_list[0][7])  # Assuming entry_name is at index 7
    
    return entries_list

class KeywordSearch:
    """A keyword-based search implementation that doesn't use an LLM"""
    def __init__(self):
        self.ready = True
        print("Initialized keyword-based search (no LLM required)")
        
    def extract_search_params(self, user_query):
        """Parse the query using basic keyword matching"""
        print(f"Processing query: {user_query}")
        search_params = {
            "explanation": "I'm searching based on keywords I extracted from your query."
        }
        
        user_query = user_query.lower()
        
        # Look for title keywords
        title_patterns = [
            r'title\s+(?:contains?|has|with|like)\s+["\']?([^"\']+)["\']?',
            r'name\s+(?:contains?|has|with|like)\s+["\']?([^"\']+)["\']?', 
            r'(?:called|named)\s+["\']?([^"\']+)["\']?',
            r'title\s*:\s*["\']?([^"\']+)["\']?',
            r'with\s+(?:the\s+)?title\s+["\']?([^"\']+)["\']?'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, user_query)
            if match:
                search_params["title"] = match.group(1).strip()
                break
                
        # If no specific title pattern matched but contains "title", extract nearby words
        if "title" in user_query and not search_params.get("title"):
            words = user_query.split()
            if "title" in words:
                idx = words.index("title")
                if idx + 1 < len(words):
                    # Take up to 3 words after "title"
                    search_params["title"] = " ".join(words[idx+1:min(idx+4, len(words))])
        
        # Look for author
        author_patterns = [
            r'by\s+(?:author\s+)?["\']?([^"\']+)["\']?',
            r'author\s*:\s*["\']?([^"\']+)["\']?',
            r'author\s+(?:is|named|called)\s+["\']?([^"\']+)["\']?',
            r'written\s+by\s+["\']?([^"\']+)["\']?'
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, user_query)
            if match:
                search_params["author"] = match.group(1).strip()
                break
        
        # Look for tags
        tag_patterns = [
            r'tag\s*(?:s|ged)?\s*:?\s*["\']?([^"\']+)["\']?',
            r'with\s+tags?\s+["\']?([^"\']+)["\']?',
            r'tagged\s+(?:with|as)\s+["\']?([^"\']+)["\']?'
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, user_query)
            if match:
                search_params["tags"] = match.group(1).strip()
                break
        
        # Look for dates
        self._extract_date_params(user_query, search_params)
        
        # Text search for any remaining keywords
        if not any(k in search_params for k in ["title", "author", "tags"]):
            # Extract key terms by removing common words
            common_words = ["find", "search", "show", "me", "entries", "with", "about", 
                          "that", "have", "containing", "get", "list", "display", "i", 
                          "want", "need", "looking", "for", "related", "to", "the", "all"]
            
            words = user_query.split()
            terms = [word for word in words if word.lower() not in common_words and len(word) > 3]
            
            if terms:
                search_params["text"] = " ".join(terms[:3])  # Use first 3 meaningful terms
        
        print(f"Extracted parameters: {search_params}")
        return search_params
    
    def _extract_date_params(self, user_query, search_params):
        """Extract date-related parameters from the query"""
        today = datetime.datetime.now()
        
        # Check for date ranges
        date_patterns = {
            # Last X days/weeks/months
            r'last\s+(\d+)\s+day': lambda x: (today - datetime.timedelta(days=int(x)), today),
            r'last\s+(\d+)\s+week': lambda x: (today - datetime.timedelta(weeks=int(x)), today),
            r'last\s+(\d+)\s+month': lambda x: (today - datetime.timedelta(days=int(x)*30), today),
            
            # Common time periods
            'last week': lambda x: (today - datetime.timedelta(weeks=1), today),
            'last month': lambda x: (today - datetime.timedelta(days=30), today),
            'this week': lambda x: (today - datetime.timedelta(days=today.weekday()), today),
            'this month': lambda x: (datetime.datetime(today.year, today.month, 1), today),
            'yesterday': lambda x: (today - datetime.timedelta(days=1), today - datetime.timedelta(days=1)),
            'today': lambda x: (today, today),
        }
        
        # Check for exact pattern matches first
        for pattern, date_func in date_patterns.items():
            if isinstance(pattern, str) and pattern in user_query:
                start_date, end_date = date_func(None)
                search_params["date_start"] = start_date.strftime("%Y-%m-%d")
                search_params["date_end"] = end_date.strftime("%Y-%m-%d")
                return
            elif isinstance(pattern, str):
                continue
                
            # For regex patterns
            match = re.search(pattern, user_query)
            if match:
                start_date, end_date = date_func(match.group(1))
                search_params["date_start"] = start_date.strftime("%Y-%m-%d")
                search_params["date_end"] = end_date.strftime("%Y-%m-%d")
                return

        # Look for specific dates in YYYY-MM-DD format
        date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', user_query)
        if len(date_matches) >= 2:
            search_params["date_start"] = date_matches[0]
            search_params["date_end"] = date_matches[1]
        elif len(date_matches) == 1:
            if "before" in user_query:
                search_params["date_end"] = date_matches[0]
            elif "after" in user_query or "since" in user_query:
                search_params["date_start"] = date_matches[0]
            else:
                # Default to exact date if no direction specified
                search_params["date_start"] = date_matches[0]
                search_params["date_end"] = date_matches[0]



