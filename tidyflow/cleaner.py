"""核心清洗逻辑，支持链式API调用"""

import pandas as pd
from pathlib import Path
from typing import Any


class Cleaner:
    """数据清洗器，支持CSV/Excel/JSON文件，支持链式API调用"""

    def __init__(self, source: str | Path | pd.DataFrame) -> None:
        """
        初始化清洗器。

        Args:
            source: CSV/Excel/JSON文件路径或DataFrame对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        if isinstance(source, pd.DataFrame):
            self._df = source.copy()
            self._source_path = None
        else:
            self._source_path = Path(source)
            if not self._source_path.exists():
                raise FileNotFoundError(f"文件不存在: {self._source_path}")

            file_size_mb = self._source_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                import warnings
                warnings.warn(f"文件较大 ({file_size_mb:.1f} MB)，处理可能较慢")

            suffix = self._source_path.suffix.lower()
            if suffix == ".csv":
                self._df = self._read_csv_with_fallback(self._source_path)
            elif suffix in (".xlsx", ".xls"):
                self._df = pd.read_excel(self._source_path)
            elif suffix == ".json":
                self._df = pd.read_json(self._source_path)
            else:
                raise ValueError(f"不支持的文件格式: {suffix}，支持: .csv, .xlsx, .xls, .json")

        self._original_df = self._df.copy()
        self._operations: list[str] = []

    @property
    def df(self) -> pd.DataFrame:
        """获取当前DataFrame（只读）"""
        return self._df

    def _read_csv_with_fallback(self, path: Path) -> pd.DataFrame:
        """读取CSV文件，自动检测编码"""
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]
        for encoding in encodings:
            try:
                return pd.read_csv(path, encoding=encoding)
            except UnicodeDecodeError:
                continue
            except pd.errors.EmptyDataError:
                return pd.DataFrame()
        raise ValueError(f"无法检测文件编码: {path}")

    def remove_duplicates(self) -> "Cleaner":
        """删除重复行"""
        before = len(self._df)
        self._df = self._df.drop_duplicates()
        after = len(self._df)
        self._operations.append(f"去重: {before} -> {after} 行")
        return self

    def fill_missing(self, strategy: str = "drop", value: Any = None) -> "Cleaner":
        """
        处理缺失值。

        Args:
            strategy: "drop" 删除 | "mean" 均值 | "median" 中位数 | "value" 固定值
            value: strategy="value" 时使用的固定值
        """
        before = int(self._df.isnull().sum().sum())

        if strategy == "drop":
            self._df = self._df.dropna()
        elif strategy == "mean":
            numeric_cols = self._df.select_dtypes(include=["number"]).columns
            self._df[numeric_cols] = self._df[numeric_cols].fillna(
                self._df[numeric_cols].mean()
            )
        elif strategy == "median":
            numeric_cols = self._df.select_dtypes(include=["number"]).columns
            self._df[numeric_cols] = self._df[numeric_cols].fillna(
                self._df[numeric_cols].median()
            )
        elif strategy == "value":
            self._df = self._df.fillna(value)
        else:
            raise ValueError(f"不支持的策略: {strategy}，支持: drop, mean, median, value")

        after = int(self._df.isnull().sum().sum())
        self._operations.append(f"填空值({strategy}): {before} -> {after} 个缺失")
        return self

    def to_snake_case(self) -> "Cleaner":
        """将列名转换为snake_case格式，分隔符统一转下划线，冲突自动加后缀"""
        import re

        # 去首尾空格 → 小写 → 所有非字母数字分隔符统一转 _
        cleaned = (
            self._df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9]+", "_", regex=True)
            .str.strip("_")
        )
        # 避免全被清空（如纯中文列名）
        empty_mask = cleaned == ""
        if empty_mask.any():
            cleaned[empty_mask] = [f"col_{i}" for i in range(empty_mask.sum())]

        # 冲突检测：重复列名加 _1, _2...
        seen: dict[str, int] = {}
        final: list[str] = []
        for name in cleaned:
            if name in seen:
                seen[name] += 1
                final.append(f"{name}_{seen[name]}")
            else:
                seen[name] = 0
                final.append(name)
        self._df.columns = final

        self._operations.append("列名标准化为snake_case")
        return self

    def strip_text(self) -> "Cleaner":
        """去除文本列的前后空格"""
        text_cols = self._df.select_dtypes(include=["object", "string"]).columns
        for col in text_cols:
            self._df[col] = self._df[col].str.strip()
        self._operations.append(f"文本清洗: {len(text_cols)} 列")
        return self

    def drop_empty_rows(self) -> "Cleaner":
        """删除全空行"""
        before = len(self._df)
        self._df = self._df.dropna(how="all")
        after = len(self._df)
        self._operations.append(f"删空行: {before} -> {after} 行")
        return self

    def clean(self) -> "CleanResult":
        """执行清洗并返回结果"""
        return CleanResult(
            original_df=self._original_df,
            cleaned_df=self._df,
            operations=self._operations,
            source_path=self._source_path,
        )


class CleanResult:
    """清洗结果容器"""

    def __init__(
        self,
        original_df: pd.DataFrame,
        cleaned_df: pd.DataFrame,
        operations: list[str],
        source_path: Path | None,
    ) -> None:
        self.original_df = original_df
        self.cleaned_df = cleaned_df
        self.operations = operations
        self.source_path = source_path

    def save(self, output_path: str | Path) -> None:
        """保存清洗后的数据"""
        path = Path(output_path)
        suffix = path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            self.cleaned_df.to_excel(path, index=False)
        elif suffix == ".json":
            self.cleaned_df.to_json(path, orient="records", force_ascii=False)
        else:
            self.cleaned_df.to_csv(path, index=False)

    def report(self, output_path: str | Path | None = None) -> str:
        """生成质量报告"""
        from tidyflow.reporter import Report

        report = Report(self.original_df, self.cleaned_df, self.operations)
        report_text = report.generate()
        if output_path:
            Path(output_path).write_text(report_text, encoding="utf-8")
        return report_text

    def to_gif(self, output_path: str | Path, duration: int = 1000) -> None:
        """生成清洗前后对比GIF"""
        from tidyflow.utils import create_comparison_gif

        create_comparison_gif(self.original_df, self.cleaned_df, output_path, duration)

    def summary(self) -> dict[str, Any]:
        """返回清洗摘要"""
        return {
            "原始行数": len(self.original_df),
            "清洗后行数": len(self.cleaned_df),
            "删除行数": len(self.original_df) - len(self.cleaned_df),
            "原始缺失值": int(self.original_df.isnull().sum().sum()),
            "清洗后缺失值": int(self.cleaned_df.isnull().sum().sum()),
            "操作数": len(self.operations),
            "操作列表": self.operations,
        }
