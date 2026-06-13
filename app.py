from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Groq Setup ──────────────────────────────────────────────────────────────
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = None
if groq_api_key:
    try:
        groq_client = Groq(api_key=groq_api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"⚠️ Groq init failed: {e}")
else:
    print("⚠️ WARNING: GROQ_API_KEY not found")

# ── Trade Processing ─────────────────────────────────────────────────────────
def process_trades(file_path="trades.csv"):
    df = pd.read_csv(file_path)
    df["Trade Date"] = pd.to_datetime(df["Trade Date"])

    holdings = []
    for symbol, group in df.groupby("Symbol"):
        buys = group[group["TradeType"] == "buy"]
        sells = group[group["TradeType"] == "sell"]

        total_bought = buys["Quantity"].sum()
        total_sold = sells["Quantity"].sum()
        net_qty = total_bought - total_sold

        if net_qty <= 0:
            continue

        total_cost = (buys["Quantity"] * buys["Price"]).sum()
        sold_cost = (total_sold / total_bought * total_cost) if total_bought > 0 and total_sold > 0 else 0
        avg_buy_price = (total_cost - sold_cost) / net_qty

        holdings.append({
            "ticker": symbol,
            "quantity": int(net_qty),
            "buy_price": round(avg_buy_price, 2),
        })

    return pd.DataFrame(holdings)


# ── Price Fetching ────────────────────────────────────────────────────────────
def fetch_current_prices(tickers):
    if not tickers:
        return {}
    tickers_ns = [t + ".NS" for t in tickers]
    try:
        data = yf.download(tickers_ns, period="2d", progress=False, threads=False)
        if data.empty:
            return {t: 0.0 for t in tickers}

        price_col = "Close" if "Close" in data.columns else "Adj Close"
        prices = data[price_col]

        latest = prices.iloc[-1]
        if isinstance(latest, float):  # single ticker
            return {tickers[0]: round(float(latest), 2)}

        return {t.replace(".NS", ""): round(float(latest.get(t, 0)), 2) for t in tickers_ns}
    except Exception as e:
        print(f"⚠️ yfinance error: {e}")
        return {t: 0.0 for t in tickers}


# ── Portfolio Calculation ─────────────────────────────────────────────────────
def calculate_portfolio(df):
    if df.empty:
        return df, 0.0

    tickers = df["ticker"].tolist()
    current_prices = fetch_current_prices(tickers)

    df = df.copy()
    df["current_price"] = df["ticker"].map(current_prices).fillna(0)
    df["current_value"] = df["quantity"] * df["current_price"]
    df["buy_value"] = df["quantity"] * df["buy_price"]
    df["pnl_abs"] = df["current_value"] - df["buy_value"]
    df["pnl_pct"] = (df["pnl_abs"] / df["buy_value"].replace(0, float("nan"))) * 100

    total_value = df["current_value"].sum()
    df["allocation"] = (df["current_value"] / total_value * 100) if total_value > 0 else 0

    return df, total_value


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    try:
        df = process_trades()
        portfolio_df, total_value = calculate_portfolio(df)

        total_invested = portfolio_df["buy_value"].sum()
        total_pnl_abs = portfolio_df["pnl_abs"].sum()
        total_pnl_pct = (total_pnl_abs / total_invested * 100) if total_invested > 0 else 0

        summary = {
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_pnl_abs": round(total_pnl_abs, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
        }

        portfolio_data = portfolio_df.to_dict(orient="records")
        return render_template("index.html", portfolio=portfolio_data, summary=summary)
    except Exception as e:
        print(f"❌ Error in index route: {e}")
        return f"<h1 style='color:red'>Error: {str(e)}</h1><br><p>Check logs or ensure trades.csv and templates/index.html exist.</p>", 500


@app.route("/chat", methods=["POST"])
def chat():
    if groq_client is None:
        return jsonify({"response": "AI assistant not configured. Add GROQ_API_KEY in Railway Variables."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Hi Shravani! 💕 What would you like to know about your portfolio today?"})

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a warm, knowledgeable portfolio assistant for Shravani. Use ₹ symbol. Keep answers friendly and concise."
                },
                {"role": "user", "content": user_message},
            ],
            model="llama3-8b-8192",          # Safe & fast model
            temperature=0.7,
            max_tokens=512,
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        print(f"Groq error: {e}")
        return jsonify({"response": "Sorry baby, Groq is a bit slow right now. Try again in a moment ❤️"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Portfolio Tracker running on http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)