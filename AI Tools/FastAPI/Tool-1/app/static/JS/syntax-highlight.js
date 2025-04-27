/**
 * Simple Syntax Highlighter for Code Blocks
 * Adds basic syntax highlighting to code blocks in the chat interface
 */

document.addEventListener('DOMContentLoaded', function() {
    // Function to apply syntax highlighting to all code blocks
    function highlightAllCode() {
        const codeBlocks = document.querySelectorAll('pre code');
        
        codeBlocks.forEach(codeBlock => {
            if (!codeBlock.classList.contains('highlighted')) {
                highlightCode(codeBlock);
                codeBlock.classList.add('highlighted');
            }
        });
    }
    
    // Function to highlight code in a specific block
    function highlightCode(codeBlock) {
        let code = codeBlock.innerHTML;
        
        // Determine the language based on the code block's class or content
        let language = 'general';
        if (codeBlock.parentElement.className.includes('language-')) {
            const classes = codeBlock.parentElement.className.split(' ');
            for (const cls of classes) {
                if (cls.startsWith('language-')) {
                    language = cls.replace('language-', '');
                    break;
                }
            }
        } else if (code.includes('def ') || code.includes('import ') && code.includes(':')) {
            language = 'python';
        } else if (code.includes('function') || code.includes('const ') || code.includes('let ')) {
            language = 'javascript';
        } else if (code.includes('<html') || code.includes('<!DOCTYPE')) {
            language = 'html';
        } else if (code.includes('@media') || code.includes('font-size')) {
            language = 'css';
        }
        
        // Apply the appropriate highlighting based on the language
        if (language === 'python') {
            code = highlightPython(code);
        } else if (language === 'javascript' || language === 'js') {
            code = highlightJavaScript(code);
        } else if (language === 'html') {
            code = highlightHTML(code);
        } else if (language === 'css') {
            code = highlightCSS(code);
        } else {
            code = highlightGeneral(code);
        }
        
        codeBlock.innerHTML = code;
    }
    
    // Highlight Python code
    function highlightPython(code) {
        // Keywords
        const keywords = ['def', 'class', 'import', 'from', 'if', 'elif', 'else', 'for', 'while', 'return', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'try', 'except', 'finally', 'with', 'as', 'assert', 'break', 'continue', 'global', 'nonlocal', 'pass', 'raise', 'yield'];
        
        // Replace keywords with highlighted versions
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            code = code.replace(regex, `<span class="code-keyword">${keyword}</span>`);
        });
        
        // Highlight strings
        code = code.replace(/(["'])(?:(?=(\\?))\2.)*?\1/g, match => `<span class="code-string">${match}</span>`);
        
        // Highlight comments
        code = code.replace(/(#.*)$/gm, match => `<span class="code-comment">${match}</span>`);
        
        // Highlight function calls
        code = code.replace(/\b([a-zA-Z_][a-zA-Z0-9_]*)\(/g, (match, funcName) => {
            if (keywords.includes(funcName)) {
                return match;
            }
            return `<span class="code-function">${funcName}</span>(`;
        });
        
        return code;
    }
    
    // Highlight JavaScript code
    function highlightJavaScript(code) {
        // Keywords
        const keywords = ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'return', 'true', 'false', 'null', 'undefined', 'this', 'class', 'new', 'import', 'export', 'from', 'try', 'catch', 'finally', 'switch', 'case', 'break', 'continue', 'default', 'instanceof', 'typeof', 'in', 'of', 'async', 'await'];
        
        // Replace keywords with highlighted versions
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'g');
            code = code.replace(regex, `<span class="code-keyword">${keyword}</span>`);
        });
        
        // Highlight strings
        code = code.replace(/(["'`])(?:(?=(\\?))\2.)*?\1/g, match => `<span class="code-string">${match}</span>`);
        
        // Highlight comments
        code = code.replace(/\/\/.*/g, match => `<span class="code-comment">${match}</span>`);
        code = code.replace(/\/\*[\s\S]*?\*\//g, match => `<span class="code-comment">${match}</span>`);
        
        // Highlight function calls
        code = code.replace(/\b([a-zA-Z_][a-zA-Z0-9_]*)\(/g, (match, funcName) => {
            if (keywords.includes(funcName)) {
                return match;
            }
            return `<span class="code-function">${funcName}</span>(`;
        });
        
        return code;
    }
    
    // Highlight HTML code
    function highlightHTML(code) {
        // Highlight tags
        code = code.replace(/(&lt;[\/]?)([a-zA-Z0-9]+)([^&]*?)(&gt;)/g, (match, start, tag, attrs, end) => {
            return `${start}<span class="code-keyword">${tag}</span>${attrs}${end}`;
        });
        
        // Highlight attributes
        code = code.replace(/([a-zA-Z0-9_-]+)=["']([^"']*)["']/g, (match, attr, value) => {
            return `<span class="code-function">${attr}</span>="<span class="code-string">${value}</span>"`;
        });
        
        return code;
    }
    
    // Highlight CSS code
    function highlightCSS(code) {
        // Highlight selectors
        code = code.replace(/([a-zA-Z0-9_\-\.#]+)(\s*\{)/g, (match, selector, bracket) => {
            return `<span class="code-keyword">${selector}</span>${bracket}`;
        });
        
        // Highlight properties
        code = code.replace(/(\s+)([a-zA-Z0-9_\-]+)(\s*:)/g, (match, space, property, colon) => {
            return `${space}<span class="code-function">${property}</span>${colon}`;
        });
        
        // Highlight values
        code = code.replace(/(:)(\s*)([^;}]+)/g, (match, colon, space, value) => {
            return `${colon}${space}<span class="code-string">${value}</span>`;
        });
        
        // Highlight comments
        code = code.replace(/(\/\*[\s\S]*?\*\/)/g, match => `<span class="code-comment">${match}</span>`);
        
        return code;
    }
    
    // General code highlighting for unknown languages
    function highlightGeneral(code) {
        // Highlight strings
        code = code.replace(/(["'])(?:(?=(\\?))\2.)*?\1/g, match => `<span class="code-string">${match}</span>`);
        
        // Highlight numbers
        code = code.replace(/\b(\d+)\b/g, match => `<span class="code-number">${match}</span>`);
        
        return code;
    }
    
    // Watch for new messages and apply highlighting
    function setupMutationObserver() {
        // Create a MutationObserver to watch for new messages
        const observer = new MutationObserver(mutations => {
            mutations.forEach(mutation => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Check if any code blocks were added
                    setTimeout(() => {
                        highlightAllCode();
                    }, 100);
                }
            });
        });
        
        // Start observing the chat messages container
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            observer.observe(chatMessages, { childList: true, subtree: true });
        }
    }
    
    // Apply initial highlighting and set up observer
    highlightAllCode();
    setupMutationObserver();
}); 