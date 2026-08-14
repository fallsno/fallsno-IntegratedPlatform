from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import traceback
from pathlib import Path
import os
import importlib
import pkgutil
import app.routers as routers_pkg
from app.routers import product_types, families, product_components, design_flows, formulas, versions, compare, search, history, knowledge, reports, ai
from app.database import engine, Base
from sqlalchemy import text, inspect
from app.models import *

# 自动检查并修复数据库字段
def patch_database():
    try:
        inspector = inspect(engine)
        
        # 修复 model_families
        columns_families = [c['name'] for c in inspector.get_columns('model_families')]
        if 'product_type_id' not in columns_families:
            print("修复数据库: 为 model_families 添加 product_type_id 字段...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE model_families ADD COLUMN product_type_id INTEGER REFERENCES product_types(id) ON DELETE SET NULL;"))
                conn.commit()
                print("model_families 修复完成")
        family_new_cols = {
            'capacity_options': 'VARCHAR(100)',
            'default_template_code': 'VARCHAR(100)',
            'sort_order': 'INTEGER DEFAULT 0',
        }
        for col, type_ in family_new_cols.items():
            if col not in columns_families:
                print(f"修复数据库: 为 model_families 添加 {col} 字段...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE model_families ADD COLUMN {col} {type_};"))
                    conn.commit()
                    print(f"{col} 字段添加成功")

        columns_versions = [c['name'] for c in inspector.get_columns('model_versions')]
        version_new_cols = {
            'capacity_value': 'INTEGER',
            'display_name': 'VARCHAR(100)',
        }
        for col, type_ in version_new_cols.items():
            if col not in columns_versions:
                print(f"修复数据库: 为 model_versions 添加 {col} 字段...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE model_versions ADD COLUMN {col} {type_};"))
                    conn.commit()
                    print(f"{col} 字段添加成功")

        # 修复 product_types
        columns_types = [c['name'] for c in inspector.get_columns('product_types')]
        new_cols = {
            'model_code': 'VARCHAR(100)',
            'alias_keywords': 'VARCHAR(200)',
            'english_name': 'VARCHAR(100)',
            'category': 'VARCHAR(100)',
            'sort_order': 'INTEGER DEFAULT 0',
            'status': "VARCHAR(20) DEFAULT 'active'",
            'version': 'VARCHAR(50)',
            'publisher': 'VARCHAR(100)',
            'machine_model': 'VARCHAR(50)'
        }
        for col, type_ in new_cols.items():
            if col not in columns_types:
                print(f"修复数据库: 为 product_types 添加 {col} 字段...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE product_types ADD COLUMN {col} {type_};"))
                    conn.commit()
                    print(f"{col} 字段添加成功")

        # 修复 formula_library
        columns_formulas = [c['name'] for c in inspector.get_columns('formula_library')]
        formula_new_cols = {
            'canonical_expression': 'TEXT',
            'solve_targets': 'JSON',
        }
        for col, type_ in formula_new_cols.items():
            if col not in columns_formulas:
                print(f"修复数据库: 为 formula_library 添加 {col} 字段...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE formula_library ADD COLUMN {col} {type_};"))
                    conn.commit()
                    print(f"{col} 字段添加成功")

        columns_workbench_formulas = [c['name'] for c in inspector.get_columns('workbench_formulas')]
        workbench_formula_new_cols = {
            'module_code': "VARCHAR(50) DEFAULT 'power_calc'",
            'module_name': "VARCHAR(100) DEFAULT '功率计算'",
            'sort_order': 'INTEGER DEFAULT 0',
        }
        for col, type_ in workbench_formula_new_cols.items():
            if col not in columns_workbench_formulas:
                print(f"修复数据库: 为 workbench_formulas 添加 {col} 字段...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE workbench_formulas ADD COLUMN {col} {type_};"))
                    conn.commit()
                    print(f"{col} 字段添加成功")

        table_names = inspector.get_table_names()
        if "model_parameter_values" not in table_names:
            print("修复数据库: 创建 model_parameter_values 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS model_parameter_values (
                            id SERIAL PRIMARY KEY,
                            version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
                            parameter_id INTEGER NOT NULL REFERENCES parameter_definitions(id) ON DELETE CASCADE,
                            param_value VARCHAR(200) NOT NULL,
                            value_source VARCHAR(50) DEFAULT 'manual',
                            version_no VARCHAR(50) DEFAULT 'draft',
                            sort_order INTEGER DEFAULT 0,
                            remark TEXT,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ
                        )
                        """
                    )
                )
                conn.commit()
                print("model_parameter_values 创建完成")

        if "workbench_parameter_snapshots" not in table_names:
            print("修复数据库: 创建 workbench_parameter_snapshots 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS workbench_parameter_snapshots (
                            id SERIAL PRIMARY KEY,
                            run_key VARCHAR(100) NOT NULL,
                            version_id INTEGER REFERENCES model_versions(id) ON DELETE SET NULL,
                            parameter_id INTEGER NOT NULL REFERENCES parameter_definitions(id) ON DELETE CASCADE,
                            snapshot_value VARCHAR(200) NOT NULL,
                            source_version VARCHAR(50),
                            source_type VARCHAR(50) DEFAULT 'matrix',
                            created_at TIMESTAMPTZ DEFAULT NOW()
                        )
                        """
                    )
                )
                conn.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS ix_workbench_parameter_snapshots_run_key
                        ON workbench_parameter_snapshots (run_key)
                        """
                    )
                )
                conn.commit()
                print("workbench_parameter_snapshots 创建完成")

        if "parameter_lookup_definitions" not in table_names:
            print("修复数据库: 创建 parameter_lookup_definitions 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS parameter_lookup_definitions (
                            id SERIAL PRIMARY KEY,
                            lookup_code VARCHAR(100) NOT NULL UNIQUE,
                            lookup_name VARCHAR(100) NOT NULL,
                            description TEXT,
                            status VARCHAR(20) DEFAULT 'active',
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ
                        )
                        """
                    )
                )
                conn.commit()
                print("parameter_lookup_definitions 创建完成")
        else:
            lookup_definition_columns = [c['name'] for c in inspector.get_columns('parameter_lookup_definitions')]
            if 'curve_profile' not in lookup_definition_columns:
                print("修复数据库: 为 parameter_lookup_definitions 添加 curve_profile 字段...")
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE parameter_lookup_definitions ADD COLUMN curve_profile JSON;"))
                    conn.commit()
                    print("curve_profile 字段添加成功")

        if "parameter_lookup_rows" not in table_names:
            print("修复数据库: 创建 parameter_lookup_rows 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS parameter_lookup_rows (
                            id SERIAL PRIMARY KEY,
                            lookup_id INTEGER NOT NULL REFERENCES parameter_lookup_definitions(id) ON DELETE CASCADE,
                            lookup_key VARCHAR(100) NOT NULL,
                            result_value VARCHAR(200) NOT NULL,
                            sort_order INTEGER DEFAULT 0,
                            remark TEXT,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ,
                            CONSTRAINT uq_parameter_lookup_rows_lookup_key UNIQUE (lookup_id, lookup_key)
                        )
                        """
                    )
                )
                conn.commit()
                print("parameter_lookup_rows 创建完成")

        if "parameter_lookup_configs" not in table_names:
            print("修复数据库: 创建 parameter_lookup_configs 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS parameter_lookup_configs (
                            id SERIAL PRIMARY KEY,
                            parameter_id INTEGER NOT NULL REFERENCES parameter_definitions(id) ON DELETE CASCADE,
                            lookup_id INTEGER NOT NULL REFERENCES parameter_lookup_definitions(id) ON DELETE CASCADE,
                            input_parameter_id INTEGER NOT NULL REFERENCES parameter_definitions(id) ON DELETE CASCADE,
                            base_factor VARCHAR(100) DEFAULT '1',
                            final_expression VARCHAR(200) DEFAULT 'base_factor*lookup_result',
                            status VARCHAR(20) DEFAULT 'active',
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ,
                            CONSTRAINT uq_parameter_lookup_configs_parameter UNIQUE (parameter_id)
                        )
                        """
                    )
                )
                conn.commit()
                print("parameter_lookup_configs 创建完成")

        if "model_focus_metric_configs" not in table_names:
            print("修复数据库: 创建 model_focus_metric_configs 表...")
            with engine.connect() as conn:
                conn.execute(
                    text(
                        """
                        CREATE TABLE IF NOT EXISTS model_focus_metric_configs (
                            id SERIAL PRIMARY KEY,
                            version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
                            metric_name VARCHAR(200) NOT NULL,
                            config JSON,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            updated_at TIMESTAMPTZ,
                            CONSTRAINT uq_model_focus_metric_configs_metric UNIQUE (version_id, metric_name)
                        )
                        """
                    )
                )
                conn.commit()
                print("model_focus_metric_configs 创建完成")
    except Exception as e:
        print(f"数据库自动修复失败 (可能已修复): {e}")

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 执行数据库字段补丁
patch_database()

