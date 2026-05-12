document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const form = document.getElementById('chat-form');
    const input = document.getElementById('message');
    const chatBox = document.getElementById('chat-box');
    let receiver = document.querySelector('.chat-item.active')?.getAttribute('data-username') || null;

    // === Utility Functions ===

    function toggleDarkMode(isEnabled) {
        document.body.classList.toggle("dark-mode", isEnabled);
        localStorage.setItem("darkMode", isEnabled);
        document.getElementById("dark-mode").checked = isEnabled;
    }

    function createMessageElement(msg) {
        const item = document.createElement('div');
        item.classList.add('msg', msg.sender === username ? 'right' : 'left');
        item.setAttribute('data-sender', msg.sender);
        item.setAttribute('data-receiver', msg.receiver);

        const content = document.createElement('p');
        content.innerHTML = msg.text;

        const time = document.createElement('span');
        time.classList.add('time');
        time.textContent = msg.time;

        item.appendChild(content);
        item.appendChild(time);
        return item;
    }

    function displayRelevantMessages() {
        const messages = document.querySelectorAll('#chat-box .msg');
        messages.forEach(msg => {
            const sender = msg.getAttribute('data-sender');
            const rec = msg.getAttribute('data-receiver');
            const shouldShow = (sender === username && rec === receiver) || (sender === receiver && rec === username);
            msg.style.display = shouldShow ? 'block' : 'none';
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function handleUserSelection(item) {
        document.querySelectorAll('.chat-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        receiver = item.getAttribute('data-username');
        document.getElementById('rec').textContent = receiver;

        fetch('/mark_read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender: receiver })
        })
            .then(res => res.json())
            .then(data => {
                console.log("Marked as read:", data.read_count);
                item.querySelector('.unseen')?.remove();
            });

        fetch(`/messages/${receiver}`)
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success') {
                    chatBox.innerHTML = '';

                    data.messages.forEach(msg => {
                        const msgEl = createMessageElement(msg);
                        chatBox.appendChild(msgEl);
                    });

                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            });

        displayRelevantMessages();
    }

    // === Dark Mode Setup ===
    toggleDarkMode(localStorage.getItem("darkMode") === "true");

    document.getElementById('dark-mode').addEventListener('click', () => {
        const isDark = !document.body.classList.contains("dark-mode");
        toggleDarkMode(isDark);
    });

    // === Socket.io Message Handler ===
    socket.on('message', function (msg) {
        if ((msg.sender === username && msg.receiver === receiver) ||
            (msg.sender === receiver && msg.receiver === username)) {
            const messageElement = createMessageElement(msg);
            chatBox.appendChild(messageElement);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        if (msg.sender === receiver || msg.receiver === receiver) {
            const target = document.querySelector(`.chat-item[data-username="${msg.sender}"] .unseen span`);
            if (target) {
                target.textContent = parseInt(target.textContent) + 1;
            } else {
                const span = document.createElement('span');
                span.textContent = 1;
                document.querySelector(`.chat-item[data-username="${msg.sender}"] .unseen`)?.appendChild(span);
            }
        }
    });

    // === Form Submission ===
    form.addEventListener('submit', function (e) {
        e.preventDefault();
        if (!receiver) {
            alert("Please select a user to chat with.");
            return;
        }
        if (input.value) {
            socket.emit('message', {
                text: input.value,
                receiver: receiver
            });
            input.value = '';
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });

    // === User Selection from Sidebar ===
    document.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', () => {
            handleUserSelection(item);
            document.querySelector('.sidebar').classList.remove('active');

            document.getElementById('carea').style.display = 'flex';
            document.getElementById('clogo').style.display = 'none';

        });
    });

});
document.getElementById('ic').addEventListener('click', () => {
    const sidebar = document.querySelector('.sidebar');

    const isActive = sidebar.classList.contains('active');

    if (isActive) {
        sidebar.classList.remove('active');
    } else {
        sidebar.classList.add('active');
    }
});

const messageInput = document.getElementById('message');

messageInput.addEventListener('focus', () => {
    setTimeout(() => {
        messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 300);
});


setInterval(() => {
    location.reload();
}, 90000);
