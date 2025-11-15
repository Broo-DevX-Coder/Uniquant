import json
import logging
import os

import httpx
import websockets

from core.utils import TIME_FRAMES_INTERVALS

# To force the program to use PySide2
os.environ["PYQTGRAPH_QT_LIB"] = "PySide2"

import time
import asyncio
import pandas as pd
import pyqtgraph as pg

import aiohttp
from socket import gaierror
import qasync
import asyncio

from PySide2 import QtCore, QtGui
from PySide2.QtWidgets import *

from .utils import *

binance_charts_theme()

class ImbalanceChart(pg.GraphicsLayoutWidget):
    """Real-time Binance trade & depth imbalance chart"""

    # ===== Set ChowChart items ======
    chowcharts_item = {"imbalance_l":{},"depth_l":{},}

    def __init__(self,**keyargs):
        super().__init__()
        self.async_tasks = []
        self.setStyleSheet(QSS_BINANCE_STYLE)
        
        time_frame = to_milliseconds(keyargs["time_frame"])
        self.TIME_MS: int =  time_frame[0]  # Frame duration in ms
        self.SYMBOL = keyargs["symbol"]
        self.IMBALANCE_LEVEL = int(keyargs["imbalance_level"])
        self.DEPTH_LEVEL = int(keyargs["depth_level"])
        self.VALUE_PAST = int(keyargs["value_past"])
        self.INTERVAL_PAST = str(keyargs["interval_past"])
        self.LAST_CENTER = keyargs["last_centered"]

        self.global_asks = {}
        self.global_bids = {}
        self.snapshot_update = 0
        self.snapshot_update_status = 0
        self.updates = {}
        self.bests_ob = {"min":{"asks":0,"bids":0},"max":{"asks":0,"bids":0}}

        self.rest_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(20))

        logging.info(f"Start OBI-VOI Indecator for `{self.SYMBOL.upper()}`")

        # Window settings
        self.resize(800, 500)
        self.setWindowTitle(f"{self.SYMBOL} order-book and real-time imbalance")

        # Create custom time axis and view box
        self.time_axis = TimeAxis(orientation="bottom")
        self.VB = pg.ViewBox()
        self.VB.setLimits(yMin=-2, yMax=2)                     # Y-axis limits
        self.VB.setLimits(xMin=self.time_n())                  # X-axis min limit

        # Create plot with grid
        self.plot = self.addPlot(viewBox=self.VB, axisItems={"bottom": self.time_axis})
        self.plot.showGrid(x=True, y=True, alpha=0.1)           # Light grid lines

        # Initial axis ranges
        self.VB.setYRange(-1.1, 1.1)
        self.VB.setXRange(self.time_n(), self.time_n() + 50 * 1000)

        # ===== Widget & Style Storage =====
        self.styles = {}
        self.widgets = {"cursor": {}, "curves": {"trades": {}, "depth": {}}}

        # Background color creator
        self.styles["bg"] = lambda x: QtGui.QColor(str(x))
        self.styles["DashLine"] = QtCore.Qt.DashLine
        self.TOP_Z_VALUE = lambda x: x.setZValue(1000)  # Keep item on top

        # Cursor line factory
        self.widgets["cursor"]["lambda"] = lambda angle, style=self.styles["DashLine"], color=(255, 255, 255, 150), width=0.5: pg.InfiniteLine(
            angle=float(angle),
            pen=pg.mkPen(color=color, width=width, style=style),
            movable=False
        )

        # Cursor elements
        self.widgets["cursor"]["vline"] = self.widgets["cursor"]["lambda"](90)   # Vertical
        self.widgets["cursor"]["hline"] = self.widgets["cursor"]["lambda"](0)    # Horizontal
        self.widgets["cursor"]["label_pos"] = pg.TextItem()                     # Label near cursor
        self.widgets["cursor"]["label_pos2"] = pg.TextItem(fill=self.styles["bg"]("#6B7AFF"))  # Side label
        self.widgets["0_line"] = self.widgets["cursor"]["lambda"](angle=0, color="white", style=None)  # Zero line

        # Top label
        self.widgets["top_label"] = pg.TextItem(html=f"<font color='white'>Time Frame: {time_frame[1]}</font><br><font color='yellow'>Order Book Imbalance</font><br><font color='red'>Real Time Imbalance</font>")
        self.plot.addItem(self.widgets["top_label"])
        self.TOP_Z_VALUE(self.widgets["top_label"])
        self.widgets["top_label"].setPos(self.VB.viewRect().left(), self.VB.viewRect().bottom())

        # Top label set pos
        self.widgets["top_label"].setPos(self.VB.viewRect().left(),self.VB.viewRect().bottom())

        # Add cursor items to plot
        for item in ("vline", "hline", "label_pos", "label_pos2"):
            self.plot.addItem(self.widgets["cursor"][item])
            self.TOP_Z_VALUE(self.widgets["cursor"][item])
        self.plot.addItem(self.widgets["0_line"])

        # Initialize curve data arrays
        self.widgets["curves"]['trades']["X"] = [self.time_n()]
        self.widgets["curves"]['trades']["Y"] = [0]
        self.widgets["curves"]['depth']["X"] = [self.time_n()]
        self.widgets["curves"]['depth']["Y"] = [0]

        # Create plot curves
        self.widgets["curves"]['trades']["plot"] = self.plot.plot([0], [0], pen=pg.mkPen(color='r', width=2), ignoreBounds=True)
        self.widgets["curves"]['depth']["plot"] = self.plot.plot([0], [0], pen=pg.mkPen(color='y', width=2), ignoreBounds=True)

        # Mouse move tracking
        self.scene().sigMouseMoved.connect(self.mouse_moved)
        self.VB.sigResized.connect(self.update_labels_pos)
        self.VB.sigRangeChanged.connect(lambda _, __: self.update_labels_pos())

    def mouse_moved(self, pos):
        """Update cursor position & labels when mouse moves"""
        if self.plot.sceneBoundingRect().contains(pos):
            vb = self.plot.getViewBox()
            mouse_point = vb.mapSceneToView(pos)
            x_, y_ = mouse_point.x(), mouse_point.y()

            # Move cursor lines
            self.widgets["cursor"]["vline"].setPos(x_)
            self.widgets["cursor"]["hline"].setPos(y_)

            # Move and update labels
            self.widgets["cursor"]["label_pos"].setPos(x_, y_)
            self.widgets["cursor"]["label_pos2"].setY(y_)
            GlobalCursor.set_label_pos(self.widgets["cursor"]["label_pos"],date_str=DATE(x_),value_n="Imbalance",value_v=y_)
            GlobalCursor.set_label_pos2(self.widgets["cursor"]["label_pos2"],y_)
            self.scene().update()

    def time_n(self):
        """Return current time in milliseconds"""
        return time.time() * 1000
    
    def update_labels_pos(self):
        self.widgets["top_label"].setPos(self.VB.viewRect().left(), self.VB.viewRect().bottom())
        self.widgets["cursor"]["label_pos2"].setX(self.VB.viewRect().left())

    async def _update_depth_rest(self):
        url = "https://api.binance.com/api/v3/depth"
        params = {"symbol": self.SYMBOL.upper(),"limit": self.DEPTH_LEVEL}
        self.snapshot_update_status = 0
        try:
            async with self.rest_session.get(url, params=params) as r:
            
                if r.status == 429:self.close();return error_429("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status == 418:self.close();return error_418("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status == 403:self.close();return error_403("[O-R-Imbalance Chart][Binance Depth API]")
                if r.status != 200:
                    self.close()
                    unknown_error("[O-R-Imbalance Chart][Binance Depth API]",f"Unexpected HTTP {r.status}")
                depth_dict = await r.json()
                self.snapshot_update = depth_dict.get("lastUpdateId")
                self.snapshot_update_status = 10

                self.global_asks = {float(p):float(q) for p,q in depth_dict.get("asks")}
                self.global_bids = {float(p):float(q) for p,q in depth_dict.get("bids")}
                self.bests_ob = {
                    "min":{
                        "asks":min(self.global_asks.keys()),
                        "bids":min(self.global_bids.keys())
                    },
                    "max":{
                        "asks":max(self.global_asks.keys()),
                        "bids":max(self.global_bids.keys())
                    }}
                logging.info("[O-R-Imbalance Chart][Binance Depth API] Get ordrbook Snapshot")

        except (aiohttp.ClientConnectionError,gaierror):
            self.close()
            return connection_error("[O-R-Imbalance Chart][Binance Depth API]")
        except Exception as e:
            self.close()
            return unknown_error("[O-R-Imbalance Chart][Binance Depth API]",f"Unexpected polling error: {e}")
        

    async def _get_days_past(self):
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": self.SYMBOL.upper(),"interval": self.INTERVAL_PAST,"limit": self.VALUE_PAST}
        self.snapshot_update_status = 0
        try:
            async with self.rest_session.get(url, params=params) as r:
                if r.status == 429:self.close();return error_429("[O-R-Imbalance Chart][Binance Historical-Data API]")
                if r.status == 418:self.close();return error_418("[O-R-Imbalance Chart][Binance Historical-Data API]")
                if r.status == 403:self.close();return error_403("[O-R-Imbalance Chart][Binance Historical-Data API]")
                if r.status != 200:
                    self.close()
                    unknown_error("[O-R-Imbalance Chart][Binance Historical-Data API]",f"Unexpected HTTP {r.status}")
                data = await r.json()
                result = ImbalanceChart.extract_buy_sell_volumes(data)
                df = pd.DataFrame(data=result)
                for i in ["total_volume","buy_volume","sell_volume"]:
                    df[i] = df[i].astype(float)
                self.asks_trades_v += df['sell_volume'].sum()
                self.bids_trades_v += df['buy_volume'].sum()
                logging.info("[O-R-Imbalance Chart][Binance Historical-Data API] Get Historical")
        except (aiohttp.ClientConnectionError,gaierror):
            self.close()
            return connection_error("[O-R-Imbalance Chart][Binance Historical-Data API]")
        except Exception as e:
            self.close()
            return unknown_error("[O-R-Imbalance Chart][Binance Historical-Data API]",f"Unexpected polling error: {e}")

    async def _from_server(self):
        """Receive and process real-time trade & depth data from Binance WebSocket"""
        url = f"wss://stream.binance.com:9443/stream?streams={self.SYMBOL.lower()}@trade/{self.SYMBOL.lower()}@depth@100ms"
        try:
            async with websockets.connect(url) as ws:
                time_start = self.time_n()
                time_start_2 = self.time_n()
                self.asks_trades_v, self.bids_trades_v = 0, 0
                asks_depth_v, bids_depth_v = 0, 0
                self.current_price = 0
                last = 0

                task1 = asyncio.create_task(self._update_depth_rest());task1
                self.async_tasks.append(task1)

                if self.VALUE_PAST > 0: 
                    task2 = asyncio.create_task(self._get_days_past());task2
                    self.async_tasks.append(task2)

                while True:
                    try:
                        resp = await ws.recv()
                        msg = json.loads(resp)
                        data = msg.get("data", {})
                    except websockets.exceptions.ConnectionClosedError:
                        self.close()
                        return connection_error("[O-R-Imbalance Chart][Binance WebSocket]")
                    except Exception as e:
                        self.close()
                        return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"WebSocket recv/parsing error: {e}")

                    # Binance sometimes sends status codes inside 'code'
                    if "code" in msg:
                        code = msg.get("code")
                        if code == 429: self.close();return error_429("[O-R-Imbalance Chart][Binance WebSocket]")
                        if code == 418: self.close();return error_418("[O-R-Imbalance Chart][Binance WebSocket]")
                        if code == 403: self.close();return error_403("[O-R-Imbalance Chart][Binance WebSocket]")

                    # === Trades stream ===
                    if msg.get("stream") == f"{self.SYMBOL.lower()}@trade":
                        try:
                            qty = float(data.get("q", 0))
                            pri = float(data.get("p", 0))
                            self.current_price = float(data.get("p", 0))
                            side = "Sell" if data.get("m", True) else "Buy"
                            if side == "Sell":
                                self.asks_trades_v += qty * self.current_price
                            else:
                                self.bids_trades_v += qty * self.current_price
                        except Exception as e:
                            self.close()
                            return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"Trades stream error: {e}")

                    # === Depth stream ===
                    if msg.get("stream") == f"{self.SYMBOL.lower()}@depth@100ms" and self.current_price != 0:
                        
                        try:
                            msg = data
                            lastUpdateId = msg.get("u")
                            firstUpdateId = msg.get("U")
                            if self.snapshot_update_status == 0: 
                                self.updates[lastUpdateId] = msg
                            elif self.snapshot_update_status == -1:
                                if not last+1 == firstUpdateId:
                                    t = asyncio.create_task(self._update_depth_rest());t
                                    self.async_tasks.append(t)
                                    continue
                                asks_ = msg.get("a")
                                bids_ = msg.get("b")
                                self._update_ob(asks_,bids_)
                                last = lastUpdateId
                            else:
                                last_updates_key = list(self.updates.keys())[-1] if len(list(self.updates.keys())) > 0 else lastUpdateId
                                self.snapshot_update_status = -1
                                if last_updates_key == self.snapshot_update:
                                    asks_ = msg.get("a")
                                    bids_ = msg.get("b")
                                    self._update_ob(asks_,bids_)
                                    last = lastUpdateId
                                else:
                                    udpdates_keys = list(self.updates.keys())
                                    if self.snapshot_update in udpdates_keys:
                                        idx = udpdates_keys.index(self.snapshot_update)
                                        vals = {k:self.updates[k] for k in udpdates_keys[idx+1:]}
                                        for l,value in vals.items():
                                            vals_asks = value.get("a")
                                            vals_bids = value.get("b")
                                            self._update_ob(vals_asks,vals_bids)
                                            self.updates.clear()
                                        asks_ = msg.get("a")
                                        bids_ = msg.get("b")
                                        self._update_ob(asks_,bids_)
                                        last = lastUpdateId
                                    else:
                                        t = asyncio.create_task(self._update_depth_rest());t
                                        self.async_tasks.append(t)
                                        continue

                            best_price = (self.bests_ob["min"]["asks"] + self.bests_ob["max"]["bids"]) / 2
                            max_ask = best_price + best_price*self.IMBALANCE_LEVEL/100
                            max_bid = best_price - best_price*self.IMBALANCE_LEVEL/100
                            

                            bids_depth_v = sum(q*p for p, q in self.global_bids.items() if p > max_bid)
                            asks_depth_v = sum(q*p for p, q in self.global_asks.items() if p < max_ask)
                        except Exception as e:
                            self.close()
                            return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"Depth stream error: {e}")

                    # === Frame update ===
                    if self.time_n() - time_start >= 1000:
                        try:
                            total_depth_vol = bids_depth_v + asks_depth_v
                            imbalance_depth = (bids_depth_v - asks_depth_v) / total_depth_vol if total_depth_vol > 0 else 0

                            total_trades_vol = self.bids_trades_v + self.asks_trades_v
                            imbalance_trades = (self.bids_trades_v - self.asks_trades_v) / total_trades_vol if total_trades_vol > 0 else 0

                            asyncio.create_task(self._update_trades(x=time_start, y=imbalance_trades))
                            asyncio.create_task(self._update_depth(x=time_start, y=imbalance_depth))
                        except Exception as e:
                            self.close()
                            return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"Frame update error: {e}")

                        # Reset for next frame
                        
                        time_start = self.time_n()

                    if self.time_n() - time_start_2 >= self.TIME_MS:
                        try:
                            self.asks_trades_v, self.bids_trades_v = 0, 0
                        except Exception as e:
                            self.close()
                            return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"Frame update error: {e}")

                        # Reset for next frame
                        
                        time_start_2 = self.time_n()

        except (OSError, websockets.exceptions.InvalidStatus, gaierror) as e:
            self.close()
            return connection_error("[O-R-Imbalance Chart][Binance WebSocket]")
        except Exception as e:
            self.close()
            return unknown_error("[O-R-Imbalance Chart][Binance WebSocket]",f"Critical WebSocket error: {e}")

    def _update_ob(self,asks_,bids_):
        for p,q in bids_:
            q = float(q)
            p = float(p)
            self.global_bids[p] = q
            if self.global_bids[p] == 0: 
                del self.global_bids[p]
        for p,q in asks_:
            q = float(q)
            p = float(p)
            self.global_asks[p] = q
            if self.global_asks[p] == 0: 
                del self.global_asks[p]

    @staticmethod
    def _kligns_reform(klines:list):
        """
        Extract Buy and Sell volumes from Binance Klines.

        :param klines: list of klines from Binance API
        :return: list of dicts with open_time, buy_volume, sell_volume, total_volume
        """
        results = []
        for k in klines:
            open_time = k[0]                            # Open timestamp in ms
            close_price = float(k[4])                   # Close price of eatch candal
            total_volume = float(k[5])*close_price      # Total base asset volume
            taker_buy_volume = float(k[9])*close_price  # Taker buy base asset volume
            taker_sell_volume = total_volume - taker_buy_volume  # Compute sell volume

            results.append({
                "open_time": open_time,
                "total_volume": total_volume,
                "buy_volume": taker_buy_volume,
                "sell_volume": taker_sell_volume
            })
        return results

    async def _update_trades(self, x, y):
        """Append and plot trades imbalance"""
        self.widgets["curves"]['trades']["X"].append(x)
        self.widgets["curves"]['trades']["Y"].append(y)
        self.widgets["curves"]['trades']["plot"].setData(
            self.widgets["curves"]['trades']["X"],
            self.widgets["curves"]['trades']["Y"]
        )
        self.scene().update()
        if self.LAST_CENTER: self.VB.setXRange(x - 100_000, x + 100_000)  # Keep window centered

    async def _update_depth(self, x, y):
        """Append and plot depth imbalance"""
        self.widgets["curves"]['depth']["X"].append(x)
        self.widgets["curves"]['depth']["Y"].append(y)
        self.widgets["curves"]['depth']["plot"].setData(
            self.widgets["curves"]['depth']["X"],
            self.widgets["curves"]['depth']["Y"]
        )
        self.scene().update()

    # ==============================================

    # On Close chart
    def closeEvent(self, event):
        """Cancel tasks and close aiohttp session cleanly"""
        asyncio.create_task(self._cleanup())
        for i in self.async_tasks:
            try:i.cancel()
            except:pass
        event.accept()
        logging.info(f"Close OBI-VOI Indecator for `{self.SYMBOL.upper()}`")

    async def _cleanup(self):
        if not self.rest_session.closed:
            await self.rest_session.close()

    # Start chart
    def run(self):
        """Run main tasks"""
        self.async_tasks.append(asyncio.create_task(self._from_server()))
        self.show()
