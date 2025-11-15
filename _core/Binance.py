# ---------------------------------------------------------------
# Import libs and modules 
# ---------------------------------------------------------------
import asyncio
import json
import websockets

from index import CoreIndex

# ---------------------------------------------------------------
#  Main Class
# ---------------------------------------------------------------
class Binance(CoreIndex):
    def __init__(self, symbol: str, *args, **kwargs):
        super()._init__(symbol, *args, **kwargs)

    async def update_ob_snapshot(self):
        url = "https://api.binance.com/api/v3/depth"
        params = {"symbol": self.SYMBOL.upper(),"limit": 3000}
        await self._update_ob_snapshot_start()
        try:
            async with self.rest_session.get(url, params=params) as r:
            
                if r.status == 429:self.close();return print("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status == 418:self.close();return print("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status == 403:self.close();return print("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status != 200:
                    self.close()
                    print("[O-R-Imbalance Chart][Binance Depth API]",f"Unexpected HTTP {r.status}")
                
                depth_dict = await r.json()
                await self._update_ob_snapshot_end(depth_dict)
        
        except Exception as e:
            print(e)

    async def orderbook_ws(self):
        url = f"wss://stream.binance.com:9443/ws/{self.SYMBOL.lower()}@depth@100ms"
        self.async_tasks.append(asyncio.create_task(self.update_ob_snapshot()))
        try:
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
                    await self.process_ob_message(data)

                    yield {"asks": self.global_asks, "bids": self.global_bids}

        except Exception as e:
            print(e)

async def main():
    binance_ob = Binance("btcusdt")
    async for ob in binance_ob.orderbook_ws():
        print(ob)

asyncio.run(main())