"""create formula templates

Revision ID: 20260727_create_formula_templates
Revises: 
Create Date: 2026-07-27 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260727_formula_tpl'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # We create the formula templates tables
    op.create_table('formula_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_code', sa.String(length=50), nullable=True),
        sa.Column('template_name', sa.String(length=100), nullable=True),
        sa.Column('product_type_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_formula_templates_id'), 'formula_templates', ['id'], unique=False)
    op.create_index(op.f('ix_formula_templates_template_code'), 'formula_templates', ['template_code'], unique=True)

    op.create_table('formula_template_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('module_code', sa.String(length=50), nullable=True),
        sa.Column('module_name', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['formula_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_formula_template_modules_id'), 'formula_template_modules', ['id'], unique=False)

    op.create_table('formula_template_scenes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('scene_code', sa.String(length=50), nullable=True),
        sa.Column('scene_name', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['module_id'], ['formula_template_modules.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_formula_template_scenes_id'), 'formula_template_scenes', ['id'], unique=False)

    op.create_table('formula_template_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=True),
        sa.Column('formula_name', sa.String(length=100), nullable=True),
        sa.Column('expression', sa.String(length=500), nullable=True),
        sa.Column('variables', sa.JSON(), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['formula_template_scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_formula_template_items_id'), 'formula_template_items', ['id'], unique=False)

    # Add formula_template_id to model_workbench_configs if it doesn't exist
    try:
        op.add_column('model_workbench_configs', sa.Column('formula_template_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_model_workbench_configs_formula_template_id', 'model_workbench_configs', 'formula_templates', ['formula_template_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass


def downgrade() -> None:
    try:
        op.drop_constraint('fk_model_workbench_configs_formula_template_id', 'model_workbench_configs', type_='foreignkey')
        op.drop_column('model_workbench_configs', 'formula_template_id')
    except Exception:
        pass
    
    op.drop_index(op.f('ix_formula_template_items_id'), table_name='formula_template_items')
    op.drop_table('formula_template_items')
    op.drop_index(op.f('ix_formula_template_scenes_id'), table_name='formula_template_scenes')
    op.drop_table('formula_template_scenes')
    op.drop_index(op.f('ix_formula_template_modules_id'), table_name='formula_template_modules')
    op.drop_table('formula_template_modules')
    op.drop_index(op.f('ix_formula_templates_template_code'), table_name='formula_templates')
    op.drop_index(op.f('ix_formula_templates_id'), table_name='formula_templates')
    op.drop_table('formula_templates')
