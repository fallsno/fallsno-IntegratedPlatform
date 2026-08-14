from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GuidanceAction, RuleHitRecord
from app.schemas import (
    GuidanceActionOut,
    GuidanceActionUpdate,
    RuleHitRecordCreate,
    RuleHitRecordOut,
)
from app.services.design_guidance import (
    DesignGuidanceValidationError,
    build_guidance_actions,
    build_guidance_summary,
    derive_rule_hit_status,
    normalize_guidance_action_update,
    normalize_rule_hit_payload,
)

router = APIRouter(prefix="/guidance", tags=["guidance"])


def serialize_action(row: GuidanceAction):
    return {
        "id": row.id,
        "rule_hit_id": row.rule_hit_id,
        "action_code": row.action_code,
        "action_label": row.action_label,
        "action_type": row.action_type,
        "priority": row.priority,
        "status": row.status,
        "result_note": row.result_note,
        "result_snapshot": row.result_snapshot,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


@router.get("/summary")
def get_guidance_summary(db: Session = Depends(get_db)):
    rows = db.query(RuleHitRecord).order_by(RuleHitRecord.created_at.desc()).all()
    actions = db.query(GuidanceAction).order_by(GuidanceAction.created_at.desc()).all()
    actions_by_hit = {}
    for action in actions:
        actions_by_hit.setdefault(action.rule_hit_id, []).append(serialize_action(action))
    return {
        "summary": build_guidance_summary(
            [
                {
                    "severity": row.severity,
                    "status": row.status,
                    "source_type": row.source_type,
                }
                for row in rows
            ],
            [{"status": row.status} for row in actions],
        ),
        "hits": [
            {
                "id": row.id,
                "source_type": row.source_type,
                "target_type": row.target_type,
                "target_id": row.target_id,
                "severity": row.severity,
                "message": row.message,
                "suggestion": row.suggestion,
                "status": row.status,
                "hit_snapshot": row.hit_snapshot,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "actions": actions_by_hit.get(row.id, []),
            }
            for row in rows[:20]
        ],
    }


@router.post("/hits", response_model=RuleHitRecordOut)
def create_rule_hit(data: RuleHitRecordCreate, db: Session = Depends(get_db)):
    try:
        payload = normalize_rule_hit_payload(data.model_dump())
    except DesignGuidanceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    row = RuleHitRecord(**payload)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/hits/{hit_id}/actions/generate", response_model=list[GuidanceActionOut])
def generate_guidance_actions(hit_id: int, db: Session = Depends(get_db)):
    hit = db.query(RuleHitRecord).filter(RuleHitRecord.id == hit_id).first()
    if not hit:
        raise HTTPException(status_code=404, detail="rule hit not found")

    existing_rows = (
        db.query(GuidanceAction).filter(GuidanceAction.rule_hit_id == hit_id).all()
    )
    existing_codes = {
        row.action_code
        for row in existing_rows
        if str(row.status or "open").strip() in {"open", "in_progress"}
    }
    for item in build_guidance_actions(
        {
            "source_type": hit.source_type,
            "target_type": hit.target_type,
            "target_id": hit.target_id,
            "severity": hit.severity,
            "message": hit.message,
        }
    ):
        if item["action_code"] in existing_codes:
            continue
        db.add(GuidanceAction(rule_hit_id=hit_id, **item))
    db.commit()
    return (
        db.query(GuidanceAction)
        .filter(GuidanceAction.rule_hit_id == hit_id)
        .order_by(GuidanceAction.id.asc())
        .all()
    )


@router.patch("/actions/{action_id}", response_model=GuidanceActionOut)
def update_guidance_action(
    action_id: int, data: GuidanceActionUpdate, db: Session = Depends(get_db)
):
    action = db.query(GuidanceAction).filter(GuidanceAction.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="guidance action not found")
    try:
        payload = normalize_guidance_action_update(data.model_dump())
    except DesignGuidanceValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    action.status = payload["status"]
    action.result_note = payload["result_note"]
    action.result_snapshot = payload["result_snapshot"]

    sibling_actions = (
        db.query(GuidanceAction).filter(GuidanceAction.rule_hit_id == action.rule_hit_id).all()
    )
    hit = db.query(RuleHitRecord).filter(RuleHitRecord.id == action.rule_hit_id).first()
    if hit:
        hit.status = derive_rule_hit_status(
            [
                {"status": payload["status"] if row.id == action.id else row.status}
                for row in sibling_actions
            ]
        )
    db.commit()
    db.refresh(action)
    return action
