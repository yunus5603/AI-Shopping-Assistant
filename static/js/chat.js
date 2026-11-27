// Chat client: posts a question, reads the Server-Sent Events stream, renders
// tokens as they arrive and shows the reviews the answer was based on.
// All model and user text is inserted with textContent, never innerHTML.
(function () {
    const BOT_AVATAR = "https://cdn-icons-png.flaticon.com/512/4711/4711984.png";
    const USER_AVATAR = "https://cdn-icons-png.flaticon.com/512/1077/1077114.png";

    const messages = document.getElementById("messages");
    const form = document.getElementById("chatForm");
    const input = document.getElementById("userInput");
    const sendBtn = document.getElementById("sendBtn");
    const resetBtn = document.getElementById("resetBtn");

    function el(tag, className, text) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function scrollToBottom() {
        messages.scrollTop = messages.scrollHeight;
    }

    function addMessage(sender, text) {
        const wrapper = el("div", `message ${sender}-message`);
        const avatarBox = el("div", "img_cont_msg");
        const avatar = el("img", "user_img_msg");
        avatar.src = sender === "bot" ? BOT_AVATAR : USER_AVATAR;
        avatar.alt = `${sender} avatar`;
        avatarBox.appendChild(avatar);

        const content = el("div", "message-content");
        const body = el("div", "message-text", text || "");
        content.appendChild(body);
        wrapper.append(avatarBox, content);
        messages.appendChild(wrapper);
        scrollToBottom();
        return { content, body };
    }

    function showTyping(content) {
        const dots = el("div", "typing-indicator");
        dots.append(el("span"), el("span"), el("span"));
        content.prepend(dots);
        return dots;
    }

    // Minimal, safe Markdown: **bold** and "- " / "* " bullets, built from text nodes.
    function renderRich(body) {
        const text = body.textContent;
        body.textContent = "";
        let list = null;
        text.split("\n").forEach((line) => {
            const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
            const target = bullet ? el("li") : el("div");
            line = bullet ? bullet[1] : line;
            line.split(/(\*\*[^*]+\*\*)/).forEach((part) => {
                if (/^\*\*[^*]+\*\*$/.test(part)) target.appendChild(el("strong", null, part.slice(2, -2)));
                else if (part) target.appendChild(document.createTextNode(part));
            });
            if (bullet) {
                if (!list) body.appendChild((list = el("ul")));
                list.appendChild(target);
            } else {
                list = null;
                if (!line.trim()) target.appendChild(el("br"));
                body.appendChild(target);
            }
        });
        body.classList.add("rich");
    }

    function renderSources(content, sources) {
        if (!sources || !sources.length) return;
        const details = el("details", "sources");
        details.appendChild(el("summary", null, `Based on ${sources.length} customer reviews`));
        const list = el("ol");
        sources.forEach((src) => {
            const item = el("li");
            item.value = src.index;
            const rating = src.rating == null ? "" : ` · ${src.rating}★`;
            item.appendChild(el("strong", null, src.product_name + rating));
            item.appendChild(el("div", "source-snippet", src.snippet));
            list.appendChild(item);
        });
        details.appendChild(list);
        content.appendChild(details);
    }

    function setBusy(busy) {
        input.disabled = busy;
        sendBtn.disabled = busy;
        if (!busy) input.focus();
    }

    async function ask(question) {
        addMessage("user", question);
        const { content, body } = addMessage("bot", "");
        const typing = showTyping(content);
        let sources = null;
        setBusy(true);

        try {
            const response = await fetch("/get", {
                method: "POST",
                body: new URLSearchParams({ msg: question }),
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                throw new Error(data.error || `Request failed (${response.status})`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            for (;;) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                // Events end with a blank line; keep any partial event for the next chunk.
                const events = buffer.split("\n\n");
                buffer = events.pop();
                for (const event of events) {
                    if (!event.startsWith("data: ")) continue;
                    const data = JSON.parse(event.slice(6));
                    if (data.token) {
                        typing.remove();
                        body.textContent += data.token;
                        scrollToBottom();
                    } else if (data.sources) {
                        sources = data.sources;
                    } else if (data.error) {
                        typing.remove();
                        body.textContent = data.error;
                        body.classList.add("error");
                    }
                }
            }
            if (!body.classList.contains("error")) renderRich(body);
            renderSources(content, sources);
        } catch (err) {
            body.textContent = err.message || "Sorry, there was an error processing your request.";
            body.classList.add("error");
        } finally {
            typing.remove();
            setBusy(false);
            scrollToBottom();
        }
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        input.value = "";
        ask(question);
    });

    messages.addEventListener("click", (event) => {
        if (event.target.classList.contains("suggestion") && !input.disabled) {
            ask(event.target.textContent);
        }
    });

    resetBtn.addEventListener("click", async () => {
        await fetch("/reset", { method: "POST" });
        messages.querySelectorAll(".message").forEach((node, i) => {
            if (i > 0) node.remove();
        });
        input.focus();
    });
})();
