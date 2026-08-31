"""Typed domain contracts for FEAT-045."""
from __future__ import annotations
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class Status(StrEnum):
    LOCAL_ONLY = "LOCAL_ONLY"
    QUEUED = "QUEUED"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    CONFLICT = "CONFLICT"
    SYNCED = "SYNCED"
    FAILED = "FAILED"
    DISCARDED = "DISCARDED"

class CreateRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    expected_revision:int=Field(default=0,ge=0)
    client_reference:str=Field(min_length=1,max_length=128)
    payload:dict[str,Any]=Field(default_factory=dict)

class CommandRequest(BaseModel):
    model_config=ConfigDict(extra="forbid")
    expected_revision:int=Field(ge=0)
    action:str=Field(min_length=1,max_length=64)
    reason:str|None=Field(default=None,max_length=1000)
    payload:dict[str,Any]=Field(default_factory=dict)

class OfflineReceiptDraft(BaseModel):
    id:str
    tenant_id:str
    status:Status
    revision:int=Field(ge=0)
    client_reference:str
    data:dict[str,Any]=Field(default_factory=dict)
    evidence:dict[str,Any]=Field(default_factory=dict)
    created_at:datetime=Field(default_factory=lambda:datetime.now(UTC))
    updated_at:datetime=Field(default_factory=lambda:datetime.now(UTC))

class ApiProblem(BaseModel):
    code:str; message:str; field:str|None=None; retryable:bool=False; correlation_id:str

class DomainError(Exception):
    def __init__(self,code:str,message:str,status_code:int=409):
        super().__init__(message); self.code=code; self.message=message; self.status_code=status_code
class NotFoundError(DomainError):
    def __init__(self): super().__init__("NOT_FOUND","Resource not found",404)
class StaleRevisionError(DomainError):
    def __init__(self): super().__init__("STALE_REVISION","Expected revision is stale",409)
class IdempotencyConflictError(DomainError):
    def __init__(self): super().__init__("IDEMPOTENCY_CONFLICT","Key was used with another payload",409)
