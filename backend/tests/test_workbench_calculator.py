import pytest

def test_calculator_merges_template_and_params():
    from app.services.workbench_calculator import calculate_workbench_instance
    
    # 模拟模板公式 (只读)
    template_data = {
        "modules": [{
            "scenes": [{
                "items": [
                    {"formula_name": "存料量", "expression": "=进料量*1000/60", "variables": ["进料量"]},
                    {"formula_name": "总重量", "expression": "=存料量+设备自重", "variables": ["存料量", "设备自重"]}
                ]
            }]
        }]
    }
    
    # 模拟该型号参数中心的实际参数
    model_params = {
        "进料量": {"value": 38, "unit": "t/h"},
        "设备自重": {"value": 100, "unit": "t"}
    }
    
    result = calculate_workbench_instance(template_data, model_params)
    assert result["存料量"]["value"] == pytest.approx(633.33, 0.01)
    assert result["总重量"]["value"] == pytest.approx(733.33, 0.01)


def test_calculator_supports_dict_variables_and_numeric_strings():
    from app.services.workbench_calculator import calculate_workbench_instance

    template_data = {
        "modules": [{
            "scenes": [{
                "items": [
                    {
                        "formula_name": "存料量",
                        "expression": "=进料量*1000/60",
                        "variables": {"进料量": "t/h"},
                        "unit": "kg"
                    },
                    {
                        "formula_name": "总重量",
                        "expression": "=存料量+设备自重",
                        "variables": {"存料量": "kg", "设备自重": "kg"},
                        "unit": "kg"
                    }
                ]
            }]
        }]
    }

    model_params = {
        "进料量": {"value": "38", "unit": "t/h"},
        "设备自重": {"value": "100", "unit": "kg"}
    }

    result = calculate_workbench_instance(template_data, model_params)
    assert result["存料量"]["value"] == pytest.approx(633.33, 0.01)
    assert result["总重量"]["value"] == pytest.approx(733.33, 0.01)
