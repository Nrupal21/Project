/**
 * Firebase-style Theme JavaScript
 * Handles animations, interactions, and UI enhancements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Add the firebase-theme class to the body
    document.body.classList.add('firebase-theme');
    
    // Initialize animations
    initAnimations();
    
    // Initialize tabs
    initTabs();
    
    // Initialize form handlers
    initFormHandlers();
    
    // Code highlighting
    highlightCode();
});

/**
 * Initialize animations for page elements
 */
function initAnimations() {
    // Animate elements when they come into view
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    // Create an observer for elements
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-visible');
                // Unobserve after animation is triggered
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1
    });
    
    // Observe each element
    animatedElements.forEach(el => {
        observer.observe(el);
    });
    
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.classList.add('card-hovered');
        });
        
        card.addEventListener('mouseleave', function() {
            this.classList.remove('card-hovered');
        });
    });
}

/**
 * Initialize tabs functionality
 */
function initTabs() {
    const tabLinks = document.querySelectorAll('[data-tab-target]');
    const tabContents = document.querySelectorAll('.tab-pane');
    
    tabLinks.forEach(tabLink => {
        tabLink.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all tabs
            tabLinks.forEach(link => {
                link.classList.remove('active');
                link.setAttribute('aria-selected', 'false');
            });
            
            // Add active class to current tab
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            
            // Hide all tab panes
            tabContents.forEach(content => {
                content.classList.add('hidden');
                content.classList.remove('active');
            });
            
            // Show the current tab pane
            const targetId = this.getAttribute('data-tab-target');
            const targetPane = document.getElementById(targetId);
            targetPane.classList.remove('hidden');
            targetPane.classList.add('active');
            
            // Reset results container
            document.getElementById('results-container').innerHTML = 
                '<p class="results-placeholder">Results will appear here after processing.</p>';
        });
    });
}

/**
 * Initialize form handlers for AI interactions
 */
function initFormHandlers() {
    // Text AI form handler
    const textForm = document.getElementById('text-processing-form');
    if (textForm) {
        textForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const resultsContainer = document.getElementById('results-container');
            resultsContainer.innerHTML = `
                <div class="flex justify-center items-center p-8">
                    <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            `;
            
            // Simulate API call with delay
            setTimeout(() => {
                const task = document.getElementById('text-task').value;
                const text = document.getElementById('text-input').value;
                
                // Display mock result
                resultsContainer.innerHTML = getTextResult(task, text);
            }, 1500);
        });
    }
    
    // Chat form handler
    const chatForm = document.getElementById('chat-form');
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageInput = document.getElementById('message-input');
            const message = messageInput.value;
            const model = document.getElementById('chat-model').value;
            
            if (!message.trim()) return;
            
            // Add user message
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML += `
                <div class="mb-3 bg-indigo-100 p-3 rounded-lg inline-block max-w-3/4 ml-auto">
                    <p class="text-gray-800"><strong>You:</strong> ${message}</p>
                </div>
            `;
            
            // Clear input
            messageInput.value = '';
            
            // Show typing indicator
            chatMessages.innerHTML += `
                <div id="typing-indicator" class="mb-3 bg-gray-100 p-3 rounded-lg inline-block max-w-3/4">
                    <p class="text-gray-800">
                        <strong>AI:</strong> 
                        <span class="typing-dots">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </span>
                    </p>
                </div>
            `;
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Add AI response (mock)
            setTimeout(() => {
                // Remove typing indicator
                document.getElementById('typing-indicator').remove();
                
                chatMessages.innerHTML += `
                    <div class="mb-3 bg-gray-100 p-3 rounded-lg inline-block max-w-3/4">
                        <p class="text-gray-800"><strong>AI (${model}):</strong> This is a response to your message: "${message}"</p>
                    </div>
                `;
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 1500);
        });
    }
    
    // Other form handlers...
}

/**
 * Generate text result based on task
 */
function getTextResult(task, text) {
    switch(task) {
        case 'summarize':
            return `
                <div class="p-4 bg-green-900/20 border border-green-800/30 rounded-md">
                    <h4 class="font-bold mb-2 text-green-400">Summary:</h4>
                    <p>This is a concise summary of the text you provided, highlighting the key points while maintaining the core message. The summary is approximately 25% of the original length.</p>
                </div>
            `;
        case 'translate':
            return `
                <div class="p-4 bg-blue-900/20 border border-blue-800/30 rounded-md">
                    <h4 class="font-bold mb-2 text-blue-400">Translation:</h4>
                    <p>Esto es una traducción del texto que proporcionaste. La traducción mantiene el significado original mientras se adapta naturalmente al español.</p>
                </div>
            `;
        case 'sentiment':
            return `
                <div class="p-4 bg-purple-900/20 border border-purple-800/30 rounded-md">
                    <h4 class="font-bold mb-2 text-purple-400">Sentiment Analysis:</h4>
                    <div class="flex items-center mb-3">
                        <div class="w-full bg-gray-700 rounded-full h-4">
                            <div class="bg-green-500 h-4 rounded-full" style="width: 85%"></div>
                        </div>
                        <span class="ml-3 font-medium">85%</span>
                    </div>
                    <p>The text has a <strong>Positive</strong> sentiment with 85% confidence. The language shows enthusiasm and optimism.</p>
                </div>
            `;
        case 'paraphrase':
            return `
                <div class="p-4 bg-indigo-900/20 border border-indigo-800/30 rounded-md">
                    <h4 class="font-bold mb-2 text-indigo-400">Paraphrased Text:</h4>
                    <p>Here is an alternative way to express the same ideas from your original text. The paraphrased version maintains the same meaning but uses different vocabulary and sentence structures.</p>
                </div>
            `;
        default:
            return `
                <div class="p-4 bg-gray-900/20 border border-gray-800/30 rounded-md">
                    <h4 class="font-bold mb-2">Processed Result:</h4>
                    <p>The AI has processed your text: "${text.substring(0, 50)}${text.length > 50 ? '...' : ''}"</p>
                </div>
            `;
    }
}

/**
 * Syntax highlighting for code blocks
 */
function highlightCode() {
    const codeBlocks = document.querySelectorAll('pre code');
    
    codeBlocks.forEach(block => {
        // Get the code
        const code = block.textContent;
        
        // Simple syntax highlighting for Python (this is basic, you may want to use a library like Prism.js for production)
        const pythonKeywords = ['def', 'return', 'if', 'else', 'elif', 'for', 'while', 'in', 'class', 'import', 'from', 'None', 'True', 'False'];
        
        // Highlight keywords
        let highlightedCode = code;
        pythonKeywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            highlightedCode = highlightedCode.replace(regex, `<span class="code-keyword">${keyword}</span>`);
        });
        
        // Highlight strings
        highlightedCode = highlightedCode.replace(/(["'])(.*?)\1/g, '<span class="code-string">$&</span>');
        
        // Highlight comments
        highlightedCode = highlightedCode.replace(/(#.*$)/gm, '<span class="code-comment">$1</span>');
        
        // Highlight function definitions
        highlightedCode = highlightedCode.replace(/\b(def\s+)(\w+)(\()/g, '$1<span class="code-function">$2</span>$3');
        
        // Set the highlighted code
        block.innerHTML = highlightedCode;
    });
} 