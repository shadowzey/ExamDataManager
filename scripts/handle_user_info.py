"""
用户信息处理模块

此模块用于处理用户信息Excel文件，包括读取、处理和写入功能。
主要功能是处理工作人员信息和费用发放表，并进行信息补充。
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict

import pandas as pd
from pymongo import MongoClient

# 导入通用Excel处理模块
from .excel_utils import (
    read_excel_to_dataframe,
    process_dataframe,
    read_multiple_sheets,
    write_to_excel,
    write_to_mongodb
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
    "姓名": "name",
    "收款账号身份证号": "id_card",
    "收款账号身份证号码": "id_card",
    "收款账号": "bank_card",
    "收款账号开户行": "bank_name",
    "电话号码": "phone",
    "手机号码": "phone",
    "备注": "remark",
    "身份证号": "id_card",
    "身份证": "id_card",
    "银行卡号": "bank_card",
    "发放明细": "detail",
    "次数（小时）": "count_hour",
    "标准": "standard",
    "其他项目": "other_project",
    "电话": "phone",
    "开户行": "bank_name",
    "工资编号": "salary_id",
    "工资编码": "salary_id",
    "分院": "department"
}


def handle_user_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    处理用户数据，过滤空姓名并保留有效列
    
    Args:
        df: 输入的DataFrame
        
    Returns:
        处理后的DataFrame
    """
    # 过滤掉姓名为空的行
    df = df[df['姓名'].notna() & (df['姓名'] != '')]
    
    # 和COLUMNS取交集，只保留有效列
    valid_columns = set(COLUMNS).intersection(df.columns)
    if valid_columns:
        df = df[list(valid_columns)]
    
    return df


