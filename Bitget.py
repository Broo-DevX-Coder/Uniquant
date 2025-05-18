import requests,hmac,hashlib,json,base64,math,time
from requests.adapters import HTTPAdapter

# ===================================================================
# Class to fetch data from Bitget ===================================
class BitgetData:
    headers = {'User-Agent': 'Mozilla/5.0'}
    adapters = ["https://api.bitget.com/api/"]
    API_SECRET = ""
    API_KEY = ""
    PASSPHRASE = ""
    API = ""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        ada = HTTPAdapter(pool_connections=100,pool_maxsize=100)
        for i in self.adapters:
            self.session.mount(i,ada)

        self._cached_symbol_data = None
    
    # ==============================================
    # All this just to get * pairs and new pairs ===

    def get_all_symboles(self):
        # Request all available trading pairs
        url = 'https://api.bitget.com/api/v2/spot/public/symbols'
        try:
            response = self.session.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                self._cached_symbol_data = data.get('data', [])
                return self._cached_symbol_data, None, None
            else:
                return [], "response_code", str(response.status_code)
        except requests.RequestException as e:
            return [], "request_code", str(e)

    # get all trading pairs from SQLite ============
    def get_all_trading_pairs(self,quoteCoin:str=None):
        # Get all USDT trading pairs that are online ===============
        trading_pairs, error_type, error_info = self.fetch_symbol_data()
        pairs_info = [
            pair['symbol']
            for pair in trading_pairs if pair['status'] == 'online' and pair['quoteCoin'] == "USDT"
        ]
        return set(pairs_info), error_type, error_info
    
    # Get full information for a specific trading pair ==============
    def get_pair_info(self, symbol: str):
        url = f'https://api.bitget.com/api/v2/spot/public/symbols?symbol={symbol}'
        try:
            response = self.session.get(url, timeout=2)
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('data', [])
                return pairs[0], None, None
            else:
                return None, "response_code", str(response.status_code)
        except requests.RequestException as e:
            return None, "request_code", str(e)

    def get_symboles(self, table_name: str, db):
        # Get all stored symbols from database
        cursor = db.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return set([pair[1] for pair in cursor.fetchall()])
    
    # ===============================================
    # But this to Buy/sell pairs ====================

    # HMAC signature ==================
    def generate_signature(self, timestamp, method, request_path, body=''):
        prehash = f"{timestamp}{method}{request_path}{body}"
        signature = hmac.new(
        self.API_SECRET.encode('utf-8'),
        prehash.encode('utf-8'),
        hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    # to place Buy/Sell orders ==========================
    def place_order(self, symbol:str, side:str, order_type:str ,quantity:dict ,price:dict=None):
        try:
            url = "https://api.bitget.com/api/v2/spot/trade/place-order"
            method = "POST"
            timestamp = str(int(time.time() * 1000))
            safe_amount = math.floor(float(quantity["amount"]) * (10 ** float(quantity["checkScale"]))) / (10 ** float(quantity["checkScale"]))

            body = {
                    "symbol": symbol,      # مثل "BTCUSDT"
                    "side": side,          # "buy" أو "sell"
                    "orderType": order_type,
                    "size": str(safe_amount)
                }

            if order_type == "limit":
                safe_price = math.floor( float(price["price"]) * (10 ** float(price["checkScale"])) ) / (10 ** float(price["checkScale"]))
                body.update({"force":"gtc","price":str(safe_price)})

            body_str = json.dumps(body)
            sign = self.generate_signature(timestamp, method, "/api/v2/spot/trade/place-order", body_str)

            headers = {
                "Content-Type": "application/json",
                "ACCESS-KEY": self.API_KEY,
                "ACCESS-SIGN": sign,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": self.PASSPHRASE
            }

            response = self.session.post(url, headers=headers, data=body_str,timeout=1)

            if response.status_code == 200:
                data = response.json()
                # استخراج الكمية من رصيد الـ BTC أو أي زوج آخر
                return data,None
            else:
                return None,response.text
            
        except requests.RequestException as e:
            return None,str(e)
        
    # To get accont balanses ===========================
    def get_balance(self):
        try:
            timestamp = str(int(time.time() * 1000))
            method = "GET"
            url = "https://api.bitget.com/api/v2/spot/account/assets"
            sign = self.generate_signature(timestamp, method, "/api/v2/spot/account/assets")
    
    
            response = self.session.get(url, headers={
                "Content-Type": "application/json",
                "ACCESS-KEY": self.API_KEY,
                "ACCESS-SIGN": sign,
                "ACCESS-TIMESTAMP": timestamp,
                "ACCESS-PASSPHRASE": self.PASSPHRASE
            })
    
            if response.status_code == 200:
                data = response.json()
                assests = {
                    str(ass["coin"]):{
                        "amount":str(ass["available"]),
                        "frozen":str(ass["frozen"])
                    } 
                    for ass in data["data"] }
                return assests,None
            else:
                return None,response.text
        except requests.RequestException as e:
            return None,str(e)
        
    # To get symbol's curent price ===================
    def get_current_price(self,symbol):
        try:
            url = f"https://api.bitget.com/api/v2/spot/market/tickers?symbol={symbol}"
            response = self.session.get(url)
    
            if response.status_code == 200:
                data = response.json()
                price = data['data'][0]["lastPr"] # السعر الحالي
                return float(price),None
            else:
                return None,response.text
        except requests.RequestException as e:
            return None,str(e)