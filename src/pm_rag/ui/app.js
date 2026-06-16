document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const queryInput = document.getElementById("queryInput");
    const chatContainer = document.getElementById("chatContainer");
    const sendBtn = document.getElementById("sendBtn");
    const statusBadge = document.getElementById("statusBadge");

    // Use relative API path (works in HF Spaces iframe)
    const API_URL = "/api/chat";

    // Funds metadata for dynamic sidebar and title updates
    const fundsMetadata = {
        "hdfc-mid-cap-direct-growth": {
            name: "HDFC Mid Cap Fund",
            category: "Equity Mid Cap",
            description: "An equity mutual fund scheme investing predominantly in mid-cap companies. Aimed at generating long-term capital appreciation.",
            url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth"
        },
        "hdfc-equity-direct-growth": {
            name: "HDFC Flexi Cap Fund",
            category: "Equity Flexi Cap",
            description: "A flexible equity scheme investing across large-cap, mid-cap, and small-cap stocks, allowing dynamic portfolio adjustments.",
            url: "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth"
        },
        "hdfc-focused-direct-growth": {
            name: "HDFC Focused Fund",
            category: "Equity Focused",
            description: "A focused portfolio investing in a limited number of high-conviction companies (maximum 30) across market capitalizations.",
            url: "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth"
        },
        "hdfc-elss-tax-saver-direct-plan-growth": {
            name: "HDFC ELSS Tax Saver Fund",
            category: "Equity ELSS",
            description: "An Equity Linked Savings Scheme (ELSS) providing tax deduction benefits under Section 80C with a mandatory 3-year lock-in period.",
            url: "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth"
        },
        "hdfc-large-cap-direct-growth": {
            name: "HDFC Large Cap Fund",
            category: "Equity Large Cap",
            description: "A large-cap equity scheme investing primarily in established, blue-chip market leaders with stable growth profiles.",
            url: "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
        }
    };

    // Active fund state
    let activeSchemeId = "hdfc-mid-cap-direct-growth";

    // Chat history state per fund
    const chatHistories = {
        "hdfc-mid-cap-direct-growth": [
            { text: "Hi! I can answer questions about the HDFC Mid Cap Fund. Try clicking an example chip or type your question!", isUser: false }
        ],
        "hdfc-equity-direct-growth": [
            { text: "Hi! I can answer questions about the HDFC Flexi Cap Fund. Try clicking an example chip or type your question!", isUser: false }
        ],
        "hdfc-focused-direct-growth": [
            { text: "Hi! I can answer questions about the HDFC Focused Fund. Try clicking an example chip or type your question!", isUser: false }
        ],
        "hdfc-elss-tax-saver-direct-plan-growth": [
            { text: "Hi! I can answer questions about the HDFC ELSS Tax Saver Fund. Try clicking an example chip or type your question!", isUser: false }
        ],
        "hdfc-large-cap-direct-growth": [
            { text: "Hi! I can answer questions about the HDFC Large Cap Fund. Try clicking an example chip or type your question!", isUser: false }
        ]
    };

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

    // Select fund and sync both top and sidebar selector active states
    function selectFund(schemeId, force = false) {
        if (activeSchemeId === schemeId && !force) return;
        
        activeSchemeId = schemeId;
        
        // Sync both sidebar tabs and top horizontal tabs active states
        document.querySelectorAll(".sidebar-tab, .fund-tab").forEach(tab => {
            const tabScheme = tab.getAttribute("data-scheme");
            if (tabScheme === activeSchemeId) {
                tab.classList.add("active");
                tab.setAttribute("aria-selected", "true");
            } else {
                tab.classList.remove("active");
                tab.setAttribute("aria-selected", "false");
            }
        });
        
        renderActiveChat();
    }

    // Handle clicks on top horizontal tabs and sidebar tabs
    document.querySelectorAll(".sidebar-tab, .fund-tab").forEach(tab => {
        tab.addEventListener("click", () => {
            const schemeId = tab.getAttribute("data-scheme");
            selectFund(schemeId);
        });
    });

    // Render active chat and sidebar details
    function renderActiveChat() {
        // Clear chat container
        chatContainer.innerHTML = "";
        
        // Render message history for the active fund
        const history = chatHistories[activeSchemeId] || [];
        history.forEach(msg => {
            appendMessageHTML(msg.text, msg.isUser);
        });
        
        // Update sidebar details with a premium fade transition
        const meta = fundsMetadata[activeSchemeId];
        const detailsCard = document.getElementById("schemeDetails");
        if (meta && detailsCard) {
            detailsCard.classList.add("fade-out");
            
            setTimeout(() => {
                document.getElementById("schemeDetailTitle").textContent = meta.name;
                document.getElementById("schemeDetailDesc").textContent = meta.description;
                document.getElementById("schemeGrowwLink").href = meta.url;
                document.querySelector(".logo p").textContent = `${meta.category} \u2022 Facts only`;
                
                detailsCard.classList.remove("fade-out");
            }, 150);
        }
    }

    // Handle example question clicks
    document.querySelectorAll(".example-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const query = chip.getAttribute("data-query");
            queryInput.value = query;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    function appendMessageHTML(text, isUser = false) {
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

    function appendMessage(text, isUser = false) {
        // Save to active chat history
        if (!chatHistories[activeSchemeId]) {
            chatHistories[activeSchemeId] = [];
        }
        chatHistories[activeSchemeId].push({ text, isUser });
        return appendMessageHTML(text, isUser);
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
                body: JSON.stringify({ query, scheme_id: activeSchemeId })
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

    // Initial render
    selectFund(activeSchemeId, true);
    queryInput.focus();
});