app = FastAPI(title="型号版本管理系统 API")

# 挂载静态文件目录 (用于访问参考资料等)
BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

import logging
from logging.handlers import RotatingFileHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
handler = RotatingFileHandler("app.log", maxBytes=1000000, backupCount=5)
logger.addHandler(handler)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        traceback.print_exc()
        raise e

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ 全局异常捕获: {exc}")
    error_traceback = traceback.format_exc()
    logger.error(error_traceback)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": error_traceback},
    )

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传目录配置
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# ---------- 动态导入所有路由模块 ----------
for _, module_name, _ in pkgutil.iter_modules(routers_pkg.__path__):
    if module_name == "derivation":
        continue
    try:
        module = importlib.import_module(f"app.routers.{module_name}")
        if hasattr(module, "router"):
            # 为公式路由单独设置一个不带前缀的备用路由，以处理前端可能存在的绝对路径请求
            if module_name == "formulas":
                app.include_router(module.router, tags=["formulas_legacy"])
            
            app.include_router(module.router, prefix="/api")
            print(f"[OK] 已注册路由: /api 从 {module_name}")
        else:
            print(f"[WARN] 模块 {module_name} 未定义 router，跳过")
    except Exception as e:
        print(f"[ERROR] 导入模块 {module_name} 失败: {e}")

# 挂载前端静态文件 (解决离线环境 Vite 依赖问题)
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    frontend_assets = FRONTEND_DIST / "assets"
    frontend_index = FRONTEND_DIST / "index.html"
    if frontend_assets.exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_assets)), name="assets")

    if frontend_index.exists():
        # 挂载根目录下的静态资源
        @app.get("/{file_path:path}")
        async def serve_frontend(file_path: str):
            full_path = FRONTEND_DIST / file_path
            if full_path.is_file():
                return FileResponse(str(full_path))

            # SPA 路由：找不到文件时返回 index.html
            return FileResponse(str(frontend_index))
else:
    print(f"⚠️ 未找到前端编译目录: {FRONTEND_DIST}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
