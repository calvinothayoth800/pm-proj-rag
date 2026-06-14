document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const queryInput = document.getElementById("queryInput");
    const chatContainer = document.getElementById("chatContainer");
    const sendBtn = document.getElementById("sendBtn");
    const statusBadge = document.getElementById("statusBadge");

    // Use relative API path (works in HF Spaces iframe)
    const API_URL = "/api/chat";

    // Check API status on load
    async function checkAPIStatus() {
        try {
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: "test" })
            });
            if (res.ok) {
                statusBadge.textContent = "Online";
                statusBadge.style.background = "#d1fae5";
                statusBadge.style.color = "#065f46";
            } else {
                statusBadge.textContent = "Error";
                statusBadge.style.background = "#fee2e2";
                statusBadge.style.color = "#991b1b";
            }
        } catch (err) {
            statusBadge.textContent = "Offline";
            statusBadge.style.background = "#fee2e2";
            statusBadge.style.color = "#991b1b";
        }
    }
    // Delay status check to avoid blocking initial load
    setTimeout(checkAPIStatus, 1000);

    // Handle example question clicks
    document.querySelectorAll(".example-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const query = chip.getAttribute("data-query");
            queryInput.value = query;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    function appendMessage(text, isUser = false) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${isUser ? "user-message" : "system-message"}`;
        
        const avatar = document.createElement("div");
        avatar.className = "avatar";
        avatar.textContent = isUser ? "You" : "AI";

        const bubble = document.createElement("div");
        bubble.className = "bubble";
        
        if (!isUser) {
            // Convert markdown links to HTML links
            let formatted = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
            // Convert plain URLs to links
            formatted = formatted.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
            bubble.innerHTML = `<pre>${formatted}</pre>`;
        } else {
            bubble.textContent = text;
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return msgDiv;
    }

    function showLoading() {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message system-message loading-msg";
        msgDiv.innerHTML = `
            <div class="avatar">AI</div>
            <div class="bubble">
                <div class="loading-dots"><div></div><div></div><div></div></div>
            </div>
        `;
        chatContainer.appendChild(msgDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return msgDiv;
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        appendMessage(query, true);
        queryInput.value = "";
        sendBtn.disabled = true;

        const loadingMsg = showLoading();

        try {
            const res = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            const data = await res.json();
            
            chatContainer.removeChild(loadingMsg);
            
            if (res.ok) {
                appendMessage(data.answer, false);
            } else {
                appendMessage("Error: " + (data.detail || "Unable to process request"), false);
            }
        } catch (err) {
            chatContainer.removeChild(loadingMsg);
            appendMessage("Connection error. Please check if the server is running.", false);
        } finally {
            sendBtn.disabled = false;
            queryInput.focus();
        }
    });

    // Focus input on load
    queryInput.focus();
});
