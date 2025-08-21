document.addEventListener('DOMContentLoaded', () => {

    //================================================================
    // MOBILE NAVIGATION
    //================================================================
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileNav = document.getElementById('mobile-nav');
    const navLinks = mobileNav.querySelectorAll('a');

    menuBtn.addEventListener('click', () => {
        mobileNav.classList.toggle('open');
    });

    // Close menu when a link is clicked
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileNav.classList.remove('open');
        });
    });

    //================================================================
    // SMOOTH SCROLLING FOR ALL ANCHOR LINKS
    //================================================================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    //================================================================
    // CHATBOT FUNCTIONALITY
    //================================================================
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatbotWindow = document.getElementById('chatbot-window');
    const chatbotClose = document.getElementById('chatbot-close');
    const chatbotMessages = document.getElementById('chatbot-messages');
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSend = document.getElementById('chatbot-send');
    const quickActionButtons = document.querySelectorAll('.quick-actions .btn');

    const predefinedReplies = [
        "Welcome to FutureTech University! How can I assist you today?",
        "Our AI and Quantum Computing programs are quite popular. Would you like to know more?",
        "I can help you with admissions, programs, campus facilities, or any other questions!",
        "Our placement rate is 95% with a high average package. Impressive, right?",
        "The holographic labs and quantum facilities are available for tours. Shall I schedule one?",
        "Our virtual reality library has infinite digital resources. Want to explore?",
        "Our Space Technology program includes zero-gravity simulators. Exciting, isn't it?",
        "I'm powered by advanced AI. Feel free to ask anything about our university!"
    ];

    // --- Event Listeners ---
    chatbotToggle.addEventListener('click', () => chatbotWindow.classList.toggle('open'));
    chatbotClose.addEventListener('click', () => chatbotWindow.classList.remove('open'));
    chatbotSend.addEventListener('click', handleSendMessage);
    chatbotInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
    
    quickActionButtons.forEach(button => {
        button.addEventListener('click', () => {
            chatbotInput.value = button.textContent;
            handleSendMessage();
        });
    });

    // --- Core Functions ---
    function handleSendMessage() {
        const userText = chatbotInput.value.trim();
        if (userText) {
            addMessage(userText, 'user');
            chatbotInput.value = '';
            setTimeout(sendBotResponse, 1000);
        }
    }

    function sendBotResponse() {
        const randomReply = predefinedReplies[Math.floor(Math.random() * predefinedReplies.length)];
        addMessage(randomReply, 'bot');
    }

    function addMessage(text, sender) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        const bubbleElement = document.createElement('div');
        bubbleElement.classList.add('message-bubble');
        bubbleElement.textContent = text;
        
        messageElement.appendChild(bubbleElement);
        chatbotMessages.appendChild(messageElement);
        scrollToBottom();
    }
    
    function scrollToBottom() {
        chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
    }
    
    // Initial bot message
    function initChat() {
        setTimeout(() => {
            addMessage("Hello! I'm ARIA, your AI assistant at FutureTech University. How can I help you?", 'bot');
        }, 500);
    }
    
    initChat();

});