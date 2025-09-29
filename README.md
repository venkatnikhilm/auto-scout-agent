# AutoScout 🔍🤖

AutoScout is an **AI-powered monitoring agent** that lets you track prices, product availability, scores, or any website change in real-time — all through **natural language commands**.  

No coding, no scraping rules. Just tell AutoScout what you want, and it does the rest.  

---

## ✨ Features
- 📝 **Natural language input** → *“Track this Nike shoe every hour and alert me if it drops below $250.”*  
- ⚡ **AI-powered extraction with Gemini** → parses user intent into structured fields (URL, condition, interval).  
- 🌐 **Flexible monitoring** → works on product pages, news articles, or live scores.  
- 📩 **Smart notifications** → sends clean email alerts when conditions are met.  
- 🗄️ **DynamoDB persistence** → monitors are stored with conditions, history, and metadata.  
- ⏱️ **Automatic scheduling** → background jobs powered by APScheduler.  

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Python  
- **Frontend**: Vercel (Next.js v0)  
- **Database**: AWS DynamoDB  
- **Cloud Services**: AWS SNS (notifications)  
- **AI**: Google Gemini (2.5-flash) for field extraction + intelligent data parsing  
- **Browser Automation**: Playwright / Selenium for full-page screenshots & scraping  

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+  
- Node.js (if working on frontend)  
- AWS credentials with DynamoDB + SNS access  
- [Google Gemini API key](https://ai.google.dev)  

### Backend Setup
```bash
cd backend
python -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📦 Example Usage
1. Create a monitor:
- Track "object/price/event" from "url" every "time interval" and let me know when "condition"
```

2. AutoScout:
- Extracts fields with **Gemini** (url, condition, interval).  
- Stores the monitor in **DynamoDB**.  
- Schedules background job to run every hour.  
- Checks the page with HTML + screenshot analysis.  
- Sends an **alert** when condition is met.  

---

## 🔑 Example Use Cases
- 👟 Track sneaker drops and price changes.  
- 📈 Monitor stock tickers or crypto prices.  
- 📰 Get notified when a keyword appears in news articles.  
- 🛒 Watch e-commerce sites for restocks or discounts.  
- 🏏 Follow live sports scores with custom conditions.  

---

## 📌 What's Next
- 🌍 Deploy as a SaaS platform (multi-user, dashboards).  
- 📱 Add push notifications / Slack integration.  
- 🧠 Expand Gemini prompts for richer conditions (e.g., “alert me if reviews drop below 4★”).  
- 🔐 Add authentication + user accounts.  

---

## 🤝 Team
Built at **SunHacks 2025**
