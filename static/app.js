/**
 * World Bank Chatbot - Frontend Logic
 */

// Global state
let userId = null;

// DOM Elements
const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const loadingDiv = document.getElementById('loading');

// ========== EVENT LISTENERS ==========

document.addEventListener('DOMContentLoaded', () => {
    // Send button click
    sendBtn.addEventListener('click', sendMessage);
    
    // Enter key press
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Auto-focus input
    userInput.focus();
});

// ========== FUNCTIONS ==========

/**
 * Send user message to backend
 */
async function sendMessage() {
    const query = userInput.value.trim();
    
    if (!query) return;
    
    // Disable input
    userInput.disabled = true;
    sendBtn.disabled = true;
    loadingDiv.style.display = 'flex';
    
    // Display user message
    appendMessage(query, 'user');
    
    // Clear input
    userInput.value = '';
    
    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                user_id: userId
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Save user_id
        if (data.user_id) {
            userId = data.user_id;
        }
        
        // Display bot response
        appendMessage(data.answer, 'bot');
        
    } catch (error) {
        console.error('Error:', error);
        appendMessage(
            `<p><strong>❌ Erreur</strong></p>
             <p>Une erreur s'est produite : ${error.message}</p>
             <p>Veuillez réessayer.</p>`,
            'bot'
        );
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendBtn.disabled = false;
        loadingDiv.style.display = 'none';
        userInput.focus();
    }
}

/**
 * Append message to chat
 * 
 * @param {string} content - Message content (HTML for bot, text for user)
 * @param {string} type - 'user' or 'bot'
 */
function appendMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (type === 'bot') {
        // Bot message: already HTML from backend
        contentDiv.innerHTML = content;
    } else {
        // User message: plain text
        const p = document.createElement('p');
        p.textContent = content;
        contentDiv.appendChild(p);
    }
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
