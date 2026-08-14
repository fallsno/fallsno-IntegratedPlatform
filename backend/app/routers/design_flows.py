from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import PartDesignFlow, FlowStep, StepParameter, FormulaLibrary
from app.schemas import (
    DesignFlowCreate, DesignFlowOut, 
    FlowStepBase, FlowStepCreate, FlowStepOut,
    StepParameterBase, StepParameterCreate, StepParameterOut
)

router = APIRouter(prefix="/design-flows", tags=["design-flows"])

# ---------- 设计流程 API ----------

@router.get("/part/{part_id}", response_model=List[DesignFlowOut])
def get_flows_by_part(part_id: int, db: Session = Depends(get_db)):
    return db.query(PartDesignFlow).filter(PartDesignFlow.part_id == part_id).all()

@router.post("/", response_model=DesignFlowOut)
def create_flow(data: DesignFlowCreate, db: Session = Depends(get_db)):
    flow = PartDesignFlow(**data.dict())
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return flow

@router.delete("/{flow_id}")
def delete_flow(flow_id: int, db: Session = Depends(get_db)):
    flow = db.query(PartDesignFlow).filter(PartDesignFlow.id == flow_id).first()
    if flow:
        db.delete(flow)
        db.commit()
    return {"ok": True}

# ---------- 步骤 API ----------

@router.get("/{flow_id}/steps", response_model=List[FlowStepOut])
def get_steps(flow_id: int, db: Session = Depends(get_db)):
    return db.query(FlowStep).filter(FlowStep.flow_id == flow_id).order_by(FlowStep.step_order).all()

@router.post("/{flow_id}/steps", response_model=FlowStepOut)
def create_step(flow_id: int, data: FlowStepCreate, db: Session = Depends(get_db)):
    # 步骤创建时包含参数
    step_dict = data.dict(exclude={"parameters"})
    if 'flow_id' in step_dict:
        del step_dict['flow_id']
    db_step = FlowStep(flow_id=flow_id, **step_dict)
    db.add(db_step)
    db.flush() # 获取 id
    
    if data.parameters:
        for p in data.parameters:
            db_param = StepParameter(step_id=db_step.id, **p.dict(exclude={'step_id'}))
            db.add(db_param)
            
    db.commit()
    db.refresh(db_step)
    return db_step

@router.put("/steps/{step_id}", response_model=FlowStepOut)
def update_step(step_id: int, data: FlowStepBase, db: Session = Depends(get_db)):
    db_step = db.query(FlowStep).filter(FlowStep.id == step_id).first()
    if not db_step:
        raise HTTPException(404, "Step not found")
    
    # 更新基本字段
    step_dict = data.dict(exclude={"parameters"})
    for k, v in step_dict.items():
        setattr(db_step, k, v)
    
    # 更新参数 (先删后加)
    db.query(StepParameter).filter(StepParameter.step_id == step_id).delete()
    if data.parameters:
        for p in data.parameters:
            db_param = StepParameter(step_id=step_id, **p.dict())
            db.add(db_param)
            
    db.commit()
    db.refresh(db_step)
    return db_step

@router.delete("/steps/{step_id}")
def delete_step(step_id: int, db: Session = Depends(get_db)):
    step = db.query(FlowStep).filter(FlowStep.id == step_id).first()
    if step:
        db.delete(step)
        db.commit()
    return {"ok": True}

# ---------- 图表 API ----------

@router.get("/{flow_id}/graph")
def get_flow_graph(flow_id: int, db: Session = Depends(get_db)):
    steps = db.query(FlowStep).filter(FlowStep.flow_id == flow_id).all()
    nodes = []
    edges = []
    for s in steps:
        nodes.append({"id": str(s.id), "label": f"{s.step_order} {s.design_point}"})
        # 简单逻辑：根据 step_order 建立连线 (1 -> 1.1, 1 -> 2 等)
        # 实际可能需要根据 source_step_id
        for p in s.parameters:
            if p.source_step_id:
                edges.append({
                    "source": str(p.source_step_id), 
                    "target": str(s.id), 
                    "label": p.param_name
                })
    return {"nodes": nodes, "edges": edges}

# ---------- 核心计算逻辑：对比功能专用 ----------

@router.get("/compare/{design_point}")
def compare_design_points(design_point: str, db: Session = Depends(get_db)):
    # 查找所有具有相同设计点的步骤
    steps = db.query(FlowStep).filter(FlowStep.design_point == design_point).all()
    results = []
    for s in steps:
        results.append({
            "part_id": s.flow.part_id,
            "part_name": s.flow.part.part_name,
            "version_code": s.flow.part.version.version_code,
            "family_code": s.flow.part.version.family.family_code,
            "result_value": s.result_value,
            "note": s.note
        })
    return results
