import yfinance as yf
import requests
from flask import Flask, jsonify, request

# Initialize Flask app
app = Flask(__name__)

def lookup(symbol):
    """
    Look up quote for a specific symbol using yfinance.
    Attempts to find common international symbols by appending suffixes if direct lookup fails.
    Returns stock info dictionary on success, "None" (string) on failure.
    """
    original_symbol_upper = symbol.upper().strip()

    # List of common suffixes for major global exchanges.
    # Order can matter for performance (most common first).
    common_suffixes = [
        "",         # Try original symbol first (e.g., for US stocks or already suffixed)
        ".NS",      # India - NSE
        ".BO",      # India - BSE
        ".SI",      # Singapore
        ".L",       # UK - London Stock Exchange
        ".PA",      # France - Euronext Paris
        ".DE",      # Germany - Xetra / Frankfurt
        ".AX",      # Australia - ASX
        ".TO",      # Canada - Toronto Stock Exchange
        ".HK",      # Hong Kong
        ".MI",      # Italy - Milan
        ".KS",      # South Korea - Korea Exchange
        ".MC",      # Spain - Madrid
        ".SW",      # Switzerland - SIX Swiss Exchange
        ".BR",      # Belgium - Euronext Brussels
        ".IR",      # Ireland - Euronext Dublin
        ".SA"       # Brazil - Bovespa / Saudi Arabia - Tadawul
    ]

    symbols_to_try = []

    # Add the original symbol first
    symbols_to_try.append(original_symbol_upper)

    # Add suffixed versions if the original symbol doesn't already have a recognized suffix
    has_known_suffix = False
    for suffix_check in common_suffixes:
        if suffix_check and original_symbol_upper.endswith(suffix_check.upper()):
            has_known_suffix = True
            break
    
    if not has_known_suffix:
        for suffix_to_add in common_suffixes:
            if suffix_to_add: # Don't re-add an empty string suffix
                symbols_to_try.append(original_symbol_upper + suffix_to_add)

    # Use a set to maintain uniqueness and avoid redundant lookups
    unique_symbols_to_try = list(dict.fromkeys(symbols_to_try)) # Preserves order while removing duplicates

    for s in unique_symbols_to_try:
        try:
            # print(f"DEBUG: Attempting lookup for symbol: {s}")

            ticker = yf.Ticker(s)
            hist = ticker.history(period="1d", auto_adjust=True)

            if hist.empty:
                hist = ticker.history(period="5d", auto_adjust=True)
            
            if not hist.empty:
                price = round(float(hist["Close"].iloc[-1]), 2)
                company_info = ticker.info
                name = company_info.get("longName") or company_info.get("shortName") or s

                if price > 0:
                    # print(f"DEBUG: Found data for {s}: {name}, ${price}")
                    return {
                        "name": name,
                        "price": price,
                        "symbol": s
                    }
                # else:
                    # print(f"DEBUG: Price is zero or invalid for {s}. Data might be incomplete. Trying next symbol.")
            # else:
                # print(f"DEBUG: No historical data found for {s} after trying 1d and 5d periods. Trying next symbol.")

        except requests.exceptions.HTTPError as http_err:
            # print(f"Error (HTTP) during lookup for '{s}': {http_err} - might be a subscription issue or invalid symbol. Trying next symbol.")
            pass # Continue to next symbol if HTTP error
        except requests.exceptions.ConnectionError as conn_err:
            # print(f"Error (Connection) during lookup for '{s}': {conn_err} - check internet connection or yfinance server. Trying next symbol.")
            pass # Continue to next symbol if connection error
        except Exception as e:
            # print(f"General error looking up '{s}': {e}. Trying next symbol.")
            pass # Continue to next symbol for other exceptions

    # If no symbol from the list yields valid data after all attempts
    # print(f"DEBUG: Failed to find valid data for original input: {original_symbol_upper}")
    return "None" # Returns the string "None" as per your previous implementation

@app.route('/quote_api', methods=['GET'])
def get_stock_quote():
    """
    API endpoint to get a stock quote.
    Expects a 'symbol' query parameter.
    Example: /quote_api?symbol=AAPL
    """
    print("hello") # This prints to the Render logs, not to the client
    symbol = request.args.get('symbol')

    if not symbol:
        return jsonify({"error": "Missing 'symbol' parameter"}), 400

    stock_info = lookup(symbol)

    if stock_info != "None": # Check for the string "None"
        return jsonify(stock_info), 200
    else:
        # Provide a more specific error message in the API response
        return jsonify({
            "error": f"Could not find stock for '{symbol}'. "
            "Please provide an exact ticker symbol. If it's an international stock, "
            "include its exchange suffix. Examples: "
            "'TATAMOTORS.NS' (India - NSE), 'D05.SI' (Singapore - SGX), "
            "'OR.PA' (France - Euronext Paris), 'HSBA.L' (UK - LSE), 'SHOP.TO' (Canada - TSX)."
        }), 404 # Not Found

if __name__ == '__main__':
    # Run the Flask app on a specific port.
    # In a production environment, you would use a WSGI server like Gunicorn.
    app.run(debug=True, port=5000)
