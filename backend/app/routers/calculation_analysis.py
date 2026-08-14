"""
计算链智能分析 API
==================
- POST /api/calculation-analysis/models/{model_id}/chain       构建影响链分析模型
- POST /api/calculation-analysis/models/{model_id}/scenarios   多设计方案全链计算
- POST /api/calculation-analysis/models/{model_id}/sensitivity 参数敏感性贡献分析
- POST /api/calculation-analysis/models/{model_id}/curve       单参数响应曲线
- POST /api/calculation-analysis/models/{model_id}/surface     双参数响应面
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.calculation_analysis import (
    AnalysisError,
    build_chain_analysis,
    compute_response_curve,
    compute_response_surface,
    compute_sensitivity,
    load_workbench_context,
    run_scenarios,
)

router = APIRouter(prefix="/calculation-analysis", tags=["calculation-analysis"])


def _handle(fn):
    try:
        return fn()
    except AnalysisError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/models/{model_id}/chain")
def analysis_chain(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_data, model_params = _handle(
        lambda: load_workbench_context(db, model_id, str(payload.get("module_code") or "") or None)
    )
    return _handle(
        lambda: build_chain_analysis(
            template_data,
            model_params,
            str(payload.get("target_node") or "").strip(),
            db=db,
        )
    )


@router.post("/models/{model_id}/scenarios")
def analysis_scenarios(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_data, model_params = _handle(
        lambda: load_workbench_context(db, model_id, str(payload.get("module_code") or "") or None)
    )
    target_node = str(payload.get("target_node") or "").strip()
    scenarios: List[Dict[str, Any]] = payload.get("scenarios") or []
    return _handle(lambda: run_scenarios(template_data, model_params, target_node, scenarios, db=db))


@router.post("/models/{model_id}/sensitivity")
def analysis_sensitivity(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_data, model_params = _handle(
        lambda: load_workbench_context(db, model_id, str(payload.get("module_code") or "") or None)
    )
    target_node = str(payload.get("target_node") or "").strip()
    inputs: List[Dict[str, Any]] = payload.get("inputs") or []
    return _handle(lambda: compute_sensitivity(template_data, model_params, target_node, inputs, db=db))


@router.post("/models/{model_id}/curve")
def analysis_curve(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_data, model_params = _handle(
        lambda: load_workbench_context(db, model_id, str(payload.get("module_code") or "") or None)
    )
    return _handle(
        lambda: compute_response_curve(
            template_data,
            model_params,
            str(payload.get("target_node") or "").strip(),
            str(payload.get("param") or "").strip(),
            payload.get("min"),
            payload.get("max"),
            steps=payload.get("steps", 21),
            track_intermediate=bool(payload.get("track_intermediate", True)),
            db=db,
        )
    )


@router.post("/models/{model_id}/surface")
def analysis_surface(model_id: int, payload: Dict[str, Any], db: Session = Depends(get_db)):
    template_data, model_params = _handle(
        lambda: load_workbench_context(db, model_id, str(payload.get("module_code") or "") or None)
    )
    return _handle(
        lambda: compute_response_surface(
            template_data,
            model_params,
            str(payload.get("target_node") or "").strip(),
            str(payload.get("param1") or "").strip(),
            str(payload.get("param2") or "").strip(),
            payload.get("range1") or {},
            payload.get("range2") or {},
            grid=payload.get("grid", 15),
        )
    )
