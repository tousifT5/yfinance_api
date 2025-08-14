import yfinance as yf
import requests
from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

def lookup(symbol):
    """
    Look up quote for a specific symbol using yfinance.
    Does not attempt fuzzy matching or suffix appending.
    Returns stock info dictionary on success, None on failure.
    """
    symbol_upper = symbol.upper().strip()

    try:
        # print(f"DEBUG: Attempting direct lookup for symbol: {symbol_upper}") # Debugging print

        ticker = yf.Ticker(symbol_upper)
        hist = ticker.history(period="1d", auto_adjust=True)

        if hist.empty:
            hist = ticker.history(period="5d", auto_adjust=True)
        
        if not hist.empty:
            price = round(float(hist["Close"].iloc[-1]), 2)
            company_info = ticker.info
            name = company_info.get("longName") or company_info.get("shortName") or symbol_upper

            if price > 0:
                # print(f"DEBUG: Found data for {symbol_upper}: {name}, ${price}")
                return {
                    "name": name,
                    "price": price,
                    "symbol": symbol_upper
                }
            else:
                # print(f"DEBUG: Price is zero or invalid for {symbol_upper}. Data might be incomplete.")
                return None
        else:
            # print(f"DEBUG: No historical data found for {symbol_upper} after trying 1d and 5d periods.")
            return None

    except requests.exceptions.HTTPError as http_err:
        # print(f"Error (HTTP) during lookup for '{symbol_upper}': {http_err} - might be a subscription issue or invalid symbol.")
        return None
    except requests.exceptions.ConnectionError as conn_err:
        # print(f"Error (Connection) during lookup for '{symbol_upper}': {conn_err} - check internet connection or yfinance server.")
        return None
    except Exception as e:
        # print(f"General error looking up '{symbol_upper}': {e}")
        return None


@app.route('/quote_api', methods=['GET'])
def get_stock_quote():
    """
    API endpoint to get a stock quote.
    Expects a 'symbol' query parameter.
    Example: /quote_api?symbol=AAPL
    """
    print("hello")
    symbol = request.args.get('symbol')

    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400

    stock_info = lookup(symbol)

    if stock_info:
        return jsonify(stock_info), 200
    else:
        # Provide a more specific error message in the API response
        return jsonify({
            "error": f"Could not find stock for '{symbol}'. "
            "Try providing the exact ticker symbol, including exchange suffixes "
            "for international stocks. For example: "
            "'TATAMOTORS.NS' (India - NSE), 'D05.SI' (Singapore - SGX), "
            "'OR.PA' (France - Euronext Paris), 'HSBA.L' (UK - LSE)."
        }), 404 # Not Found

if __name__ == '__main__':
    # Run the Flask app on a specific port.
    # In a production environment, you would use a WSGI server like Gunicorn.
    app.run()
