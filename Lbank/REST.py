# Libraries ================================
import asyncio,aiohttp,sys,os,json
import hmac,hashlib,secrets
import time

# DIRS =====================================
BASE_DIR = os.path.dirname(__file__)

# Packages from projuct ====================
from uniquant.main.__exeptions__ import RequestCodeError,UnknownError

# EndPointes ============================
BASE_URL = "https://api.lbkex.com"
GET_ALL_PAIRS = f"{BASE_URL}/v2/currencyPairs.do"
GET_PAIRS_INFO  = f"{BASE_URL}/v2/accuracy.do"
PLACE_ORDER  = f"{BASE_URL}/v2/supplement/create_order.do"
DEPTH = f"{BASE_URL}/v2/depth.do"

# The client class ====================================
class AsyncClient():
    # Auto (Unused by user) -------------------------------
    def __init__(self,api:str,secret:str):
        self.api_key = api
        self.api_secret = secret
        self.session = aiohttp.ClientSession()
        self.session.headers.update({"Content-Type": "application/x-www-form-urlencoded"})

    # To close the session ...
    async def __aexit__(self,exc_type,exc,tb):
        await self.session.close()

    async def __aenter__(self):
        return self

    # Get the HMAC signateur
    async def genirate_sign(self,body:dict,auth:str):
        sorted_parms = dict(sorted((k, str(v)) for k, v in body.items()))
        strs = "&".join(f"{k}={v}" for k, v in sorted_parms.items())
        pripare_case = hashlib.md5(strs.encode()).hexdigest().upper()
        signature = hmac.new(
            self.api_secret.encode(), pripare_case.encode(), hashlib.sha256
        ).hexdigest()
        return signature


    
    # Manual (Used By User) -------------------------------------------

    # To close connection
    async def close(self):
        await self.session.close()

    # PUBLIC --------------------------------
    # To get all spot trading pairs ...
    async def get_all_pairs(self) -> list:
        try:
            async with self.session.get(GET_ALL_PAIRS) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if data.get("error_code") == 0:
                        pairs = data.get("data",[])
                        return set(pairs)
                    else:
                        raise RequestCodeError(f"{data.get('error_code')} | With a message from server >> {data.get('msg')}")
                
                else:
                    raise RequestCodeError(f"{resp.status}")
        except Exception as e:
            raise UnknownError(e)
        
    # To get all pairs whith thier base informations or get just one pair informations
    async def get_pairs_info(self,symbol:str=None) -> list:
        try:
            URL = f"{GET_PAIRS_INFO}?symbol={symbol}" if symbol != None else f"{GET_PAIRS_INFO}"
            async with self.session.get(URL) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    if data.get("error_code") == 0:
                        pairs = data.get("data",[])
                        return pairs
                    else:
                        raise RequestCodeError(f"{data.get('error_code')} | With a message from server >> {data.get('msg')}")
                
                else:
                    raise RequestCodeError(f"{resp.status}")
        except Exception as e:
            raise UnknownError(e)
        
    async def order_book(self,code:str,limit:int):
        try:
            url = f"{DEPTH}?size={limit}&symbol={code}"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("error_code") == 0:
                        return data
                    else:
                        raise RequestCodeError(f"{data.get('error_code')} | With a message from server >> {data.get('msg')}")
                else:
                    raise RequestCodeError(f"{resp.status}")
        except Exception as e:
            raise UnknownError(e)
        

    # PRIVATE --------------------------------- 
    # to place any spot order    
    async def place_order(self, symbol: str, type_: str, amount: dict, price: dict = None):
        if not amount.get('value') or not amount.get('checkScal'):
            raise ValueError("You must provide amount as {'value':float ,'checkScal':int} ")
    
        if amount.get('value') is None or amount.get('checkScal') is None:
            raise ValueError("Amount values can't be None.")

        body = {
            "symbol": symbol,
            "api_key": self.api_key,
        }

        if type_ in ["buy_limit", "sell_limit", "buy", "sell"]:
            if price is None:
                raise ValueError("Price is required for limit orders.")
            body.update({
                "price": str(round(price.get('value'), price.get('checkScal'))),
                "amount": str(round(amount.get('value'), amount.get('checkScal'))),
            })
            body["type"] = "buy" if "buy" in type_ else "sell"

        elif type_ in ["buy_market", "sell_market"]:
            body.update({
                "amount": str(round(amount.get('value'), amount.get('checkScal'))),
                "type":type_
            })
        else:
            raise ValueError("Invalid order type.")

        body.update({
            "timestamp": str(int(time.time() * 1000)),
            "signature_method": "HmacSHA256",
            "echostr": secrets.token_hex(20)
        })

        headers = {
            "timestamp": str(int(time.time() * 1000)),
            "signature_method": "HmacSHA256",
            "echostr": secrets.token_hex(20)
        }
        sign_parms = headers.copy()
        sign_parms.update({"api_key": self.api_key})

        body["sign"] = str(await self.genirate_sign(body,symbol))

        async with self.session.post(PLACE_ORDER, data=body) as resp:
            resp_json = await resp.text()
            print(f"{resp_json} -> {symbol}")