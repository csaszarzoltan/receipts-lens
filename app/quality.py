"""Deterministic OCR benchmark, confidence calibration and review contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True)
class BenchmarkCase:
    case_id:str; truth:dict[str,Any]; prediction:dict[str,Any]; confidence:dict[str,float]
@dataclass(frozen=True)
class BenchmarkReport:
    corpus_version:str; exact_match:dict[str,float]; precision:float; recall:float; f1:float; calibration_ece:float
@dataclass(frozen=True)
class Correction:
    case_id:str; original_prediction:dict[str,Any]; corrected:dict[str,Any]; actor:str; created_at:str

class BenchmarkRunner:
    def _field_scores(self, cases: list[BenchmarkCase]) -> dict[str, float]:
        fields = sorted({k for c in cases for k in c.truth})
        return {f: sum(c.prediction.get(f) == c.truth.get(f) for c in cases) / len(cases)
                for f in fields}

    def _aggregate_metrics(self, cases: list[BenchmarkCase], fields: list[str]) -> tuple[float, float, float]:
        tp = sum(c.prediction.get(f) == c.truth.get(f) and c.truth.get(f) is not None
                 for c in cases for f in fields)
        predicted = sum(c.prediction.get(f) is not None for c in cases for f in fields)
        actual = sum(c.truth.get(f) is not None for c in cases for f in fields)
        precision = tp / predicted if predicted else 0.0
        recall = tp / actual if actual else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        return precision, recall, f1

    def _calibration_ece(self, cases: list[BenchmarkCase], fields: list[str]) -> float:
        pairs = [(c.confidence.get(f, 0.0), 1.0 if c.prediction.get(f) == c.truth.get(f) else 0.0)
                 for c in cases for f in fields]
        return sum(abs(conf - ok) for conf, ok in pairs) / len(pairs) if pairs else 0.0

    def run(self, version: str, cases: list[BenchmarkCase]) -> BenchmarkReport:
        if not version or not cases:
            raise ValueError("version and cases required")
        fields = sorted({k for c in cases for k in c.truth})
        exact = self._field_scores(cases)
        precision, recall, f1 = self._aggregate_metrics(cases, fields)
        ece = self._calibration_ece(cases, fields)
        return BenchmarkReport(version, exact, precision, recall, f1, ece)

class ReviewPolicy:
    def __init__(self,thresholds:dict[str,float],default:float=0.7)->None:
        self.thresholds=dict(thresholds); self.default=default
    def requires_review(self,prediction:dict[str,Any],confidence:dict[str,float])->bool:
        return any(prediction.get(f) is None or confidence.get(f,0)<self.thresholds.get(f,self.default) for f in set(prediction)|set(self.thresholds))
    def correct(self,case:BenchmarkCase,changes:dict[str,Any],actor:str)->Correction:
        if not actor or not changes: raise ValueError("actor and changes required")
        corrected={**case.prediction,**changes}
        return Correction(case.case_id,dict(case.prediction),corrected,actor,datetime.now(timezone.utc).isoformat())