def read_worker_info(
    file_path: str, 
    sheet_lists: List[str], 
    type: str = "教师"
) -> List[Dict[str, Any]]:
    """
    读取工作人员信息
    
    Args:
        file_path: Excel文件路径
        sheet_lists: 要读取的sheet名称列表
        type: 人员类型，默认为"教师"
        
    Returns:
        工作人员信息字典列表
    """
    # 为不同sheet准备不同的header设置
    headers = {}
    type_mapping = {}
    
    for sheet in sheet_lists:
        headers[sheet] = 0  # 默认header为0
        type_mapping[sheet] = type  # 默认类型
        
        # 特殊情况处理
        if sheet == '物业人员信息':
            headers[sheet] = 1
            type_mapping[sheet] = "物业人员"
    
    def process_sheet(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """处理单个sheet的数据"""
        # 基本数据处理
        df = handle_user_data(df)
        
        # 应用列名映射
        df = process_dataframe(
            df,
            column_mapping=COLUMNS_MAPPING,
            extend_data={'type': type_mapping.get(sheet_name, type)}
        )
        
        return df
    
    # 读取所有sheet并处理
    df = read_multiple_sheets(
        file_path,
        sheet_lists,
        header=headers,
        process_func=process_sheet
    )
    
    # 转换为字典列表
    return df.to_dict(orient='records') if not df.empty else []


def read_fee_info(
    file_path: str, 
    sheet_lists: List[str]
) -> List[Dict[str, Any]]:
    """
    读取费用发放表信息
    
    Args:
        file_path: Excel文件路径
        sheet_lists: 要读取的sheet名称列表
        
    Returns:
        费用信息字典列表
    """
    def process_sheet(df: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
        """处理单个sheet的费用数据"""
        # 基本数据处理
        df = handle_user_data(df)
        
        # 应用列名映射
        df = process_dataframe(
            df,
            column_mapping=COLUMNS_MAPPING
        )
        
        return df
    
    # 读取所有sheet并处理
    df = read_multiple_sheets(
        file_path,
        sheet_lists,
        process_func=process_sheet
    )
    
    # 转换为字典列表
    return df.to_dict(orient='records') if not df.empty else []


def supplement_fee_info(
    fee_info: List[Dict[str, Any]], 
    worker_info: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    通过搜索工作人员信息表补充费用发放表信息
    
    Args:
        fee_info: 费用信息列表
        worker_info: 工作人员信息列表
        
    Returns:
        补充后的费用信息列表
    """
    # 创建工作人员信息的姓名索引，提高查询效率
    worker_by_name = {}
    for worker in worker_info:
        if 'name' in worker:
            worker_by_name[worker['name']] = worker
    
    # 补充费用信息
    for fee in fee_info:
        if 'name' in fee and fee['name'] in worker_by_name:
            worker = worker_by_name[fee['name']]
            
            # 补充缺失的信息
            fee['id_card'] = fee.get('id_card') or worker.get('id_card')
            fee['bank_card'] = fee.get('bank_card') or worker.get('bank_card')
            fee['phone'] = fee.get('phone') or worker.get('phone')
            fee['bank_name'] = fee.get('bank_name') or worker.get('bank_name')
    
    return fee_info


def merge_user_phone(
    user_file_path: str, 
    phone_file_path: str
) -> List[Dict[str, Any]]:
    """
    合并用户信息和电话信息
    
    Args:
        user_file_path: 用户信息文件路径
        phone_file_path: 电话信息文件路径
        
    Returns:
        合并后的用户信息列表
    """
    # 读取用户信息和电话信息
    user_info = read_worker_info(user_file_path, sheet_lists=['Sheet1'])
    user_phone = read_worker_info(phone_file_path, sheet_lists=['Sheet1'])
    
    # 创建电话信息的工号索引
    phone_by_id = {}
    for phone in user_phone:
        if 'salary_id' in phone:
            phone_by_id[phone['salary_id']] = phone
    
    # 合并信息
    for user in user_info:
        if 'salary_id' in user and user['salary_id'] in phone_by_id:
            user['phone'] = phone_by_id[user['salary_id']].get('phone')
    
    return user_info


def find_repeat_name(
    user_info: List[Dict[str, Any]], 
    db_name: str = "myDatabase", 
    collection_name: str = "employee_collection",
    connection_string: str = "mongodb://10.10.10.10:27017/"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    查找重复姓名并更新到MongoDB
    
    Args:
        user_info: 用户信息列表
        db_name: 数据库名称
        collection_name: 集合名称
        connection_string: MongoDB连接字符串
        
    Returns:
        重复姓名及其对应的记录字典
    """
    # 连接到MongoDB
    client = MongoClient(connection_string)
    db = client[db_name]
    collection = db[collection_name]
    
    # 按姓名分组
    grouped_data = defaultdict(list)
    for item in user_info:
        if 'name' in item:
            grouped_data[item['name']].append(item)
    
    # 找出重复的姓名
    duplicates = {name: items for name, items in grouped_data.items() if len(items) > 1}
    
    # 更新到MongoDB
    for name, items in duplicates.items():
        print(f"姓名 '{name}' 出现多次:")
        for item in items:
            if 'id_card' in item:
                collection.update_one(
                    {"id_card": item["id_card"]}, 
                    {"$set": item}, 
                    upsert=True
                )
    
    return duplicates


def main():
    """
    主函数，演示如何使用模块功能
    """
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 示例：读取工作人员信息
    worker_file = os.path.join(script_dir, "11月14日学生.xlsx")
    kaoshi_file = os.path.join(script_dir, "周六监考信息表.xlsx")
    
    if os.path.exists(worker_file) and os.path.exists(kaoshi_file):
        # 读取工作人员信息
        worker_info = read_worker_info(worker_file, sheet_lists=["Sheet1"], type="学生")
        kaoshi_info = read_worker_info(kaoshi_file, sheet_lists=["Sheet1"], type="学生")
        
        # 合并信息
        worker_info.extend(kaoshi_info)
        
        # 写入MongoDB
        write_to_mongodb(
            worker_info, 
            db_name="myDatabase", 
            collection_name="employee_collection",
            connection_string="mongodb://10.10.10.10:27017/",
            id_field="id_card"
        )
        
        print(f"成功处理了 {len(worker_info)} 条用户记录")
    else:
        print("示例文件不存在，请检查文件路径")


if __name__ == '__main__':
    main()