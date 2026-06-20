"""生成测试用脏数据"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_dirty_data(rows: int = 100, output_path: str = "dirty_data.csv"):
    """生成包含各种问题的CSV数据"""
    np.random.seed(42)

    # 基础数据
    names = ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", None]
    cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", None]
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]

    data = {
        "Employee Name": np.random.choice(names, rows),
        "Employee Age": np.random.choice([25, 30, 35, 40, None], rows),
        "Department": np.random.choice(departments, rows),
        "City ": np.random.choice(cities, rows),  # 列名有空格
        "Salary": np.random.randint(5000, 50000, rows).astype(float),
        " Join Date": [  # 列名有空格
            f"2024-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}"
            for _ in range(rows)
        ],
    }

    df = pd.DataFrame(data)

    # 添加一些重复行
    dup_rows = df.sample(n=min(10, rows // 10))
    df = pd.concat([df, dup_rows], ignore_index=True)

    # 保存
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"已生成测试数据: {output_path} ({len(df)} 行)")

    return df


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成测试用脏数据")
    parser.add_argument("-n", "--rows", type=int, default=100, help="生成行数")
    parser.add_argument("-o", "--output", default="examples/dirty_data.csv", help="输出路径")
    args = parser.parse_args()

    generate_dirty_data(args.rows, args.output)
