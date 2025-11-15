# ---------------------------------------------------------------
# Import libs and modules 
# ---------------------------------------------------------------
import os
import sys
from pathlib import Path

import asyncio
import aiohttp

# ---------------------------------------------------------------
#  Main Class
# ---------------------------------------------------------------
class CoreIndex:
    def _init__(self,symbol:str,*args, **kwargs):
        # Base attributes
        self.SYMBOL = symbol
        self.async_tasks = []
        self.rest_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(20))

        # Order-book attributes
        self.snapshot_update_status = 0
        self.snapshot_update = None
        self.updates = {}
        self.bests_ob = {}
        self.global_bids = {}
        self.global_asks = {}
        self.lastUpdateInOB = 0

    # Order-book methods ===============================================

    # Set order-book updates
    async def process_ob_message(self,msg:dict):
        """Set order-book upates"""
        try:
            lastUpdateId = msg.get("lastUpdateId")
            firstUpdateId = msg.get("firstUpdateId")
            if self.snapshot_update_status == 0: 
                self.updates[lastUpdateId] = msg
            elif self.snapshot_update_status == -1:
                if not self.lastUpdateInOB+1 == firstUpdateId:
                    t = asyncio.create_task(self.update_ob_snapshot());t
                    self.async_tasks.append(t)
                    return
                asks_ = msg.get("asks")
                bids_ = msg.get("bids")
                self._update_ob(asks_,bids_)
                self.lastUpdateInOB = lastUpdateId
            else:
                last_updates_key = list(self.updates.keys())[-1] if len(list(self.updates.keys())) > 0 else lastUpdateId
                self.snapshot_update_status = -1
                if last_updates_key == self.snapshot_update:
                    asks_ = msg.get("asks")
                    bids_ = msg.get("bids")
                    self._update_ob(asks_,bids_)
                    self.lastUpdateInOB = lastUpdateId
                else:
                    udpdates_keys = list(self.updates.keys())
                    if self.snapshot_update in udpdates_keys:
                        idx = udpdates_keys.index(self.snapshot_update)
                        vals = {k:self.updates[k] for k in udpdates_keys[idx+1:]}
                        for l,value in vals.items():
                            vals_asks = value.get("asks")
                            vals_bids = value.get("bids")
                            self._update_ob(vals_asks,vals_bids)
                            self.updates.clear()
                        asks_ = msg.get("asks")
                        bids_ = msg.get("bids")
                        self._update_ob(asks_,bids_)
                        self.lastUpdateInOB = lastUpdateId
                    else:
                        t = asyncio.create_task(self.update_ob_snapshot());t
                        self.async_tasks.append(t)
                        return
            if len(self.global_asks) > 0 and len(self.global_bids) > 0:
                self.bests_ob = {
                    "min":{
                        "asks":min(self.global_asks.keys()),
                        "bids":min(self.global_bids.keys())
                    },
                    "max":{
                        "asks":max(self.global_asks.keys()),
                        "bids":max(self.global_bids.keys())
                }}
        except Exception as e:
            raise e
        
    # Update order-book levels
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

    # upate order-book snapshot start operation
    async def _update_ob_snapshot_start(self):
        self.snapshot_update_status = 0

    # update order-book snapshot end operation
    async def _update_ob_snapshot_end(self,data:dict):
        self.snapshot_update = data.get("lastUpdateId")
        self.snapshot_update_status = 10
        self.global_asks = {float(p):float(q) for p,q in data.get("asks")}
        self.global_bids = {float(p):float(q) for p,q in data.get("bids")}
        self.bests_ob = {
            "min":{
                "asks":min(self.global_asks.keys()),
                "bids":min(self.global_bids.keys())
            },
            "max":{
                "asks":max(self.global_asks.keys()),
                "bids":max(self.global_bids.keys())
            }}

    # Update order-book snapshot
    async def update_ob_snapshot(self):
        raise NotImplementedError("The method `update_ob_snapshot` should be implemented in the subclass.")
    

    # Main methods ==================================================

    # Close async sessions and tasks
    async def close(self):
        """Close all async sessions and tasks"""
        for task in self.async_tasks:
            task.cancel()
        await self.rest_session.close()

