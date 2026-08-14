"""module level parameters: add module_id to parameter_definitions, create module_parameter_values

Revision ID: 20260807_module_parameters
Revises: 20260727_create_formula_templates
Create Date: 2026-08-07 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260807_module_params'
down_revision = '20260727_formula_tpl'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. parameter_definitions 增加 module_id（先加列，再迁移数据，最后加外键）
    op.add_column('parameter_definitions', sa.Column('module_id', sa.Integer(), nullable=True))

    # 2. 创建 module_parameter_values
    op.create_table(
        'module_parameter_values',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('parameter_id', sa.Integer(), nullable=False),
        sa.Column('param_value', sa.String(length=200), nullable=False),
        sa.Column('value_source', sa.String(length=50), nullable=True),
        sa.Column('version_no', sa.String(length=50), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['formula_template_modules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parameter_id'], ['parameter_definitions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_id', 'version_id', 'parameter_id', name='uq_module_parameter_values_module_version_param'),
    )
    op.create_index(op.f('ix_module_parameter_values_id'), 'module_parameter_values', ['id'], unique=False)

    # 3. 迁移数据：把现有 11 个参数（model_parameter_values 中的记录）挂到“功率计算”模块
    #    功率计算模块 = formula_template_modules 中 module_code='power_calc' 的第一条记录
    module_row = bind.execute(
        sa.text("SELECT id FROM formula_template_modules WHERE module_code = 'power_calc' ORDER BY id LIMIT 1")
    ).fetchone()
    if module_row is not None:
        module_id = module_row[0]
        # 3a. 参数定义挂模块
        bind.execute(
            sa.text(
                "UPDATE parameter_definitions pd SET module_id = :mid "
                "WHERE pd.id IN (SELECT DISTINCT parameter_id FROM model_parameter_values)"
            ),
            {"mid": module_id},
        )
        # 3b. 参数值迁移到模块级表
        bind.execute(
            sa.text(
                "INSERT INTO module_parameter_values "
                "(module_id, version_id, parameter_id, param_value, value_source, version_no, sort_order, remark, created_at, updated_at) "
                "SELECT :mid, version_id, parameter_id, param_value, value_source, version_no, sort_order, remark, created_at, updated_at "
                "FROM model_parameter_values"
            ),
            {"mid": module_id},
        )

    # 4. 外键约束（module_id -> formula_template_modules）
    op.create_foreign_key(
        'fk_parameter_definitions_module_id',
        'parameter_definitions',
        'formula_template_modules',
        ['module_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint('fk_parameter_definitions_module_id', 'parameter_definitions', type_='foreignkey')
    op.drop_index(op.f('ix_module_parameter_values_id'), table_name='module_parameter_values')
    op.drop_table('module_parameter_values')
    op.drop_column('parameter_definitions', 'module_id')
