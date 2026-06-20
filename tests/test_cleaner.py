"""cleaner模块测试"""

import pytest
import pandas as pd
from pathlib import Path
from tidyflow.cleaner import Cleaner, CleanResult


@pytest.fixture
def sample_df():
    """创建测试用DataFrame"""
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie", "Alice", None],
        "Age": [25, 30, 35, 25, 40],
        "City": [" Beijing ", "Shanghai", " Guangzhou ", "Beijing", "Shenzhen"],
    })


@pytest.fixture
def sample_csv(tmp_path, sample_df):
    """创建测试用CSV文件"""
    csv_path = tmp_path / "test.csv"
    sample_df.to_csv(csv_path, index=False)
    return csv_path


@pytest.fixture
def sample_excel(tmp_path, sample_df):
    """创建测试用Excel文件"""
    excel_path = tmp_path / "test.xlsx"
    sample_df.to_excel(excel_path, index=False)
    return excel_path


@pytest.fixture
def sample_json(tmp_path, sample_df):
    """创建测试用JSON文件"""
    json_path = tmp_path / "test.json"
    sample_df.to_json(json_path, orient="records", force_ascii=False)
    return json_path


class TestCleanerInit:
    """Cleaner初始化测试"""

    def test_init_from_df(self, sample_df):
        """测试从DataFrame初始化"""
        cleaner = Cleaner(sample_df)
        assert cleaner._df.shape == sample_df.shape
        assert cleaner._source_path is None

    def test_init_from_csv(self, sample_csv):
        """测试从CSV文件初始化"""
        cleaner = Cleaner(sample_csv)
        assert cleaner._source_path == sample_csv

    def test_init_from_excel(self, sample_excel):
        """测试从Excel文件初始化"""
        cleaner = Cleaner(sample_excel)
        assert cleaner._source_path == sample_excel
        assert len(cleaner._df) == 5

    def test_init_from_json(self, sample_json):
        """测试从JSON文件初始化"""
        cleaner = Cleaner(sample_json)
        assert cleaner._source_path == sample_json
        assert len(cleaner._df) == 5

    def test_init_file_not_found(self):
        """测试文件不存在"""
        with pytest.raises(FileNotFoundError):
            Cleaner("nonexistent.csv")

    def test_init_unsupported_format(self, tmp_path):
        """测试不支持的文件格式"""
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("hello")
        with pytest.raises(ValueError, match="不支持的文件格式"):
            Cleaner(txt_path)

    def test_init_empty_csv(self, tmp_path):
        """测试空CSV文件"""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")
        # pandas读取空文件会返回空DataFrame
        cleaner = Cleaner(csv_path)
        assert len(cleaner._df) == 0


