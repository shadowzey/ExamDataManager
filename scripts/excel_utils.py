"""
Excel 处理工具模块

提供通用的 Excel 文件处理功能，包括读取、处理和写入操作。
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional, Tuple, Callable

import pandas as pd


def read_excel_to_dataframe(
    file_path: str, 
    sheet_name: str, 
    header: int = 0, 
    skiprows: int = 0,
    required_columns: List[str] = None
) -> pd.DataFrame:
    """
    读取 Excel 文件中的指定 sheet 到 DataFrame
    
    Args:
        file_path: Excel 文件路径
        sheet_name: 要读取的 sheet 名称
        header: 表头行索引，默认为 0
        skiprows: 跳过的行数，默认为 0
        required_columns: 必需的列名列表，如果指定则会检查这些列是否存在
        
    Returns:
        读取的 DataFrame
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当 sheet 不存在或数据格式不正确时
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 '{file_path}' 不存在")
            
        # 读取 Excel 文件中的指定 sheet，并将指定行作为列标题
        df = pd.read_excel(
            file_path, 
            sheet_name=sheet_name, 
            header=header, 
            dtype=str, 
            skiprows=skiprows
        )
        
        # 检查必要的列是否存在
        if required_columns:
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Excel 文件缺少必要的列: {', '.join(missing_columns)}")
                
        return df
        
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        return pd.DataFrame()
    except ValueError as e:
        print(f"错误: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        print(f"处理 Excel 文件时发生错误: {str(e)}")
        return pd.DataFrame()


def process_dataframe(
    df: pd.DataFrame,
    process_func: Callable[[pd.DataFrame], pd.DataFrame] = None,
    filter_conditions: Dict[str, Any] = None,
    column_mapping: Dict[str, str] = None,
    extend_data: Dict[str, Any] = None,
    fill_na: bool = False,
    fill_method: str = 'ffill'
) -> pd.DataFrame:
    """
    处理 DataFrame 数据
    
    Args:
        df: 要处理的 DataFrame
        process_func: 自定义处理函数，接收 DataFrame 并返回处理后的 DataFrame
        filter_conditions: 过滤条件，格式为 {列名: 条件}
        column_mapping: 列名映射，格式为 {原列名: 新列名}
        extend_data: 要添加的额外数据，格式为 {列名: 值}
        fill_na: 是否填充缺失值
        fill_method: 填充方法，默认为 'ffill'（前向填充）
        
    Returns:
        处理后的 DataFrame
    """
    if df.empty:
        return df
        
    # 应用自定义处理函数
    if process_func:
        df = process_func(df)
        
    # 应用过滤条件
    if filter_conditions:
        for column, condition in filter_conditions.items():
            if column in df.columns:
                if callable(condition):
                    df = df[condition(df[column])]
                else:
                    df = df[df[column] == condition]
    
    # 填充缺失值
    if fill_na:
        df = df.fillna(method=fill_method)
    
    # 重命名列
    if column_mapping:
        # 只重命名存在的列
        mapping_to_apply = {k: v for k, v in column_mapping.items() if k in df.columns}
        if mapping_to_apply:
            df = df.rename(columns=mapping_to_apply)
    
    # 添加额外数据
    if extend_data:
        for column, value in extend_data.items():
            df[column] = value
    
    return df


def read_multiple_sheets(
    file_path: str,
    sheet_list: List[str],
    header: Union[int, Dict[str, int]] = 0,
    process_func: Callable[[pd.DataFrame, str], pd.DataFrame] = None,
    **kwargs
) -> pd.DataFrame:
    """
    读取多个 sheet 并合并结果
    
    Args:
        file_path: Excel 文件路径
        sheet_list: 要读取的 sheet 名称列表
        header: 表头行索引，可以是整数或者 {sheet_name: header_index} 的字典
        process_func: 处理函数，接收 DataFrame 和 sheet_name，返回处理后的 DataFrame
        **kwargs: 传递给 read_excel_to_dataframe 的其他参数
        
    Returns:
        合并后的 DataFrame
    """
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        return pd.DataFrame()
    
    total_df = pd.DataFrame()
    
    for sheet in sheet_list:
        # 确定当前 sheet 的 header
        current_header = header[sheet] if isinstance(header, dict) and sheet in header else header
        
        # 读取当前 sheet
        df = read_excel_to_dataframe(file_path, sheet, header=current_header, **kwargs)
        
        if not df.empty:
            # 应用处理函数
            if process_func:
                df = process_func(df, sheet)
                
            # 合并结果
            total_df = pd.concat([total_df, df], ignore_index=True)
    
    return total_df


def process_directory_files(
    directory_path: str,
    file_pattern: str = "*.xlsx",
    process_func: Callable[[str], pd.DataFrame] = None,
    recursive: bool = False
) -> pd.DataFrame:
    """
    处理目录中的所有匹配文件
    
    Args:
        directory_path: 目录路径
        file_pattern: 文件匹配模式，默认为 "*.xlsx"
        process_func: 处理函数，接收文件路径，返回处理后的 DataFrame
        recursive: 是否递归处理子目录
        
    Returns:
        合并后的 DataFrame
    """
    if not os.path.exists(directory_path):
        print(f"错误: 目录 '{directory_path}' 不存在")
        return pd.DataFrame()
    
    total_df = pd.DataFrame()
    file_count = 0
    
    # 获取所有匹配的文件
    path_obj = Path(directory_path)
    pattern = file_pattern.lstrip("*")  # 移除前导星号
    
    if recursive:
        files = list(path_obj.glob(f"**/*{pattern}"))
    else:
        files = list(path_obj.glob(f"*{pattern}"))
    
    # 处理每个文件
    for file_path in files:
        if file_path.name.startswith("."):
            continue
            
        print(f"处理文件: {file_path.name}")
        
        if process_func:
            df = process_func(str(file_path))
            if not df.empty:
                total_df = pd.concat([total_df, df], ignore_index=True)
                file_count += 1
    
    if file_count == 0:
        print(f"警告: 在目录 '{directory_path}' 中没有找到有效的文件")
    else:
        print(f"成功处理了 {file_count} 个文件")
    
    return total_df


def write_to_excel(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    output_file_path: str,
    sheet_name: str = "Sheet1",
    index: bool = False
) -> bool:
    """
    将数据写入 Excel 文件
    
    Args:
        data: 要写入的数据，可以是 DataFrame 或字典列表
        output_file_path: 输出文件路径
        sheet_name: 要写入的 sheet 名称，默认为 "Sheet1"
        index: 是否写入索引，默认为 False
        
    Returns:
        写入是否成功
    """
    try:
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 如果输入是字典列表，转换为 DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data
        
        # 将 DataFrame 写入 Excel 文件
        df.to_excel(output_file_path, sheet_name=sheet_name, index=index)
        
        print(f"成功将数据写入到 '{output_file_path}'")
        return True
    
    except Exception as e:
        print(f"写入 Excel 文件时发生错误: {str(e)}")
        return False


def write_to_mongodb(
    data: Union[pd.DataFrame, List[Dict[str, Any]]],
    db_name: str,
    collection_name: str,
    connection_string: str = "mongodb://localhost:27017/",
    id_field: str = None,
    upsert: bool = True
) -> bool:
    """
    将数据写入 MongoDB
    
    Args:
        data: 要写入的数据，可以是 DataFrame 或字典列表
        db_name: 数据库名称
        collection_name: 集合名称
        connection_string: MongoDB 连接字符串，默认为 "mongodb://localhost:27017/"
        id_field: 用作唯一标识的字段名，如果为 None 则使用 _id
        upsert: 是否在文档不存在时插入，默认为 True
        
    Returns:
        写入是否成功
    """
    try:
        from pymongo import MongoClient
        
        # 如果输入是 DataFrame，转换为字典列表
        if isinstance(data, pd.DataFrame):
            data_dict_list = data.to_dict(orient='records')
        else:
            data_dict_list = data
        
        # 连接到 MongoDB
        client = MongoClient(connection_string)
        db = client[db_name]
        collection = db[collection_name]
        
        # 写入数据
        for item in data_dict_list:
            if id_field and id_field in item:
                # 使用指定字段作为查询条件
                query = {id_field: item[id_field]}
                collection.update_one(query, {"$set": item}, upsert=upsert)
            else:
                # 直接插入
                collection.insert_one(item)
        
        print(f"成功将 {len(data_dict_list)} 条数据写入到 MongoDB: {db_name}.{collection_name}")
        return True
        
    except Exception as e:
        print(f"写入 MongoDB 时发生错误: {str(e)}")
        return False
