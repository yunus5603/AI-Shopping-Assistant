$(document).ready(function() {
    const $messageContainer = $('#messageContainer');
    const $chatForm = $('#chatForm');
    const $userInput = $('#userInput');
    const $sendBtn = $('#sendBtn');
    const $typingIndicator = $('#typingIndicator');

    // Auto-scroll to bottom
    function scrollToBottom() {
        $messageContainer.scrollTop($messageContainer[0].scrollHeight);
    }

    // Show typing indicator
    function showTyping() {
        $typingIndicator.removeClass('d-none');
        scrollToBottom();
    }

    // Hide typing indicator
    function hideTyping() {
        $typingIndicator.addClass('d-none');
    }

    // Escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Handle form submission
    $chatForm.on('submit', function(e) {
        e.preventDefault();
        const message = $userInput.val().trim();
        if (!message) return;

        // Disable input during processing
        $userInput.prop('disabled', true);
        $sendBtn.prop('disabled', true);

        // Add user message
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const userMessage = `
            <div class="d-flex justify-content-end mb-4 message-container">
                <div class="msg_container_send">
                    ${escapeHtml(message)}
                    <span class="msg_time_send">${time}</span>
                </div>
                <div class="img_cont_msg">
                    <img src="https://i.ibb.co/d5b84Xw/Untitled-design.png" 
                         class="rounded-circle user_img_msg" 
                         alt="User Avatar">
                </div>
            </div>`;
        
        $messageContainer.append(userMessage);
        $userInput.val('');
        scrollToBottom();
        showTyping();

        // Simulate API call (replace with actual AJAX call)
        setTimeout(() => {
            // Add bot response
            const botMessage = `
                <div class="d-flex justify-content-start mb-4 message-container">
                    <div class="img_cont_msg">
                        <img src="https://static.vecteezy.com/system/resources/previews/016/017/018/non_2x/ecommerce-icon-free-png.png" 
                             class="rounded-circle user_img_msg" 
                             alt="Bot Avatar">
                    </div>
                    <div class="msg_container">
                        ${escapeHtml(`Thanks for your message: "${message}". This is a sample response.`)}
                        <span class="msg_time">${time}</span>
                    </div>
                </div>`;
            
            $messageContainer.append(botMessage);
            hideTyping();
            scrollToBottom();
            
            // Re-enable input
            $userInput.prop('disabled', false);
            $sendBtn.prop('disabled', false);
        }, 1500);
    });

    // Clear chat function
    window.clearChat = function() {
        if (confirm("Are you sure you want to clear the chat history?")) {
            $messageContainer.html(`
                <div class="d-flex justify-content-start mb-4">
                    <div class="img_cont_msg">
                        <img src="https://static.vecteezy.com/system/resources/previews/016/017/018/non_2x/ecommerce-icon-free-png.png" 
                             class="rounded-circle user_img_msg" 
                             alt="Bot Avatar">
                    </div>
                    <div class="msg_container">
                        Hi! I'm your Flipkart Product Assistant. How can I help you today?
                        <span class="msg_time">Now</span>
                    </div>
                </div>
            `);
        }
    };

    // Input validation
    $userInput.on('input', function() {
        $sendBtn.prop('disabled', !$(this).val().trim());
    });
});