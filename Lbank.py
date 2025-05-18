# Libraries ================================
import asyncio,aiohttp
from __exeptions__ import RequestCodeError,UnknownError

# EndPointes ============================
BASE_URL = "https://api.lbkex.com"
GET_ALL_PAIRS = f"{BASE_URL}/v2/currencyPairs.do"
GET_PAIRS_INFO  = f"{BASE_URL}/v2/accuracy.do"

# The client class =========================
class Client():
    def __init__(self,api:str,secret:str):
        self.api_key = api
        self.api_secret = secret

    # To start the session ...
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    # To close the session ...
    async def __aexit__(self,exc_type,exc,tb):
        await self.session.close()

    # To get all spot trading pairs ...
    async def get_all_pairs(self) -> list:
        try:
            async with self.session.get(GET_ALL_PAIRS) as resp:
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
                


# ============================================
# ============================================
async def main():
    async with Client("ll","jj") as client:
        print(await client.get_all_pairs())

asyncio.run(main())
