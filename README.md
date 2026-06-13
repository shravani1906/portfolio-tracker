# Portfolio Tracker

A clean, full-stack **Portfolio Tracker** built for tracking Indian stock holdings with live market prices and an AI-powered chatbot.

Portfolio Dashboard(https://[portfolio-tracker-product.up.railway.app])

## Features

- **Real Trade History Processing** – Handles multiple buy/sell transactions and calculates **net holdings + weighted average cost**
- **Live Market Prices** – Fetches real-time NSE prices using `yfinance`
- **Accurate P&L Calculation** – Absolute and percentage Profit & Loss
- **Portfolio Allocation** – Visual breakdown of each holding
- **Floating AI Chatbot** – Powered by **Groq + Llama 3** (fast & intelligent)
- **Modern Dark UI** – Responsive design with Tailwind CSS
- **Export Report** – Download portfolio as CSV
- **Production Ready** – Deployed with Gunicorn

## Tech Stack

- **Backend**: Flask
- **Data Processing**: pandas
- **Market Data**: yfinance
- **AI Chatbot**: Groq API (Llama 3)
- **Frontend**: Tailwind CSS + Chart.js ready
- **Deployment**: Railway

## Project Structure

portfolio_tracker/
├── app.py # Main Flask application
├── trades.csv # Your real trade history
├── requirements.txt
├── Procfile # For production deployment
├── .env.example
├── templates/
│ └── index.html # dashboard + AI chatbot
└── README.md

## 🚀 How to Run Locally

# 1. Clone the repo

git clone https://github.com/YOUR_USERNAME/portfolio-tracker.git
cd portfolio_tracker

# 2. Create virtual environment

python -m venv venv
venv\Scripts\activate # Windows

# source venv/bin/activate # Mac/Linux

# 3. Install dependencies

pip install -r requirements.txt

# 4. Setup Groq API key

cp .env.example .env

# Add your Groq key in .env file

# 5. Run the app

python app.py

Open http://127.0.0.1:8080 in your browser.

Live Demo
Live Link: https://portfolio-tracker-product.up.railway.app
(Replace with your actual Railway link once deployed)

Sample Output

Shows net quantity after buys/sells
Real-time current prices (NSE)
P&L (₹ and %)
Allocation % per stock

AI Chatbot
The floating chatbot in the bottom right can answer questions like:

"What's my total P&L?"
"How is RELIANCE performing?"
"Should I hold APARINDS?"

Notes

Uses .NS suffix automatically for Indian stocks
Weighted average buy price calculation for accurate P&L
Fully responsive and mobile-friendly

Made with by Shravani Jamsandekar
Built as part of the Technology Associate application process
