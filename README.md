# 🌍 TRIP-Planner WanderMind

**WanderMind** is an AI-powered travel planning web application built with Flask. It helps users create personalized travel itineraries, research destinations, compare locations, optimize budgets, and manage packing lists—all powered by local AI models.

---

## ✨ Features

### 1. **Travel Plan Generator** 🗺️
Generate AI-powered travel itineraries based on:
- Origin and destination
- Budget constraints
- Trip duration
- Personal interests

### 2. **Destination Research** 🔍
Deep dive into any destination with:
- Live web scraping from travel sources (WikiVoyage, WikiTravel, Numbeo)
- Cost-of-living data
- Local attractions and tips
- Travel guidelines and recommendations

### 3. **AI Chat Assistant** 💬
Interactive chat for:
- Real-time travel advice
- Destination questions
- Itinerary customization
- Local recommendations
- Multi-turn conversations with memory

### 4. **Destination Comparator** ⚖️
Compare multiple destinations side-by-side:
- Weather comparison
- Cost analysis
- Attractions and activities
- Best time to visit
- Travel convenience metrics

### 5. **Budget Optimizer** 💰
Smart budget planning:
- Per-day expense breakdown
- Category-wise allocation
- Cost estimation by destination
- Money-saving recommendations

### 6. **Smart Packing List** 🎒
Generate intelligent packing lists:
- Weather-appropriate suggestions
- Destination-specific items
- Duration-based recommendations
- Activity-based essentials

### 7. **My Trips Memory** 📚
- View and manage all saved trips
- Access previous itineraries
- Trip history and statistics

---

## 🏗️ Project Structure

```
travelplanner/
├── app.py                        # Main Flask application
├── test_api.py                   # API testing utilities
├── .env                          # Environment variables (create this)
├── .gitignore                    # Git ignore rules
│
├── memory/
│   ├── memento.py               # Memory management (Memento pattern)
│   └── memory_store.json        # Persistent trip storage
│
├── services/
│   ├── ollama_service.py        # Local LLM service (Ollama)
│   ├── firecrawl_service.py     # Web scraping service
│   └── memento.py               # Memory utilities
│
├── templates/
│   ├── index.html               # Homepage
│   ├── planner.html             # Travel planner form
│   ├── result.html              # Generated itinerary
│   ├── research.html            # Destination research
│   ├── chat.html                # AI chat interface
│   ├── compare.html             # Destination comparison
│   ├── budget.html              # Budget optimizer
│   ├── packing.html             # Packing list generator
│   └── trips.html               # Saved trips viewer
│
└── static/
    ├── css/
    │   └── style.css            # Global styling
    └── js/
        └── script.js            # Frontend functionality
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Flask** (web framework)
- **Ollama** (local LLM server) - [Download](https://ollama.ai)
- **pip** (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rg0rajesh/TRIP-Planer_WanderMind.git
   cd TRIP-Planer_WanderMind
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Key dependencies:
   - Flask
   - python-dotenv
   - requests
   - ollama
   - firecrawl-py (optional)

4. **Set up Ollama**
   ```bash
   ollama pull llama3.2  # or any other model: mistral, qwen2.5, deepseek-r1
   ollama serve          # Start the Ollama server
   ```

---

## ⚙️ Configuration

### Environment Variables (.env)

Create a `.env` file in the root directory:

```env
# Ollama Configuration
OLLAMA_MODEL=llama3.2
OLLAMA_HOST=http://127.0.0.1:11434

# Firecrawl Configuration (Optional - for web scraping)
FIRECRAWL_API_KEY=your_firecrawl_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

**Note:** If `FIRECRAWL_API_KEY` is not set, the app uses enriched fallback data.

---

## 🎯 Running the Application

1. **Start Ollama server** (in a separate terminal):
   ```bash
   ollama serve
   ```

2. **Activate virtual environment** (if not already active):
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Run Flask app**:
   ```bash
   python app.py
   ```

4. **Access the application**:
   ```
   http://localhost:5000
   ```

---

## 📡 API Endpoints

### Page Routes
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage |
| `/planner` | GET | Travel planner form |
| `/result` | GET | Display generated itinerary |
| `/research` | GET | Destination research page |
| `/chat` | GET | AI chat interface |
| `/compare` | GET | Destination comparator |
| `/budget` | GET | Budget optimizer |
| `/packing` | GET | Packing list generator |
| `/trips` | GET | Saved trips viewer |

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/plan` | POST | Generate travel itinerary |
| `/api/research` | POST | Research destination |
| `/api/compare` | POST | Compare destinations |
| `/api/chat` | POST | Chat with AI assistant |
| `/api/budget` | POST | Optimize budget |
| `/api/packing` | POST | Generate packing list |

---

## 🤖 AI Services

### Ollama Service
- **Local LLM Integration**: Runs language models locally without cloud dependencies
- **Default Model**: `llama3.2` (customizable via `OLLAMA_MODEL` env var)
- **Supported Models**: llama3.2, mistral, qwen2.5, deepseek-r1, and more
- **Benefits**: Privacy-first, no API costs, complete control

### Firecrawl Service
- **Web Scraping**: Collects real-time travel data from:
  - WikiVoyage (comprehensive travel guides)
  - WikiTravel (community travel tips)
  - Numbeo (cost-of-living data)
- **Fallback Mode**: Uses enriched placeholder data if API key unavailable
- **Optional**: Not required to run the application

---

## 💾 Memory System

The application uses the **Memento Pattern** for trip persistence:
- Stores trip history in `memory/memory_store.json`
- Enables users to access previous itineraries
- Supports trip history and statistics

---

## 🔧 Troubleshooting

### Ollama Not Connected
```
Error: Ollama service not available
```
**Solution:**
1. Ensure Ollama is running: `ollama serve`
2. Check Ollama host is correct in `.env` (default: `http://127.0.0.1:11434`)
3. Pull the model: `ollama pull llama3.2`

### Model Not Found
```
[Ollama] ⚠ Model 'llama3.2' not found locally.
```
**Solution:**
```bash
ollama pull llama3.2
```

### Firecrawl API Issues
If web scraping fails, the app automatically uses fallback data.
To enable: Set `FIRECRAWL_API_KEY` in `.env`

### Port Already in Use
```
Address already in use: ('127.0.0.1', 5000)
```
**Solution:**
```bash
python app.py --port 5001
```

---

## 📦 Dependencies

```
Flask==3.0.0+
python-dotenv==1.0.0+
requests==2.31.0+
ollama==0.0.40+
firecrawl-py==0.0.1+  (optional)
```

Install all:
```bash
pip install flask python-dotenv requests ollama firecrawl-py
```

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 👥 Author

**Rajesh** - [GitHub Profile](https://github.com/Rg0rajesh)

---

## 🌟 Support

If you find this project helpful, please give it a ⭐ star on GitHub!

For issues or questions, please open an [issue](https://github.com/Rg0rajesh/TRIP-Planer_WanderMind/issues).

---

## 🔗 Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Firecrawl Documentation](https://docs.firecrawl.dev/)
- [WikiVoyage](https://en.wikivoyage.org/)
- [Numbeo Travel Costs](https://www.numbeo.com/)