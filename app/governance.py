"""Authentication, quota, webhook integrity and tamper-evident audit primitives."""
from __future__ import annotations
import hashlib, hmac, json, threading, time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

@dataclass(frozen=True)
class AuthContext:
    tenant_id: str
    role: str
    @classmethod
    def from_api_key(cls, key: str, keys: Mapping[str, tuple[str, str]]) -> "AuthContext":
        for candidate, context in keys.items():
            if hmac.compare_digest(candidate, key): return cls(*context)
        raise PermissionError("invalid API key")
    def require(self, *roles: str) -> None:
        if self.role not in roles: raise PermissionError("insufficient role")

class RateLimiter:
    def __init__(self, limit: int, window_seconds: float) -> None:
        if limit < 1 or window_seconds <= 0: raise ValueError("positive limits required")
        self.limit, self.window = limit, window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque); self._lock=threading.Lock()
    def allow(self, tenant_id: str, now: float | None=None) -> bool:
        now=time.monotonic() if now is None else now
        with self._lock:
            q=self._hits[tenant_id]
            while q and q[0] <= now-self.window: q.popleft()
            if len(q)>=self.limit: return False
            q.append(now); return True

class WebhookSigner:
    def __init__(self, secret: bytes, tolerance_seconds: int=300) -> None:
        if not secret: raise ValueError("webhook secret required")
        self.secret,self.tolerance=secret,tolerance_seconds
    def sign(self, payload: bytes, timestamp: int|None=None) -> str:
        timestamp=int(time.time()) if timestamp is None else timestamp
        digest=hmac.new(self.secret, f"{timestamp}.".encode()+payload, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={digest}"
    def verify(self, payload: bytes, signature: str, now: int|None=None) -> bool:
        try:
            parts=dict(p.split("=",1) for p in signature.split(",")); ts=int(parts["t"])
        except (ValueError,KeyError): return False
        now=int(time.time()) if now is None else now
        if abs(now-ts)>self.tolerance: return False
        return hmac.compare_digest(self.sign(payload,ts),signature)

@dataclass(frozen=True)
class AuditEvent:
    tenant_id:str; action:str; data:dict[str,Any]; previous_hash:str; hash:str

class AuditChain:
    def __init__(self,path:str|Path)->None:
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.Lock()
    def _events(self)->list[dict[str,Any]]:
        if not self.path.exists(): return []
        return [json.loads(x) for x in self.path.read_text(encoding="utf-8").splitlines() if x]
    def append(self,tenant_id:str,action:str,data:dict[str,Any])->AuditEvent:
        forbidden={"raw_text","image_bytes","secret","token"}
        clean={k:v for k,v in data.items() if k not in forbidden}
        with self._lock:
            events=self._events(); prev=events[-1]["hash"] if events else "0"*64
            base={"tenant_id":tenant_id,"action":action,"data":clean,"previous_hash":prev}
            digest=hashlib.sha256(json.dumps(base,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            record={**base,"hash":digest}
            with self.path.open("a",encoding="utf-8") as fh: fh.write(json.dumps(record,sort_keys=True)+"\n")
            return AuditEvent(**record)
    def verify(self)->bool:
        prev="0"*64
        for record in self._events():
            digest=record.pop("hash"); record["previous_hash"]=prev
            actual=hashlib.sha256(json.dumps(record,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            if not hmac.compare_digest(digest,actual): return False
            prev=digest
        return True
