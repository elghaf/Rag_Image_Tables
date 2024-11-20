class PDFChatApp {
    constructor() {
        this.sessionId = null;
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Upload elements
        this.dropZone = document.getElementById('dropZone');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.uploadBtn = document.getElementById('uploadBtn');
        
        // Chat elements
        this.uploadSection = document.getElementById('uploadSection');
        this.chatSection = document.getElementById('chatSection');
        this.chatMessages = document.getElementById('chatMessages');
        this.userInput = document.getElementById('userInput');
        this.sendBtn = document.getElementById('sendBtn');
        
        // Context panel elements
        this.contextPanel = document.getElementById('contextPanel');
        this.contextText = document.getElementById('contextText');
        this.contextImages = document.getElementById('contextImages');
        this.contextTables = document.getElementById('contextTables');
        
        // Loading overlay
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
    }

    attachEventListeners() {
        // File upload listeners
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });

        this.dropZone.addEventListener('dragleave', () => {
            this.dropZone.classList.remove('dragover');
        });

        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type === 'application/pdf') {
                this.handleFileSelection(file);
            }
        });

        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                this.handleFileSelection(file);
            }
        });

        this.uploadBtn.addEventListener('click', () => {
            this.uploadPDF();
        });

        // Chat listeners
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    handleFileSelection(file) {
        this.selectedFile = file;
        this.fileName.textContent = file.name;
        this.fileInfo.style.display = 'block';
    }

    async uploadPDF() {
        if (!this.selectedFile) return;

        this.showLoading('Processing PDF...');
        const formData = new FormData();
        formData.append('file', this.selectedFile);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (response.ok) {
                this.sessionId = data.session_id;
                this.switchToChat();
            } else {
                throw new Error(data.detail || 'Upload failed');
            }
        } catch (error) {
            alert('Error uploading PDF: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    switchToChat() {
        this.uploadSection.style.display = 'none';
        this.chatSection.style.display = 'flex';
    }

    async sendMessage() {
        const message = this.userInput.value.trim();
        if (!message || !this.sessionId) return;

        this.addMessage(message, 'user');
        this.userInput.value = '';

        try {
            const response = await fetch(`/chat/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ question: message })
            });

            const data = await response.json();
            if (response.ok) {
                this.addMessage(data.answer, 'bot');
                this.updateContext(data.context);
            } else {
                throw new Error(data.detail || 'Failed to get response');
            }
        } catch (error) {
            this.addMessage('Error: ' + error.message, 'system');
        }
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = content;
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    updateContext(context) {
        // Update text context
        this.contextText.innerHTML = context.text_chunks.map(text => 
            `<p class="context-text-item">${text}</p>`
        ).join('');

        // Update images
        this.contextImages.innerHTML = context.images.map(image => 
            `<img src="data:image/jpeg;base64,${image}" alt="Context Image">`
        ).join('');

        // Update tables
        this.contextTables.innerHTML = context.tables.join('');
    }

    showLoading(text) {
        this.loadingText.textContent = text;
        this.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    window.pdfChatApp = new PDFChatApp();
});