class TestCleanerMethods:
    """Cleaner清洗方法测试"""

    def test_remove_duplicates(self, sample_df):
        """测试去重"""
        cleaner = Cleaner(sample_df)
        result = cleaner.remove_duplicates().clean()
        # 两行Alice的City不同，所以不完全重复
        assert len(result.cleaned_df) == 5

    def test_remove_duplicates_with_exact_dups(self):
        """测试删除完全重复行"""
        df = pd.DataFrame({"A": [1, 1, 2], "B": ["x", "x", "y"]})
        cleaner = Cleaner(df)
        result = cleaner.remove_duplicates().clean()
        assert len(result.cleaned_df) == 2

    def test_fill_missing_drop(self, sample_df):
        """测试删除缺失值"""
        cleaner = Cleaner(sample_df)
        result = cleaner.fill_missing(strategy="drop").clean()
        assert result.cleaned_df.isnull().sum().sum() == 0

    def test_fill_missing_mean(self):
        """测试均值填充"""
        df = pd.DataFrame({"A": [1, 2, None, 4, 5]})
        cleaner = Cleaner(df)
        result = cleaner.fill_missing(strategy="mean").clean()
        assert result.cleaned_df["A"].iloc[2] == 3.0

    def test_fill_missing_median(self):
        """测试中位数填充"""
        df = pd.DataFrame({"A": [1, 2, None, 4, 100]})
        cleaner = Cleaner(df)
        result = cleaner.fill_missing(strategy="median").clean()
        assert result.cleaned_df["A"].iloc[2] == 3.0

    def test_fill_missing_value(self):
        """测试固定值填充"""
        df = pd.DataFrame({"A": [1, None, 3]})
        cleaner = Cleaner(df)
        result = cleaner.fill_missing(strategy="value", value=0).clean()
        assert result.cleaned_df["A"].iloc[1] == 0

    def test_to_snake_case(self):
        """测试列名转换"""
        df = pd.DataFrame({"First Name": [1], "Last-Name": [2]})
        cleaner = Cleaner(df)
        result = cleaner.to_snake_case().clean()
        assert "first_name" in result.cleaned_df.columns
        assert "last_name" in result.cleaned_df.columns

    def test_to_snake_case_duplicate_columns(self):
        """测试冲突列名自动加后缀"""
        df = pd.DataFrame({"Name": [1], "Name ": [2], "name": [3]})
        cleaner = Cleaner(df)
        result = cleaner.to_snake_case().clean()
        assert "name" in result.cleaned_df.columns
        assert "name_1" in result.cleaned_df.columns
        assert "name_2" in result.cleaned_df.columns

    def test_strip_text(self, sample_df):
        """测试文本清洗"""
        cleaner = Cleaner(sample_df)
        result = cleaner.strip_text().clean()
        assert result.cleaned_df["City"].iloc[0] == "Beijing"

    def test_strip_text_no_text_columns(self):
        """测试无数值列时文本清洗"""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4.0, 5.0, 6.0]})
        cleaner = Cleaner(df)
        result = cleaner.strip_text().clean()
        assert len(result.operations) == 1

    def test_drop_empty_rows(self):
        """测试删除全空行"""
        df = pd.DataFrame({"A": [1, None, 3], "B": [4, None, 6]})
        cleaner = Cleaner(df)
        result = cleaner.drop_empty_rows().clean()
        assert len(result.cleaned_df) == 2

    def test_chain_api(self, sample_df):
        """测试链式API"""
        result = (
            Cleaner(sample_df)
            .remove_duplicates()
            .fill_missing(strategy="drop")
            .to_snake_case()
            .strip_text()
            .clean()
        )
        assert isinstance(result, CleanResult)
        assert len(result.operations) == 4


class TestCleanResult:
    """CleanResult类测试"""

    def test_save_csv(self, sample_df, tmp_path):
        """测试保存CSV"""
        result = Cleaner(sample_df).clean()
        output_path = tmp_path / "output.csv"
        result.save(output_path)
        assert output_path.exists()
        # 验证保存的内容
        saved_df = pd.read_csv(output_path)
        assert len(saved_df) == len(result.cleaned_df)

    def test_save_excel(self, sample_df, tmp_path):
        """测试保存Excel"""
        result = Cleaner(sample_df).clean()
        output_path = tmp_path / "output.xlsx"
        result.save(output_path)
        assert output_path.exists()

    def test_save_json(self, sample_df, tmp_path):
        """测试保存JSON"""
        result = Cleaner(sample_df).clean()
        output_path = tmp_path / "output.json"
        result.save(output_path)
        assert output_path.exists()

    def test_summary(self, sample_df):
        """测试摘要"""
        result = Cleaner(sample_df).clean()
        summary = result.summary()
        assert "原始行数" in summary
        assert "清洗后行数" in summary
        assert summary["原始行数"] == 5
        assert summary["操作数"] == 0

    def test_report(self, sample_df):
        """测试报告生成"""
        result = Cleaner(sample_df).clean()
        report_text = result.report()
        assert "数据质量报告" in report_text

    def test_report_with_file(self, sample_df, tmp_path):
        """测试报告保存到文件"""
        result = Cleaner(sample_df).clean()
        report_path = tmp_path / "report.md"
        result.report(report_path)
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "数据质量报告" in content

    def test_to_gif(self, sample_df, tmp_path):
        """测试GIF生成"""
        result = Cleaner(sample_df).clean()
        gif_path = tmp_path / "test.gif"
        result.to_gif(gif_path)
        assert gif_path.exists()
        assert gif_path.stat().st_size > 0

    def test_fill_missing_invalid_strategy(self):
        """测试未知策略抛出ValueError"""
        df = pd.DataFrame({"A": [1, None, 3]})
        cleaner = Cleaner(df)
        with pytest.raises(ValueError, match="不支持的策略"):
            cleaner.fill_missing(strategy="mode")
