"""数据诊断器，检测数据问题并给出修复建议"""

import pandas as pd
from dataclasses import dataclass, field


class Severity:
    """问题严重程度分级"""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Diagnostic:
    """单个诊断结果"""
    severity: str
    category: str
    message: str
    suggestion: str
    column: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "suggestion": self.suggestion,
            "column": self.column,
        }


@dataclass
class DiagnosticReport:
    """诊断报告"""
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def warnings(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "warning"]

    @property
    def errors(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "error"]

    @property
    def criticals(self) -> list[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "critical"]

    def to_dict(self) -> dict[str, list[dict]]:
        return {
            "warnings": [d.to_dict() for d in self.warnings],
            "errors": [d.to_dict() for d in self.errors],
            "criticals": [d.to_dict() for d in self.criticals],
        }

    def summary(self) -> str:
        """生成文本摘要"""
        lines: list[str] = []
        lines.append("数据诊断报告")
        lines.append("=" * 40)

        if self.criticals:
            lines.append(f"\nCRITICAL ({len(self.criticals)})")
            for d in self.criticals:
                lines.append(f"  * {d.message}")
                lines.append(f"    -> {d.suggestion}")

        if self.errors:
            lines.append(f"\nERROR ({len(self.errors)})")
            for d in self.errors:
                lines.append(f"  * {d.message}")
                lines.append(f"    -> {d.suggestion}")

        if self.warnings:
            lines.append(f"\nWARNING ({len(self.warnings)})")
            for d in self.warnings:
                lines.append(f"  * {d.message}")
                lines.append(f"    -> {d.suggestion}")

        if not self.diagnostics:
            lines.append("\n未发现问题")

        lines.append("\n" + "=" * 40)
        return "\n".join(lines)


class Diagnoser:
    """数据诊断器，检测数据问题并给出修复建议"""

    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df
        self.diagnostics: list[Diagnostic] = []

    def diagnose(self) -> DiagnosticReport:
        """执行完整诊断"""
        self.diagnostics = []

        self._check_missing_values()
        self._check_duplicates()
        self._check_empty_rows()
        self._check_column_names()
        self._check_text_whitespace()
        self._check_type_mismatch()

        return DiagnosticReport(diagnostics=self.diagnostics)

    def _check_missing_values(self) -> None:
        """检查缺失值"""
        if len(self.df) == 0:
            return

        missing = self.df.isnull().sum()
        for col, count in missing.items():
            if count > 0:
                ratio = count / len(self.df)
                is_numeric = pd.api.types.is_numeric_dtype(self.df[col])

                if ratio > 0.5:
                    self.diagnostics.append(Diagnostic(
                        severity="critical",
                        category="缺失值",
                        message=f"列 '{col}' 缺失率 {ratio:.0%} ({count} 行)",
                        suggestion="fill_missing(strategy='drop')",
                        column=str(col),
                    ))
                elif ratio > 0.1:
                    strategy = "mean" if is_numeric else "drop"
                    self.diagnostics.append(Diagnostic(
                        severity="error",
                        category="缺失值",
                        message=f"列 '{col}' 缺失率 {ratio:.0%} ({count} 行)",
                        suggestion=f"fill_missing(strategy='{strategy}')",
                        column=str(col),
                    ))
                elif count > 0:
                    self.diagnostics.append(Diagnostic(
                        severity="warning",
                        category="缺失值",
                        message=f"列 '{col}' 缺失 {count} 行",
                        suggestion=f"fill_missing(strategy='drop')",
                        column=str(col),
                    ))

    def _check_duplicates(self) -> None:
        """检查重复行"""
        if len(self.df) == 0:
            return

        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            ratio = dup_count / len(self.df)
            if ratio > 0.1:
                self.diagnostics.append(Diagnostic(
                    severity="error",
                    category="重复行",
                    message=f"{dup_count} 行重复 ({ratio:.0%})",
                    suggestion="remove_duplicates()",
                ))
            else:
                self.diagnostics.append(Diagnostic(
                    severity="warning",
                    category="重复行",
                    message=f"发现 {dup_count} 行重复",
                    suggestion="remove_duplicates()",
                ))

    def _check_empty_rows(self) -> None:
        """检查空行"""
        empty_rows = int(self.df.isnull().all(axis=1).sum())
        if empty_rows > 0:
            self.diagnostics.append(Diagnostic(
                severity="warning",
                category="空行",
                message=f"发现 {empty_rows} 行完全为空",
                suggestion="drop_empty_rows()",
            ))

    def _check_column_names(self) -> None:
        """检查列名格式（是否符合 [a-z0-9_]+ 格式）"""
        import re
        pattern = re.compile(r"^[a-z0-9_]+$")
        messy_cols = [
            col for col in self.df.columns
            if not pattern.match(str(col).strip().lower())
        ]
        if messy_cols:
            cols_str = ", ".join([f"'{c}'" for c in messy_cols[:3]])
            if len(messy_cols) > 3:
                cols_str += f" 等 {len(messy_cols)} 列"
            self.diagnostics.append(Diagnostic(
                severity="warning",
                category="列名格式",
                message=f"列名不规范: {cols_str}",
                suggestion="to_snake_case()",
            ))

    def _check_text_whitespace(self) -> None:
        """检查文本列前后空格"""
        text_cols = self.df.select_dtypes(include=["object", "string"]).columns
        cols_with_space: list[str] = []
        for col in text_cols:
            has_space = self.df[col].dropna().apply(
                lambda x: str(x) != str(x).strip()
            ).any()
            if has_space:
                cols_with_space.append(str(col))

        if cols_with_space:
            cols_str = ", ".join([f"'{c}'" for c in cols_with_space[:3]])
            self.diagnostics.append(Diagnostic(
                severity="warning",
                category="文本空格",
                message=f"列含前后空格: {cols_str}",
                suggestion="strip_text()",
            ))

    def _check_type_mismatch(self) -> None:
        """检查类型不匹配（数字存为字符串）"""
        for col in self.df.columns:
            if self.df[col].dtype in ("object", "string"):
                sample = self.df[col].dropna().head(100)
                if len(sample) == 0:
                    continue
                try:
                    pd.to_numeric(sample, errors="raise")
                    self.diagnostics.append(Diagnostic(
                        severity="warning",
                        category="类型不匹配",
                        message=f"列 '{col}' 存为字符串但可转为数字",
                        suggestion=f"考虑转换类型: df['{col}'] = pd.to_numeric(df['{col}'])",
                        column=str(col),
                    ))
                except (ValueError, TypeError):
                    pass
