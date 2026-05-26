# 🌐 Sentrix Browser

**Decentralized, Cross-Platform, Local-First AI Agentic Browser**

Sentrix Browser is an innovative AI-powered browser that runs entirely on your local machine. Unlike cloud-based AI agents, Sentrix leverages local LLMs via Ollama to read, reason, and act on web content while maintaining complete data privacy and security.

## ✨ Features

### Core Capabilities
- **Local-First AI Processing**: All AI reasoning happens locally using Ollama - no data leaves your machine
- **Automated Web Navigation**: Agent can autonomously navigate websites and complete tasks
- **Task Scheduling**: Schedule automated tasks for future execution with background processing
- **Secure Gmail Integration**: OAuth2-based email connectivity for automated reports
- **Cross-Platform Support**: Native applications for Windows, macOS, and Linux
- **Chrome-Like Experience**: Familiar browser interface with advanced AI capabilities

### Security Features
- **Process Isolation**: Sandboxed frontend environment with isolated backend communication
- **Cryptographic Token Authentication**: Secure token-based communication between components
- **Local Loopback Only**: Backend communicates exclusively via 127.0.0.1
- **OAuth2 Gmail Integration**: No plaintext password storage
- **Context Isolation**: Automated browser actions cannot access host system

### Technical Architecture
- **Vision-Tree DOM Compression**: Intelligent page layout analysis optimized for local LLMs
- **ReAct Execution Loop**: Reasoning and Acting framework for autonomous task completion
- **Persistent Task Storage**: SQLite database for task management and scheduling
- **Headless Background Execution**: Run automated tasks without UI interference

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Application Shell                    │
│                     (Electron Frontend)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Chat UI   │  │  Task Mgmt  │  │  Settings & Config  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ Secure Token Auth
┌─────────────────────────────────────────────────────────────┐
│                   Agent Core Engine                          │
│                  (FastAPI + Playwright)                      │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │ Vision-Tree DOM  │  │    ReAct Execution Loop         │  │
│  │   Compression    │  │  (Reason → Act → Observe)       │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ Local API Calls
┌─────────────────────────────────────────────────────────────┐
│                 Local Services & Integrations                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Ollama    │  │  Scheduler  │  │   Gmail OAuth2      │  │
│  │  (LLM Runtime)│  │  (APScheduler)│  │   Integration       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

1. **Install Ollama** (Required for AI functionality)
   ```bash
   # macOS/Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows: Download from https://ollama.ai/download
   
   # Pull a model (recommended: llama3.2)
   ollama pull llama3.2
   ```

2. **Node.js** (v18 or higher)
3. **Python** (v3.10 or higher)

### Installation

#### 1. Install Backend Dependencies
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

#### 2. Install Frontend Dependencies
```bash
cd frontend

# Install Node packages
npm install
```

### Running Sentrix Browser

#### Terminal 1: Start Backend Server
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
python main.py
```

The backend will start on `http://127.0.0.1:8765` and generate a secure execution token at `~/.sentrix/execution_token`.

#### Terminal 2: Start Frontend Application
```bash
cd frontend
npm start
```

### Optional: Start Scheduler Service
```bash
cd backend
source venv/bin/activate
python scheduler.py
```

## 📦 Building for Production

### Build for Windows
```bash
cd frontend
npm run build:win
```
Output: `dist/Sentrix Browser Setup.exe`

### Build for macOS
```bash
cd frontend
npm run build:mac
```
Output: `dist/Sentrix Browser.dmg`

### Build for Linux
```bash
cd frontend
npm run build:linux
```
Output: `dist/Sentrix Browser.AppImage` and `.deb` package

## 🔧 Configuration

### Gmail Integration Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth2 credentials (Desktop application)
5. Download `credentials.json`
6. Rename to `gmail_credentials.json` and place in `~/.sentrix/`

### Custom LLM Model

Edit `backend/main.py` to change the default model:
```python
self.model = "your-preferred-model"  # e.g., "mistral", "codellama"
```

## 📖 Usage Examples

### Chat with Agent
```
User: "Find the latest news about artificial intelligence"
Agent: *Navigates to news site, extracts headlines, summarizes findings*
```

### Schedule a Task
```
Objective: "Check my GitHub notifications"
Schedule: Tomorrow at 9:00 AM
Result: Automated report sent to email
```

### Immediate Execution
```
URL: https://example.com
Objective: "Extract all product prices and save them"
```

## 🔒 Security Considerations

- **Never share your execution token** (`~/.sentrix/execution_token`)
- **Keep Ollama running locally** - do not expose it to the network
- **Review scheduled tasks** before execution
- **Gmail tokens are encrypted** and stored securely in your home directory

## 🛠️ Development

### Project Structure
```
sentrix-browser/
├── backend/
│   ├── main.py              # FastAPI server & agent core
│   ├── scheduler.py         # Background task scheduler
│   ├── gmail_integration.py # Gmail OAuth2 integration
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.js          # Electron main process
│   │   ├── preload.js       # Context bridge
│   │   └── renderer.js      # Frontend logic
│   ├── index.html           # Main UI
│   ├── styles.css           # Styling
│   └── package.json         # Node dependencies
└── README.md
```

### Adding New Features

1. **Backend API**: Add endpoints in `backend/main.py`
2. **Frontend IPC**: Update `preload.js` and `main.js` for new IPC handlers
3. **UI Components**: Modify `index.html` and `renderer.js`

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Playwright](https://playwright.dev/) - Browser automation
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [Electron](https://www.electronjs.org/) - Desktop application framework

---

**Built with ❤️ for the local-first AI community**

For issues and support, please open a GitHub issue.
