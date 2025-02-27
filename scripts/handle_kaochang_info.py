"""
考场信息处理模块

此模块用于处理考场信息Excel文件，包括读取、处理和写入功能。
主要功能是统计不同考点和申报项目的人数。
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

import pandas as pd

# 导入通用Excel处理模块
from .excel_utils import (
    read_excel_to_dataframe,
    process_dataframe,
    read_multiple_sheets,
    process_directory_files,
    write_to_excel
)


# 列名常量定义
COLUMNS = [
    "编号", "姓名", "收款账号身份证号", "收款账号身份证号码", "身份证", 
    "收款账号", "收款账号开户行", "电话号码", "手机号码", "备注", 
    "身份证号", "银行卡号", "发放明细", "次数（小时）", "标准", 
    "其他项目", "电话", "开户行", "工资编号", "工资编码", "分院"
]

# 列名映射字典
COLUMNS_MAPPING = {
    "批次号": "batch_id",
    "申报机构": "declare_org",
    "申报项目": "declare_project",
    "申报项目人数": "declare_project_count",
    "复校合格总人数": "total_count",
    "考核时间": "exam_time",
    "拟定考点": "exam_site",
    "实际考点": "actual_exam_site",
}


def process_kaochang_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理考场数据
    
    Args:
        df: 输入的DataFrame
        
    Returns:
        处理后的DataFrame
    """
    # 检查必要的列是否存在
    required_columns = ['申报项目', '申报项目人数', '拟定考点']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"警告: DataFrame缺少必要的列: {', '.join(missing_columns)}")
        return pd.DataFrame()
    
    # 过滤掉申报项目为空的行
    df = df[df['申报项目'].notna()]
    df = df[df['申报项目人数'].notna()]
    
    # 处理拟定考点字段，将"："替换为":",去除空格
    if '拟定考点' in df.columns:
        df['拟定考点'] = df['拟定考点'].str.replace("：", ":")
        df['拟定考点'] = df['拟定考点'].str.replace(" ", "")
    
    # 将申报项目人数转换为浮点数
    try:
        df['申报项目人数'] = df['申报项目人数'].astype(float)
    except ValueError:
        print("警告: 无法将'申报项目人数'转换为浮点数")
        return pd.DataFrame()
    
    # 只保留需要的列
    df = df[["拟定考点", "申报项目", "申报项目人数"]]
    
    return df


def read_kaochang_info(file_path: str, sheet_lists: List[str]) -> pd.DataFrame:
    """
    读取多个sheet的考场信息并合并
    
    Args:
        file_path: Excel文件路径
        sheet_lists: 要读取的sheet名称列表
        
    Returns:
        合并后的DataFrame
    """
    def process_sheet(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """处理单个sheet的考场数据"""
        # 应用考场数据处理
        df = process_kaochang_data(df)
        
        # 应用列名映射
        df = process_dataframe(
            df,
            fill_na=True,
            fill_method='ffill'
        )
        
        return df
    
    # 读取所有sheet并处理
    df = read_multiple_sheets(
        file_path,
        sheet_lists,
        header=1,  # 考场信息表通常header在第2行
        process_func=process_sheet
    )
    
    return df


def handle_kaochang_info(directory_path: Optional[str] = None) -> pd.DataFrame:
    """
    处理目录中的所有考场信息Excel文件
    
    Args:
        directory_path: 包含Excel文件的目录路径，如果为None则使用默认路径
        
    Returns:
        处理后的DataFrame
    """
    # 使用相对路径或提供的路径
    if directory_path is None:
        # 使用相对于脚本的路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        directory_path = os.path.join(script_dir, "files")
    
    def process_file(file_path: str) -> pd.DataFrame:
        """处理单个考场信息文件"""
        return read_kaochang_info(file_path, sheet_lists=["Sheet1"])
    
    # 处理目录中的所有Excel文件
    return process_directory_files(
        directory_path,
        file_pattern="*.xlsx",
        process_func=process_file
    )


def main():
    """
    主函数，处理考场信息并生成统计结果
    """
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 处理考场信息
    df = handle_kaochang_info()
    
    if df.empty:
        print("没有有效的考场信息数据，程序退出")
        return
    
    # 按照拟定考点和申报项目分组，计算申报项目人数总和
    grouped_df = df.groupby(["拟定考点", "申报项目"])["申报项目人数"].sum().reset_index()
    
    # 按照拟定考点，申报项目排序
    grouped_df = grouped_df.sort_values(by=["拟定考点", "申报项目"])
    
    # 输出文件路径
    output_file_path = os.path.join(script_dir, "kaochang_info.xlsx")
    
    # 写入Excel文件
    write_to_excel(
        grouped_df, 
        output_file_path=output_file_path, 
        sheet_name="kaochang_info"
    )
    
    # 打印统计结果
    print("\n考场信息统计结果:")
    print(grouped_df)
    print(f"\n总考点数: {grouped_df['拟定考点'].nunique()}")
    print(f"总申报项目数: {grouped_df['申报项目'].nunique()}")
    print(f"总申报人数: {grouped_df['申报项目人数'].sum()}")


if __name__ == '__main__':
    main()