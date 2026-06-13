from flask import Flask, render_template, jsonify, request
import yfinance as yf
import pandas as pd
from datetime import datetime
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# ── Groq Setup ──────────────────────────────────────────────────────────────
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    print("⚠️  WARNING: GROQ_API_KEY not found in .env file")
    groq_client = None
else:
    groq_client = Groq(api_key=groq_api_key)


# ── Trade Processing ─────────────────────────────────────────────────────────
def process_trades(file_path="trades.csv"):
    df = pd.read_csv(file_path)
    df["Trade Date"] = pd.to_datetime(df["Trade Date"])

    holdings = []
    for symbol, group in df.groupby("Symbol"):
        buys  = group[group["TradeType"] == "buy"]
        sells = group[group["TradeType"] == "sell"]

        total_bought = buys["Quantity"].sum()
        total_sold   = sells["Quantity"].sum()
        net_qty      = total_bought - total_sold

        if net_qty <= 0:
            continue

        total_cost    = (buys["Quantity"] * buys["Price"]).sum()
        sold_cost     = (total_sold / total_bought * total_cost) if total_bought > 0 and total_sold > 0 else 0
        avg_buy_price = (total_cost - sold_cost) / net_qty

        holdings.append({
            "ticker":    symbol,
            "quantity":  int(net_qty),
            "buy_price": round(avg_buy_price, 2),
        })

    return pd.DataFrame(holdings)


# ── Price Fetching ────────────────────────────────────────────────────────────
def fetch_current_prices(tickers):
    """Fetch latest NSE prices for a list of ticker symbols."""
    if not tickers:
        return {}

    tickers_ns = [t + ".NS" for t in tickers]
    try:
        data = yf.download(tickers_ns, period="1d", progress=False)

        price_col = "Close" if "Close" in data.columns else "Adj Close"
        prices    = data[price_col]

        if prices.empty:
            return {t.replace(".NS", ""): 0 for t in tickers_ns}

        latest = prices.iloc[-1]

        # Handle single-ticker case (returns a scalar, not a Series)
        if isinstance(latest, float):
            return {tickers[0]: float(latest)}

        return {t.replace(".NS", ""): float(latest.get(t, 0)) for t in tickers_ns}

    except Exception as e:
        print(f"⚠️  Price fetch error: {e}")
        return {t: 0 for t in tickers}


# ── Portfolio Calculation ─────────────────────────────────────────────────────
def calculate_portfolio(df):
    if df.empty:
        return df, 0.0

    tickers        = df["ticker"].tolist()
    current_prices = fetch_current_prices(tickers)

    df = df.copy()
    df["current_price"] = df["ticker"].map(current_prices).fillna(0)
    df["current_value"] = df["quantity"] * df["current_price"]
    df["buy_value"]     = df["quantity"] * df["buy_price"]
    df["pnl_abs"]       = df["current_value"] - df["buy_value"]
    df["pnl_pct"]       = (df["pnl_abs"] / df["buy_value"].replace(0, float("nan"))) * 100

    total_value     = df["current_value"].sum()
    df["allocation"] = (df["current_value"] / total_value * 100) if total_value > 0 else 0

    return df, total_value


# ── Routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    df = process_trades()
    portfolio_df, total_value = calculate_portfolio(df)

    total_invested = portfolio_df["buy_value"].sum()
    total_pnl_abs  = portfolio_df["pnl_abs"].sum()
    total_pnl_pct  = (total_pnl_abs / total_invested * 100) if total_invested > 0 else 0

    summary = {
        "total_value":    round(total_value,    2),
        "total_invested": round(total_invested, 2),
        "total_pnl_abs":  round(total_pnl_abs,  2),
        "total_pnl_pct":  round(total_pnl_pct,  2),
    }

    portfolio_data = portfolio_df.to_dict(orient="records")
    return render_template("index.html", portfolio=portfolio_data, summary=summary)


@app.route("/chat", methods=["POST"])
def chat():
    if groq_client is None:
        return jsonify({"response": "The AI assistant isn't configured yet. Add your GROQ_API_KEY to the .env file."})

    user_message = request.json.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Hi! What would you like to know about your portfolio?"})

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a warm, knowledgeable portfolio assistant for an Indian retail investor. "
                        "You discuss NSE-listed stocks, portfolio performance, and investment strategy. "
                        "Keep responses concise and friendly. Use ₹ for currency."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=512,
        )
        return jsonify({"response": completion.choices[0].message.content})

    except Exception as e:
        print(f"⚠️  Groq error: {e}")
        return jsonify({"response": "Something went wrong on my end. Please try again."})


if __name__ == "__main__":
    print("🚀 Portfolio Tracker running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000)