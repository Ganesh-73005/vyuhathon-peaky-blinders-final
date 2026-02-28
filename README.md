# 🏪 Hisaab - AI-Powered Kirana Store Management System

<div align="center">

![Hisaab Logo](https://img.shields.io/badge/Hisaab-AI%20Powered-blue?style=for-the-badge)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=flat-square&logo=react)](https://reactjs.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Beanie-47A248?style=flat-square&logo=mongodb)](https://www.mongodb.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange?style=flat-square)](https://groq.com/)

**Empowering Small Businesses with AI-Driven Intelligence**

[Features](#-features) • [Architecture](#-architecture) • [Installation](#-installation) • [Usage](#-usage) • [API Docs](#-api-documentation)

</div>

---

## 📖 Overview

**Hisaab** is an intelligent, voice-enabled Kirana store management system that leverages cutting-edge AI to help small business owners manage inventory, track sales, analyze revenue, and gain actionable business insights—all through natural language conversations.

### 🎯 Problem Statement

Small shop owners struggle with:
- Manual inventory tracking and stock management
- Complex billing and sales recording
- Lack of business insights and competitor analysis
- Time-consuming report generation
- Language barriers with traditional software

### 💡 Solution

Hisaab provides an AI-powered assistant that:
- Understands voice and text commands in multiple languages (English, Hindi, Tamil)
- Manages stock and sales through natural conversations
- Generates professional PDF reports automatically
- Provides festival-based and competitor-driven business insights
- Processes invoices and bills using AI vision

---

## ✨ Features

### 🎤 **Voice & Text Interface**
- **Natural Language Processing**: Talk to your shop assistant in plain language
- **Multi-language Support**: English, Hindi, Tamil
- **Voice Transcription**: Powered by Groq Whisper API
- **Clarification Questions**: AI asks for missing information intelligently

### 📦 **Stock Management**
- Add, update, and query inventory through conversation
- Real-time stock level tracking
- Low stock alerts and reorder point management
- Category-based organization
- Supplier information tracking

### 💰 **Sales & Transaction Management**
- Record sales with voice/text commands
- Multiple payment modes (Cash, UPI, Card, Credit)
- Transaction history with detailed analytics
- Customer profile management

### 📊 **Analytics & Insights**
- **Revenue Analysis**: Daily, weekly, monthly trends
- **Business Summary**: Personalized to your shop type (Kirana, Bakery, etc.)
- **Festival Suggestions**: AI-powered recommendations for upcoming festivals
- **Competitor Analysis**: Location-based market intelligence via SerpAPI
- **Visual Dashboards**: Interactive charts and graphs

### 📄 **PDF Report Generation**
- **Professional 5-Page Reports** with:
  - Cover page with shop branding
  - Business summary with key metrics
  - Sales analysis table
  - Stock inventory with status indicators
  - Visual charts (sales trends, payment distribution)
- One-click download
- Beautiful, print-ready design

### 🔍 **AI-Powered Document Processing**
- **Invoice Parsing**: Upload bills/invoices as images or PDFs
- **Automatic Data Extraction**: AI extracts items, quantities, prices
- **Vision AI**: Powered by Groq Vision models
- **Bulk Processing**: Handle multiple documents

### 🤖 **Multi-Agent Architecture**
- **Stock Agent**: Manages inventory operations
- **Sales Agent**: Handles transaction recording
- **Analytics Agent**: Generates business insights
- **Insights Agent**: Provides market intelligence
- **PDF Agent**: Processes documents
- **Master Orchestrator**: Routes requests intelligently

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
│ (Shop Owner)│
└──────┬──────┘
       │ Voice/Text
       ▼
┌─────────────────────────────────────────────────────────┐
│              React Frontend (Port 3000)                  │
│  • Voice Input  • Dashboard  • Analytics  • Reports     │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
                       ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Backend (Port 8001)                    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │      Master Orchestrator (Central Hub)         │    │
│  │  • NLU Routing  • Context Manager              │    │
│  │  • Session State  • Agent Coordinator          │    │
│  └────────┬───────────────────────────────────────┘    │
│           │                                             │
│  ┌────────┴─────────────────────────────────────┐      │
│  │         Specialized AI Agents                 │      │
│  │  • Stock Agent    • Sales Agent               │      │
│  │  • Analytics Agent • Insights Agent           │      │
│  │  • PDF Processing Agent                       │      │
│  └────────┬─────────────────────────────────────┘      │
└───────────┼──────────────────────────────────────────┘
            │
    ┌───────┴────────┬──────────────┬─────────────┐
    ▼                ▼              ▼             ▼
┌─────────┐   ┌──────────┐   ┌─────────┐   ┌─────────┐
│ MongoDB │   │ Groq API │   │ SerpAPI │   │ Whisper │
│ (Beanie)│   │(Llama 3.3│   │(Market  │   │ (Voice) │
│         │   │   70B)   │   │ Intel)  │   │         │
└─────────┘   └──────────┘   └─────────┘   └─────────┘
```

### Tech Stack

**Frontend:**
- React 18.2.0
- Tailwind CSS
- Lucide Icons
- Sonner (Toast Notifications)

**Backend:**
- FastAPI (Python)
- Beanie ODM (MongoDB)
- Groq API (Llama 3.3 70B)
- Groq Whisper (Voice)
- Groq Vision (Document Processing)
- SerpAPI (Market Intelligence)
- PyMuPDF (PDF Generation)

**Database:**
- MongoDB (Cloud/Local)

---

## 🚀 Installation

### Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **MongoDB** (Local or Atlas)
- **API Keys**:
  - Groq API Key ([Get it here](https://console.groq.com/))
  - SerpAPI Key ([Get it here](https://serpapi.com/))

### 1️⃣ Clone Repository

```bash
git clone <repository-url>
cd vyuhathon1.0-main
```

### 2️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
GROQ_API_KEY=your_groq_api_key_here
SERPAPI_KEY=your_serpapi_key_here
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=hisaab_db
JWT_SECRET=your_secret_key_here
EOF

# Run backend
uvicorn main:app --reload --port 8001
```

### 3️⃣ Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Create .env file
cat > .env << EOF
REACT_APP_API_URL=http://localhost:8001
EOF

# Run frontend
npm start
```

### 4️⃣ Access Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

---

## 📱 Usage

### Getting Started

1. **Sign Up / Login**
   - Create an account with shop details
   - Specify business type (Kirana, Bakery, Medical, etc.)
   - Add location information

2. **Add Stock**
   - Voice: *"Add 50 packets of Maggi at 12 rupees each"*
   - Text: Type in the chat interface
   - Upload: Process invoice PDFs/images

3. **Record Sales**
   - Voice: *"Sold 5 Maggi packets for 70 rupees, cash payment"*
   - Text: Enter transaction details
   - AI asks clarifying questions if needed

4. **View Analytics**
   - Navigate to Dashboard for revenue trends
   - Check Insights page for business recommendations
   - Download PDF reports

### Voice Commands Examples

```
✅ "What's my total stock value?"
✅ "Show me today's sales"
✅ "Add 100 kg rice at 45 rupees per kg"
✅ "Record a sale: 2 bread, 1 milk, total 80 rupees"
✅ "Which items are low in stock?"
✅ "What's my revenue this week?"
```

---

## 📚 API Documentation

### Authentication

```bash
POST /api/auth/signup
POST /api/auth/login
```

### Stock Management

```bash
GET    /api/stock/                    # Get all stock items
POST   /api/stock/                    # Add stock item
PUT    /api/stock/{item_id}           # Update stock
DELETE /api/stock/{item_id}           # Delete stock
```

### Sales & Transactions

```bash
GET  /api/analytics/transactions      # Get transactions
POST /api/analytics/transactions      # Add transaction
GET  /api/analytics/revenue           # Revenue analytics
```

### AI Voice Agent

```bash
POST /api/voice/process               # Process voice input
POST /api/voice/chat                  # Text chat with AI
```

### Insights

```bash
GET /api/insights/summary             # Business summary
GET /api/insights/festivals           # Festival suggestions
GET /api/insights/competitors/detailed # Competitor analysis
```

### Reports

```bash
POST /api/reports/generate            # Generate PDF report
```

**Full API Documentation**: Visit `http://localhost:8001/docs` after starting the backend.

---

## 🎨 Features in Detail

### Multi-Agent Orchestration

The system uses a **Master Orchestrator** that:
1. Analyzes user intent using NLU
2. Loads shop context (stock, sales, user profile)
3. Routes to appropriate specialized agent
4. Manages conversation state
5. Handles clarification loops

### Context-Aware AI

Every agent has access to:
- Current stock inventory
- Recent sales transactions
- User profile and business type
- Location information
- Historical patterns

### Business-Type Personalization

Insights are customized based on your business:
- **Kirana Store**: Rice, Dal, Spices, Groceries
- **Bakery**: Bread, Cakes, Pastries
- **Medical Store**: Medicines, Health products
- **General Store**: Mixed inventory

---

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- API key encryption
- CORS protection
- Input validation and sanitization

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Team

Built with ❤️ for small business owners everywhere.

---

## 🙏 Acknowledgments

- **Groq** for lightning-fast LLM inference
- **MongoDB** for flexible data storage
- **SerpAPI** for market intelligence
- **FastAPI** for robust backend framework
- **React** for beautiful UI

---

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Email: support@hisaab.ai (if applicable)

---

<div align="center">

**Made with 🚀 for Vyuhathon 1.0**

⭐ Star this repo if you find it helpful!

</div>

