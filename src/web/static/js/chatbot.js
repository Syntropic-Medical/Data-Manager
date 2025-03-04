/**
 * Chatbot functionality for Data Manager
 * This file contains all the JavaScript code related to the chatbot interface
 */

document.addEventListener('DOMContentLoaded', function() {
  // DOM Elements
  const elements = {
    chatLaunchBtn: document.getElementById('chatLaunchBtn'),
    chatContainer: document.getElementById('chatContainer'),
    chatToggleBtn: document.getElementById('chatToggleBtn'),
    chatInput: document.getElementById('chatInput'),
    chatSendBtn: document.getElementById('chatSendBtn'),
    chatMessages: document.getElementById('chatMessages'),
    modelStatus: document.getElementById('modelStatus')
  };
  
  // State
  let isModelReady = false;
  
  // Initialize chatbot
  function initChatbot() {
    // Add event listeners
    setupEventListeners();
    
    // Add welcome message with a small delay to ensure libraries are loaded
    setTimeout(() => {
      // Test Markdown parsing
      console.log('Testing Markdown parsing:');
      const testMarkdown = '**Bold text** and *italic text* and a list:\n- Item 1\n- Item 2';
      console.log('Input:', testMarkdown);
      console.log('Output:', marked.parse(testMarkdown));
      
      // Add welcome message
      addWelcomeMessage();
      
      // Add suggested queries
      addSuggestedQueries();
    }, 100);
  }
  
  // Setup event listeners
  function setupEventListeners() {
    // Toggle chat visibility
    elements.chatLaunchBtn.addEventListener('click', function() {
      elements.chatContainer.style.display = 'flex';
      elements.chatLaunchBtn.style.display = 'none';
      elements.chatInput.focus();
      
      // Check model status when chat is opened
      checkModelStatus();
    });
    
    elements.chatToggleBtn.addEventListener('click', function() {
      elements.chatContainer.style.display = 'none';
      elements.chatLaunchBtn.style.display = 'flex';
    });
    
    // Send message on button click
    elements.chatSendBtn.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    elements.chatInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }
  
  // Add welcome message
  function addWelcomeMessage() {
    const welcomeMessage = `**Hello! I'm nimA, your Data Manager assistant.** I can help you:

- Search for entries using natural language (e.g. "Find experiments from last month")
- Learn how to use different features of the software
- Navigate the interface and understand functionality

I'm here to assist with software usage and searches only. I cannot answer personal questions or topics unrelated to the Data Manager software.

How can I assist you today?`;

    // Add the welcome message using the addMessage function for proper Markdown rendering
    addMessage(welcomeMessage, 'system');
  }
  
  // Check if LLM model is ready
  function checkModelStatus() {
    fetch('/llm_status')
      .then(response => response.json())
      .then(data => {
        isModelReady = data.ready;
        if (isModelReady) {
          elements.modelStatus.style.display = 'none';
        } else {
          elements.modelStatus.style.display = 'block';
          // Check again in 5 seconds
          setTimeout(checkModelStatus, 5000);
        }
      })
      .catch(error => {
        console.error('Error checking model status:', error);
        elements.modelStatus.style.display = 'block';
        // Try again in 10 seconds
        setTimeout(checkModelStatus, 10000);
      });
  }
  
  // Create typing indicator
  function createTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message system';
    indicator.id = 'typing-indicator';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    
    for (let i = 0; i < 3; i++) {
      const dot = document.createElement('div');
      dot.className = 'typing-dot';
      typingDiv.appendChild(dot);
    }
    
    indicator.appendChild(typingDiv);
    return indicator;
  }
  
  // Send message function
  function sendMessage() {
    const message = elements.chatInput.value.trim();
    if (!message) return;
    
    if (!isModelReady) {
      addMessage("**The assistant is still loading.**\n\nPlease wait a moment and try again.", 'system');
      return;
    }          
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Clear input
    elements.chatInput.value = '';
    
    // Add typing indicator
    elements.chatMessages.appendChild(createTypingIndicator());
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    // Send to backend
    fetch('/llm_search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query: message }),
    })
    .then(response => response.json())
    .then(data => {
      // Remove typing indicator
      const typingIndicator = document.getElementById('typing-indicator');
      if (typingIndicator) {
        typingIndicator.remove();
      }
      
      if (data.success) {
        // Add response message
        addMessage(data.message, 'system');
        
        // Display results if any
        if (data.entries && data.entries.length > 0) {
          displaySearchResults(data.entries);
        } else if (message.toLowerCase().includes("search") || 
                   message.toLowerCase().includes("find") || 
                   message.toLowerCase().includes("show") || 
                   message.toLowerCase().includes("get")) {
          // Only show "no entries" message if it was clearly a search query
        }
      } else {
        addMessage(data.message, 'system');
      }
    })
    .catch(error => {
      // Remove typing indicator
      const typingIndicator = document.getElementById('typing-indicator');
      if (typingIndicator) {
        typingIndicator.remove();
      }
      
      console.error('Error:', error);
      addMessage("**Sorry, there was an error processing your request.**\n\nPlease try again later.", 'system');
    });
  }
  
  // Add message to chat
  function addMessage(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', type);
    
    // Use Markdown parsing for system messages only
    if (type === 'system') {
      try {
        console.log('Parsing markdown:', text);
        // Parse markdown and sanitize the resulting HTML
        const parsedHtml = marked.parse(text);
        const sanitizedHtml = DOMPurify.sanitize(parsedHtml);
        messageDiv.innerHTML = sanitizedHtml;
        console.log('Parsed and sanitized HTML:', messageDiv.innerHTML);
      } catch (error) {
        console.error('Error parsing markdown:', error);
        // Fallback to basic formatting if parsing fails
        messageDiv.textContent = text;
      }
    } else {
      messageDiv.textContent = text;
    }
    
    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
  
  // Display search results
  function displaySearchResults(entries) {
    const resultsDiv = document.createElement('div');
    resultsDiv.classList.add('search-results');
    
    // Add header to results
    const headerDiv = document.createElement('div');
    headerDiv.classList.add('search-result-header');
    headerDiv.innerHTML = `<strong>Found ${entries.length} result${entries.length !== 1 ? 's' : ''}</strong>`;
    resultsDiv.appendChild(headerDiv);
    
    // Add divider
    const divider = document.createElement('hr');
    divider.style.margin = '8px 0';
    resultsDiv.appendChild(divider);
    
    entries.forEach(entry => {
      const entryDiv = document.createElement('div');
      entryDiv.classList.add('search-result-item');
      
      const titleDiv = document.createElement('div');
      titleDiv.classList.add('search-result-title');
      
      // Create a link to the entry
      const titleLink = document.createElement('a');
      titleLink.href = `/entry/${entry.id}`;
      titleLink.textContent = entry.title || 'Untitled Entry';
      titleDiv.appendChild(titleLink);
      
      const metaDiv = document.createElement('div');
      metaDiv.classList.add('search-result-meta');
      
      // Format the date
      let dateStr = entry.author;
      try {
        const entryDate = new Date(entry.author);
        dateStr = entryDate.toLocaleDateString();
      } catch (e) {
        // Use the original date string if parsing fails
      }
      
      metaDiv.textContent = `By ${entry.date} on ${dateStr} | Tags: ${entry.tags || 'None'}`;
      
      entryDiv.appendChild(titleDiv);
      entryDiv.appendChild(metaDiv);
      resultsDiv.appendChild(entryDiv);
    });
    
    elements.chatMessages.appendChild(resultsDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
  }
  
  // Function to add suggested queries
  function addSuggestedQueries() {
    const suggestedQueriesDiv = document.createElement('div');
    suggestedQueriesDiv.className = 'suggested-queries';
    suggestedQueriesDiv.innerHTML = `
      <p>Try asking me:</p>
      <button class="suggested-query-btn" data-query="How do I add a new entry?">How do I add a new entry?</button>
      <button class="suggested-query-btn" data-query="Show me how to search for entries">Show me how to search for entries</button>
      <button class="suggested-query-btn" data-query="Find entries from last week">Find entries from last week</button>
    `;
    
    elements.chatMessages.appendChild(suggestedQueriesDiv);
    
    // Add event listeners for suggested query buttons
    suggestedQueriesDiv.querySelectorAll('.suggested-query-btn').forEach(button => {
      button.addEventListener('click', function() {
        const query = this.getAttribute('data-query');
        elements.chatInput.value = query;
        sendMessage();
      });
    });
  }
  
  // Initialize the chatbot
  initChatbot();
}); 