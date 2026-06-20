"""diagnoser模块测试"""

import pytest
import pandas as pd
from tidyflow.diagnoser import Diagnoser, DiagnosticReport, Diagnostic


@pytest.fixture
def dirty_df():
    """创建包含各种问题的DataFrame"""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", None, "Alice", None],
        "Age": [25, 30, 35, 25, 40],
        "City": [" Beijing", "Shanghai", "Guangzhou", "Beijing", "Shenzhen"],
        "Score": ["100", "200", "300", "400", "500"],  # 数字存为字符串
    })


@pytest.fixture
def clean_df():
    """创建干净的DataFrame"""
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "city": ["Beijing", "Shanghai", "Guangzhou"],
    })


class TestDiagnostic:
    """Diagnostic数据类测试"""

    def test_to_dict(self):
        """测试to_dict方法"""
        d = Diagnostic(
            severity="warning",
            category="缺失值",
            message="列A缺失",
            suggestion="fill_missing()",
            column="A",
        )
        result = d.to_dict()
        assert result["severity"] == "warning"
        assert result["column"] == "A"

    def test_to_dict_no_column(self):
        """测试无列名时to_dict"""
        d = Diagnostic(
            severity="error",
            category="重复行",
            message="有重复",
            suggestion="remove_duplicates()",
        )
        result = d.to_dict()
        assert result["column"] is None


class TestDiagnosticReport:
    """DiagnosticReport测试"""

    def test_empty_report(self):
        """测试空报告"""
        report = DiagnosticReport()
        assert len(report.warnings) == 0
        assert len(report.errors) == 0
        assert len(report.criticals) == 0
        assert "未发现问题" in report.summary()

    def test_report_with_issues(self):
        """测试有问题的报告"""
        diagnostics = [
            Diagnostic("warning", "类别", "消息1", "建议1"),
            Diagnostic("error", "类别", "消息2", "建议2"),
            Diagnostic("critical", "类别", "消息3", "建议3"),
        ]
        report = DiagnosticReport(diagnostics=diagnostics)
        assert len(report.warnings) == 1
        assert len(report.errors) == 1
        assert len(report.criticals) == 1

    def test_to_dict(self):
        """测试to_dict方法"""
        diagnostics = [
            Diagnostic("warning", "类别", "消息", "建议"),
        ]
        report = DiagnosticReport(diagnostics=diagnostics)
        result = report.to_dict()
        assert "warnings" in result
        assert len(result["warnings"]) == 1


class TestDiagnoser:
    """Diagnoser类测试"""

    def test_diagnose_clean_data(self, clean_df):
        """测试诊断干净数据"""
        diagnoser = Diagnoser(clean_df)
        report = diagnoser.diagnose()
        assert len(report.diagnostics) == 0

    def test_diagnose_missing_values(self):
        """测试诊断缺失值"""
        df = pd.DataFrame({"A": [1, None, 3], "B": [4, 5, None]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        assert len(report.diagnostics) > 0
        # 应该有缺失值相关的诊断
        categories = [d.category for d in report.diagnostics]
        assert "缺失值" in categories

    def test_diagnose_duplicates(self):
        """测试诊断重复行"""
        df = pd.DataFrame({"A": [1, 1, 2], "B": ["x", "x", "y"]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        categories = [d.category for d in report.diagnostics]
        assert "重复行" in categories

    def test_diagnose_empty_rows(self):
        """测试诊断空行"""
        df = pd.DataFrame({"A": [1, None, 3], "B": [4, None, 6]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        categories = [d.category for d in report.diagnostics]
        assert "空行" in categories

    def test_diagnose_column_names(self):
        """测试诊断列名格式"""
        df = pd.DataFrame({"First Name": [1], "Last-Name": [2]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        categories = [d.category for d in report.diagnostics]
        assert "列名格式" in categories

    def test_diagnose_text_whitespace(self):
        """测试诊断文本空格"""
        df = pd.DataFrame({"A": [" hello", "world "]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        categories = [d.category for d in report.diagnostics]
        assert "文本空格" in categories

    def test_diagnose_type_mismatch(self):
        """测试诊断类型不匹配"""
        df = pd.DataFrame({"A": ["100", "200", "300"]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        categories = [d.category for d in report.diagnostics]
        assert "类型不匹配" in categories

    def test_diagnose_multiple_issues(self, dirty_df):
        """测试诊断多个问题"""
        diagnoser = Diagnoser(dirty_df)
        report = diagnoser.diagnose()
        # 应该有多种问题
        categories = set(d.category for d in report.diagnostics)
        assert len(categories) >= 3

    def test_diagnose_empty_df(self):
        """测试诊断空DataFrame"""
        df = pd.DataFrame()
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        assert len(report.diagnostics) == 0

    def test_diagnose_suggestions_are_valid(self, dirty_df):
        """测试修复建议是有效的Python代码"""
        diagnoser = Diagnoser(dirty_df)
        report = diagnoser.diagnose()
        for d in report.diagnostics:
            # 建议应该包含函数调用
            assert "(" in d.suggestion or "考虑" in d.suggestion

    def test_diagnose_text_column_suggests_drop(self):
        """测试文本列缺失值建议是drop而不是mean"""
        df = pd.DataFrame({"name": ["Alice", None, "Charlie", None, "Eve"]})
        diagnoser = Diagnoser(df)
        report = diagnoser.diagnose()
        suggestions = [d.suggestion for d in report.diagnostics if d.category == "缺失值"]
        assert any("drop" in s for s in suggestions)
        assert not any("mean" in s for s in suggestions)
