"""Accounting connector port, CSV adapter and auditable usage metering."""
from __future__ import annotations

import csv
import io
import json
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class AccountingProfile:
    required_fields:tuple[str,...]; delimiter:str=","; field_mapping:dict[str,str]|None=None
class AccountingConnector(Protocol):
    def export(self,receipts:list[dict[str,Any]])->str: ...
class CsvAccountingConnector:
    def __init__(self,profile:AccountingProfile)->None:self.profile=profile
    def export(self,receipts:list[dict[str,Any]])->str:
        fields=list(self.profile.required_fields); output=io.StringIO(newline="")
        writer=csv.DictWriter(output,fieldnames=fields,delimiter=self.profile.delimiter,extrasaction="ignore"); writer.writeheader()
        for receipt in receipts:
            missing=[f for f in fields if receipt.get(f) is None]
            if missing: raise ValueError("missing accounting fields: "+", ".join(missing))
            writer.writerow({f:self._safe(receipt[f]) for f in fields})
        return output.getvalue()
    @staticmethod
    def _safe(value:Any)->Any:
        if isinstance(value,str) and value.startswith(("=","+","-","@")): return "'"+value
        return value
class UsageMeter:
    def __init__(self,path:str|Path)->None:self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self._lock=threading.Lock()
    def record(self,tenant_id:str,event:str,quantity:int=1)->None:
        if not tenant_id or not event or quantity<1: raise ValueError("valid usage event required")
        row={"tenant_id":tenant_id,"event":event,"quantity":quantity,"created_at":datetime.now(UTC).isoformat()}
        with self._lock,self.path.open("a",encoding="utf-8") as fh:fh.write(json.dumps(row,sort_keys=True)+"\n")
    def report(self,tenant_id:str)->dict[str,int]:
        totals:dict[str,int]={}
        if not self.path.exists(): return totals
        for line in self.path.read_text(encoding="utf-8").splitlines():
            row=json.loads(line)
            if row["tenant_id"]==tenant_id: totals[row["event"]]=totals.get(row["event"],0)+row["quantity"]
        return totals
