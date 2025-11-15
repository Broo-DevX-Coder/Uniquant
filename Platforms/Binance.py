# ---------------------------------------------------------------
# Import libs and modules 
# ---------------------------------------------------------------
import asyncio
import json
import websockets

from socket import gaierror
from main import *

# ---------------------------------------------------------------
#  Main Class
# ---------------------------------------------------------------
class Binance(PlatformIndex):
    def __init__(self, symbol: str, *args, **kwargs):
        super()._init__(symbol, *args, **kwargs)
        self.platform_name = "Binance"

    # Update the order book snapshot from Binance REST API
    async def update_ob_snapshot(self):
        url = "https://api.binance.com/api/v3/depth"
        params = {"symbol": self.SYMBOL.upper(),"limit": 3000}
        await self._update_ob_snapshot_start()
        try:
            async with self.rest_session.get(url, params=params) as r:

                if r.status == 429:  raise Error429("Get Orderbook Snapshot | Binance API")
                if r.status == 418:  raise Error418("Get Orderbook Snapshot | Binance API")
                if r.status == 403:  raise Error403("Get Orderbook Snapshot | Binance API")
                if r.status != 200:  raise RequestCodeError(r.status)

                logging.info("Get Orderbook Snapshot | Binance API >> Success")
                
                depth_dict = await r.json()
                await self._update_ob_snapshot_end(depth_dict)
        
        except (aiohttp.ClientConnectionError,gaierror):
            raise ConnectionError("Get Orderbook Snapshot | Binance API")
        except Exception as e:
            raise UnknownError(f"Get Orderbook Snapshot | Binance API >> {e}")

    # WebSocket connection to receive real-time order book updates
    async def orderbook_ws(self):
        url = f"wss://stream.binance.com:9443/ws/{self.SYMBOL.lower()}@depth@100ms"
        self.async_tasks.append(asyncio.create_task(self.update_ob_snapshot()))
        try:
            logging.info(f"WebSocket Orderbook | Binance API >> Connected to {url}")
            async with websockets.connect(url) as ws:
                while True:
                    resp = await ws.recv()
                    msg = json.loads(resp)
                    data = {
                        "lastUpdateId": int(msg.get("u")),
                        "firstUpdateId": int(msg.get("U")),
                        "bids": msg.get("b"),
                        "asks": msg.get("a")
                    }
                    f = await self.process_ob_message(data)

                    if f:
                        yield {"asks": self.global_asks, "bids": self.global_bids}

        except websockets.exceptions.ConnectionClosedError:
            raise WebSocketClosedError("WebSocket Orderbook | Binance API")
        except (OSError, websockets.exceptions.InvalidStatus, gaierror) as e:
            raise ConnectionError(f"WebSocket Orderbook | Binance API >> {e}")
        except Exception as e:
            raise UnknownError(f"WebSocket Orderbook | Binance API >> {e}")