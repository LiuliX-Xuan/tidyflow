"""分级质量报告生成器"""

import pandas as pd
from datetime import datetime
from tidyflow.diagnoser import Diagnoser, Severity, Diagnostic


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
        self.diagnostics: list[Diagnostic] = []

    def analyze(self) -> list[Diagnostic]:
        """分析数据质量问题"""
        self.diagnostics = []

        if len(self.original_df) == 0:
            return self.diagnostics

        diagnoser = Diagnoser(self.original_df)
        report = diagnoser.diagnose()

        self.diagnostics = report.diagnostics
        return self.diagnostics

    def generate(self) -> str:
        """生成Markdown格式报告"""
        if not self.diagnostics:
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

        critical = [d for d in self.diagnostics if d.severity == Severity.CRITICAL]
        error = [d for d in self.diagnostics if d.severity == Severity.ERROR]
        warning = [d for d in self.diagnostics if d.severity == Severity.WARNING]

        lines.append(f"\n## 问题统计")
        lines.append(f"- [CRITICAL] Critical: {len(critical)} 个")
        lines.append(f"- [ERROR] Error: {len(error)} 个")
        lines.append(f"- [WARNING] Warning: {len(warning)} 个")

        if self.diagnostics:
            lines.append(f"\n## 问题详情")
            for diag in self.diagnostics:
                lines.append(f"- **[{diag.severity.value.upper()}]** {diag.message}")

        lines.append(f"\n## 执行的操作")
        for i, op in enumerate(self.operations, 1):
            lines.append(f"{i}. {op}")

        lines.append(f"\n---\n")
        lines.append("*由 tidyflow 自动生成*")

        return "\n".join(lines)
