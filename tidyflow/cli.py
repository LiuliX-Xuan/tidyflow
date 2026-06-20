"""命令行接口"""

import sys
import click
from pathlib import Path
from tidyflow.cleaner import Cleaner
from tidyflow.utils import format_number


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """tidyflow - 专业的数据清洗CLI工具"""
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("-o", "--output", default=None, help="输出文件路径")
@click.option("--report", is_flag=True, help="生成质量报告")
@click.option("--report-path", default=None, help="报告输出路径")
@click.option("--gif", is_flag=True, help="生成对比GIF")
@click.option("--gif-path", default=None, help="GIF输出路径")
@click.option(
    "--fill-strategy",
    type=click.Choice(["drop", "mean", "median"]),
    default="drop",
    help="缺失值处理策略",
)
@click.option("--no-dedup", is_flag=True, help="不删除重复行")
@click.option("--no-snake", is_flag=True, help="不转换列名为snake_case")
def clean(
    input_file: str,
    output: str | None,
    report: bool,
    report_path: str | None,
    gif: bool,
    gif_path: str | None,
    fill_strategy: str,
    no_dedup: bool,
    no_snake: bool,
) -> None:
    """清洗CSV/Excel/JSON文件"""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    input_path = Path(input_file)

    # 默认输出路径（保持原格式）
    if output is None:
        suffix = input_path.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            output = str(input_path.parent / f"{input_path.stem}_cleaned.xlsx")
        elif suffix == ".json":
            output = str(input_path.parent / f"{input_path.stem}_cleaned.json")
        else:
            output = str(input_path.parent / f"{input_path.stem}_cleaned.csv")

    console.print(f"\n[bold blue]tidyflow[/bold blue] 清洗中...\n")

    try:
        cleaner = Cleaner(input_file)

        if not no_dedup:
            cleaner.remove_duplicates()

        cleaner.fill_missing(strategy=fill_strategy)

        if not no_snake:
            cleaner.to_snake_case()

        cleaner.strip_text()
        cleaner.drop_empty_rows()

        result = cleaner.clean()
        result.save(output)

        summary = result.summary()
        table = Table(title="清洗结果")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")
        table.add_row("原始行数", format_number(summary["原始行数"]))
        table.add_row("清洗后行数", format_number(summary["清洗后行数"]))
        table.add_row("删除行数", format_number(summary["删除行数"]))
        table.add_row("原始缺失值", format_number(summary["原始缺失值"]))
        table.add_row("清洗后缺失值", format_number(summary["清洗后缺失值"]))
        console.print(table)

        console.print("\n[bold]执行的操作:[/bold]")
        for op in summary["操作列表"]:
            console.print(f"  -> {op}")

        if report:
            rp = report_path or str(input_path.parent / "quality_report.md")
            result.report(rp)
            console.print(f"\n[green][OK] 报告已生成:[/green] {rp}")

        if gif:
            gp = gif_path or str(input_path.parent / "comparison.gif")
            result.to_gif(gp)
            console.print(f"[green][OK] GIF已生成:[/green] {gp}")

        console.print(f"\n[green][OK] 清洗完成:[/green] {output}\n")

    except FileNotFoundError as e:
        console.print(f"\n[red][ERROR] {e}[/red]\n")
        sys.exit(1)
    except ValueError as e:
        console.print(f"\n[red][ERROR] {e}[/red]\n")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red][ERROR] 清洗失败: {e}[/red]\n")
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def report(input_file: str) -> None:
    """仅生成质量报告（不清洗）"""
    from rich.console import Console

    console = Console()
    console.print(f"\n[bold blue]tidyflow[/bold blue] 分析中...\n")

    try:
        cleaner = Cleaner(input_file)
        result = cleaner.clean()
        report_text = result.report()
        console.print(report_text)
    except Exception as e:
        console.print(f"\n[red][ERROR] 分析失败: {e}[/red]\n")
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
def info(input_file: str) -> None:
    """查看文件基本信息（支持CSV/Excel/JSON）"""
    from rich.console import Console
    from rich.table import Table

    console = Console()

    try:
        cleaner = Cleaner(input_file)
        df = cleaner._df

        console.print(f"\n[bold]{input_file}[/bold]\n")

        table = Table(title="文件信息")
        table.add_column("指标", style="cyan")
        table.add_column("值", style="green")
        table.add_row("行数", format_number(len(df)))
        table.add_row("列数", str(len(df.columns)))
        table.add_row("缺失值总数", format_number(int(df.isnull().sum().sum())))
        table.add_row("重复行数", format_number(int(df.duplicated().sum())))
        console.print(table)

        col_table = Table(title="列信息")
        col_table.add_column("列名", style="cyan")
        col_table.add_column("类型", style="yellow")
        col_table.add_column("缺失值", style="red")
        for col in df.columns:
            col_table.add_row(
                col,
                str(df[col].dtype),
                str(int(df[col].isnull().sum())),
            )
        console.print(col_table)
        console.print()

    except Exception as e:
        console.print(f"\n[red][ERROR] 读取失败: {e}[/red]\n")
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--json", "output_json", is_flag=True, help="输出JSON格式")
def detect(input_file: str, output_json: bool) -> None:
    """诊断数据问题并给出修复建议"""
    from rich.console import Console
    from tidyflow.diagnoser import Diagnoser

    console = Console()
    console.print(f"\n[bold blue]tidyflow[/bold blue] 诊断中...\n")

    try:
        cleaner = Cleaner(input_file)
        diagnoser = Diagnoser(cleaner._df)
        report = diagnoser.diagnose()

        if output_json:
            import json
            console.print_json(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        else:
            if report.criticals:
                console.print(f"[red][CRITICAL] ({len(report.criticals)})[/red]")
                for d in report.criticals:
                    console.print(f"  * {d.message}")
                    console.print(f"    [dim]-> {d.suggestion}[/dim]")

            if report.errors:
                console.print(f"\n[red][ERROR] ({len(report.errors)})[/red]")
                for d in report.errors:
                    console.print(f"  * {d.message}")
                    console.print(f"    [dim]-> {d.suggestion}[/dim]")

            if report.warnings:
                console.print(f"\n[yellow][WARNING] ({len(report.warnings)})[/yellow]")
                for d in report.warnings:
                    console.print(f"  * {d.message}")
                    console.print(f"    [dim]-> {d.suggestion}[/dim]")

            if not report.diagnostics:
                console.print("[green]未发现问题[/green]")

            console.print()

    except Exception as e:
        console.print(f"\n[red][ERROR] 诊断失败: {e}[/red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
