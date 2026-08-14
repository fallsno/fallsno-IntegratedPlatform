import os
import psycopg2
from psycopg2.extras import RealDictCursor

# 从环境变量或默认配置中获取连接信息
DATABASE_URL = "postgresql://postgres:605678788@127.0.0.1:5000/model_db"

def run_patch():
    print("Connecting to database...")
    conn = None
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            client_encoding="utf8",
            options="-c lc_messages=C"
        )
        conn.autocommit = False
        cursor = conn.cursor()

        # 1. 检查并添加 FormulaTemplateScene 的 scene_type 字段
        print("Checking formula_template_scenes table...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'formula_template_scenes' AND column_name = 'scene_type';
        """)
        col = cursor.fetchone()
        if not col:
            print("Adding scene_type to formula_template_scenes...")
            cursor.execute("ALTER TABLE formula_template_scenes ADD COLUMN scene_type VARCHAR(50) DEFAULT 'calc';")
        else:
            # 如果存在，可能需要修改它的类型和默认值
            print("Updating scene_type in formula_template_scenes...")
            cursor.execute("ALTER TABLE formula_template_scenes ALTER COLUMN scene_type TYPE VARCHAR(50);")
            cursor.execute("ALTER TABLE formula_template_scenes ALTER COLUMN scene_type SET DEFAULT 'calc';")

        # 2. 检查并添加/修改 FormulaTemplateItem 的 output_flag 字段
        print("Checking formula_template_items table...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'formula_template_items' AND column_name = 'output_flag';
        """)
        col = cursor.fetchone()
        if not col:
            print("Adding output_flag to formula_template_items...")
            cursor.execute("ALTER TABLE formula_template_items ADD COLUMN output_flag VARCHAR(20) DEFAULT 'auto';")
        else:
            # 如果已存在（旧的是 boolean），我们需要修改类型并设置默认值
            data_type = col[1]
            if data_type == 'boolean':
                print("Converting output_flag in formula_template_items from boolean to varchar...")
                cursor.execute("""
                    ALTER TABLE formula_template_items 
                    ALTER COLUMN output_flag TYPE VARCHAR(20) USING CASE WHEN output_flag = TRUE THEN 'force_true' ELSE 'auto' END;
                """)
            else:
                cursor.execute("ALTER TABLE formula_template_items ALTER COLUMN output_flag TYPE VARCHAR(20);")
            cursor.execute("ALTER TABLE formula_template_items ALTER COLUMN output_flag SET DEFAULT 'auto';")

        # 3. 重建 model_selection_mappings 表
        print("Recreating model_selection_mappings table...")
        cursor.execute("DROP TABLE IF EXISTS model_selection_mappings CASCADE;")
        cursor.execute("""
            CREATE TABLE model_selection_mappings (
                id SERIAL PRIMARY KEY,
                version_id INTEGER NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
                target_category VARCHAR(50) NOT NULL,
                target_field VARCHAR(100) NOT NULL,
                source_parameter VARCHAR(200) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                CONSTRAINT uq_model_selection_mappings_field UNIQUE (version_id, target_category, target_field)
            );
        """)
        
        # 4. 创建索引
        cursor.execute("CREATE INDEX ix_model_selection_mappings_id ON model_selection_mappings (id);")

        conn.commit()
        print("Patch applied successfully!")

    except Exception as e:
        if conn:
            conn.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error applying patch: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    run_patch()
