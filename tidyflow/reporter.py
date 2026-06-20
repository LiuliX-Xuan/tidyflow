"""分级质量报告生成器"""

import pandas as pd
from datetime import datetime
from tidyflow.diagnoser import Diagnoser, Severity


class Issue:
    """单个数据质量问题"""

    def __init__(self, severity: str, category: str, message: str, count: int) -> None:
        self.severity = severity
        self.category = category
        self.message = message
        self.count = count

    def to_dict(self) -> dict[str, str | int]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "count": self.count,
        }


class Report:
    """分级质量报告生成器，复用 Diagnoser 逻辑生成 Markdown 报告"""

    def __init__(
        self,
        original_df: pd.DataFrame,
        cleaned_df: pd.DataFrame,
        operations: list[str],
    ) -> None:
        self.original_df = original_df
        self.cleaned_df = cleaned_df
        self.operations = operations
        self.issues: list[Issue] = []

    def analyze(self) -> list[Issue]:
        """分析数据质量问题"""
        self.issues = []

        if len(self.original_df) == 0:
            return self.issues

        diagnoser = Diagnoser(self.original_df)
        report = diagnoser.diagnose()

        for d in report.diagnostics:
            self.issues.append(Issue(
                severity=d.severity,
                category=d.category,
                message=d.message,
                count=1,
            ))

        return self.issues

    def generate(self) -> str:
        """生成Markdown格式报告"""
        if not self.issues:
            self.analyze()

        lines: list[str] = []
        lines.append("# 数据质量报告")
        lines.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"\n---\n")

        lines.append("## 概览")
        lines.append(f"- 原始行数: {len(self.original_df)}")
        lines.append(f"- 清洗后行数: {len(self.cleaned_df)}")
        lines.append(f"- 删除行数: {len(self.original_df) - len(self.cleaned_df)}")
        lines.append(f"- 原始缺失值: {int(self.original_df.isnull().sum().sum())}")
        lines.append(f"- 清洗后缺失值: {int(self.cleaned_df.isnull().sum().sum())}")

        critical = [i for i in self.issues if i.severity == Severity.CRITICAL]
        error = [i for i in self.issues if i.severity == Severity.ERROR]
        warning = [i for i in self.issues if i.severity == Severity.WARNING]

        lines.append(f"\n## 问题统计")
        lines.append(f"- [CRITICAL] Critical: {len(critical)} 个")
        lines.append(f"- [ERROR] Error: {len(error)} 个")
        lines.append(f"- [WARNING] Warning: {len(warning)} 个")

        if self.issues:
            lines.append(f"\n## 问题详情")
            for issue in self.issues:
                lines.append(f"- **[{issue.severity.upper()}]** {issue.message}")

        lines.append(f"\n## 执行的操作")
        for i, op in enumerate(self.operations, 1):
            lines.append(f"{i}. {op}")

        lines.append(f"\n---\n")
        lines.append("*由 tidyflow 自动生成*")

        return "\n".join(lines)
