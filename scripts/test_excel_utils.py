"""
测试脚本，用于验证Excel工具模块的功能

此脚本测试excel_utils模块的主要功能，包括读取、处理和写入Excel文件。
"""
import os
import sys
import pandas as pd

# 添加当前目录到系统路径，以便能够导入excel_utils模块
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from excel_utils import (
    read_excel_to_dataframe,
    process_dataframe,
    read_multiple_sheets,
    write_to_excel
)


def test_read_excel():
    """测试读取Excel文件功能"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建测试文件路径（使用相对路径，根据实际情况调整）
    test_file = os.path.join(script_dir, "test_data.xlsx")
    
    # 创建测试数据
    test_data = pd.DataFrame({
        "姓名": ["张三", "李四", "王五"],
        "年龄": [25, 30, 35],
        "部门": ["技术部", "市场部", "人事部"]
    })
    
    # 写入测试文件
    test_data.to_excel(test_file, sheet_name="Sheet1", index=False)
    print(f"创建测试文件: {test_file}")
    
    # 测试读取功能
    df = read_excel_to_dataframe(test_file, "Sheet1")
    print("\n读取的数据:")
    print(df)
    
    # 测试处理功能
    processed_df = process_dataframe(
        df,
        column_mapping={"姓名": "name", "年龄": "age", "部门": "department"},
        extend_data={"company": "测试公司"}
    )
    print("\n处理后的数据:")
    print(processed_df)
    
    # 测试写入功能
    output_file = os.path.join(script_dir, "test_output.xlsx")
    write_to_excel(processed_df, output_file, "Processed")
    print(f"\n输出文件: {output_file}")
    
    # 清理测试文件
    try:
        os.remove(test_file)
        print(f"删除测试文件: {test_file}")
    except:
        pass


if __name__ == "__main__":
    test_read_excel()
    print("\n测试完成!")
