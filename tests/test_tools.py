import sys
from pathlib import Path

root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from app.tools import calculator


def test_calculator_multiply():
    assert calculator.invoke({"expression": "500*3"}) == "1500"


def test_calculator_power():
    assert calculator.invoke({"expression": "2**10"}) == "1024"


def test_calculator_divide():
    assert calculator.invoke({"expression": "1200/4"}) == "300.0"


def test_calculator_error_not_crash():
    result = calculator.invoke({"expression": "1/0"})
    assert result.startswith("计算失败")