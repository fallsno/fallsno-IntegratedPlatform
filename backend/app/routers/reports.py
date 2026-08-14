from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Optional
import asyncio
from pathlib import Path
import tempfile
import os
from datetime import datetime
from app.database import SessionLocal
from app.models import WorkbenchParameterSnapshot, ParameterDefinition, ModelVersion
from sqlalchemy import select
import json

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/generate")
async def generate_report(
    run_key: str,
    format: str = "pdf"
):
    """
    根据 run_key 生成报告
    - run_key: 工作台运行快照的唯一标识
    - format: 输出格式 (pdf/html)
    """
    db = SessionLocal()
    try:
        # 1. 查询快照数据
        stmt = select(WorkbenchParameterSnapshot).where(
            WorkbenchParameterSnapshot.run_key == run_key
        ).order_by(WorkbenchParameterSnapshot.created_at)
        snapshots = db.execute(stmt).scalars().all()
        
        if not snapshots:
            raise HTTPException(status_code=404, detail="未找到对应的运行快照")
        
        # 2. 查询参数定义
        param_ids = [s.parameter_id for s in snapshots]
        param_stmt = select(ParameterDefinition).where(
            ParameterDefinition.id.in_(param_ids)
        )
        params = db.execute(param_stmt).scalars().all()
        param_map = {p.id: p for p in params}
        
        # 3. 查询版本信息
        version_ids = [s.version_id for s in snapshots if s.version_id]
        if version_ids:
            version_stmt = select(ModelVersion).where(
                ModelVersion.id.in_(version_ids)
            )
            versions = db.execute(version_stmt).scalars().all()
            version_map = {v.id: v for v in versions}
        else:
            version_map = {}
        
        # 4. 构建报告数据
        report_data = {
            "title": f"工程设计计算书 - {run_key}",
            "project_code": snapshots[0].source_version or "N/A",
            "generated_at": datetime.now().isoformat(),
            "parameters": [],
            "equipments": []
        }
        
        # 5. 处理参数数据
        for snapshot in snapshots:
            param = param_map.get(snapshot.parameter_id)
            if param:
                report_data["parameters"].append({
                    "name": param.name,
                    "value": snapshot.snapshot_value,
                    "unit": param.unit or "",
                    "formula": param.formula or "手动输入"
                })
        
        # 6. 处理设备选型数据 (从快照中提取 SELECT_EQUIP 相关数据)
        # 这里需要根据实际情况解析快照中的设备选型信息
        # 暂时使用模拟数据
        report_data["equipments"] = [
            {"category": "电机", "model": "Y2-160L-4", "brand": "西门子", "specs": "功率: 18.5kW, 转速: 1460rpm"},
            {"category": "减速机", "model": "ZLYJ225", "brand": "国茂", "specs": "速比: 31.5, 扭矩: 2500N.m"}
        ]
        
        # 7. 生成报告文件
        if format == "pdf":
            # 使用无头浏览器生成 PDF
            return await generate_pdf_report(report_data)
        else:
            # 返回 HTML 格式的报告数据
            return report_data
            
    finally:
        db.close()

async def generate_pdf_report(report_data: dict):
    """使用无头浏览器生成 PDF 报告"""
    try:
        # 这里应该集成无头浏览器 (如 Playwright 或 Puppeteer)
        # 暂时返回模拟的 PDF 文件路径
        
        # 创建临时 PDF 文件
        temp_dir = tempfile.mkdtemp()
        pdf_path = Path(temp_dir) / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 这里应该调用无头浏览器生成 PDF
        # 暂时创建一个空文件作为占位符
        pdf_path.touch()
        
        return FileResponse(
            path=str(pdf_path),
            filename=f"工程设计计算书_{report_data['project_code']}.pdf",
            media_type="application/pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {str(e)}")

@router.get("/snapshots/{run_key}")
async def get_report_snapshots(run_key: str):
    """获取报告快照数据"""
    db = SessionLocal()
    try:
        stmt = select(WorkbenchParameterSnapshot).where(
            WorkbenchParameterSnapshot.run_key == run_key
        ).order_by(WorkbenchParameterSnapshot.created_at)
        snapshots = db.execute(stmt).scalars().all()
        
        if not snapshots:
            raise HTTPException(status_code=404, detail="未找到对应的运行快照")
        
        # 构建响应数据
        result = {
            "run_key": run_key,
            "snapshots": [],
            "generated_at": datetime.now().isoformat()
        }
        
        for snapshot in snapshots:
            result["snapshots"].append({
                "parameter_id": snapshot.parameter_id,
                "snapshot_value": snapshot.snapshot_value,
                "source_version": snapshot.source_version,
                "source_type": snapshot.source_type,
                "created_at": snapshot.created_at.isoformat()
            })
        
        return result
        
    finally:
        db.close()