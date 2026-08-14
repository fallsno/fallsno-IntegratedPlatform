import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, FormulaTemplate, ModelWorkbenchConfig

# Use a memory sqlite for testing
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_create_formula_template():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    
    template = FormulaTemplate(template_code="HTS_BASE", template_name="再生系列模板")
    db_session.add(template)
    db_session.commit()
    
    assert template.id is not None
    print("test_create_formula_template passed! template.id:", template.id)
    
    config = ModelWorkbenchConfig(model_version_id=1, formula_template_id=template.id)
    db_session.add(config)
    db_session.commit()
    assert config.id is not None
    print("ModelWorkbenchConfig created with formula_template_id:", config.formula_template_id)
    
    db_session.close()

if __name__ == "__main__":
    test_create_formula_template()
