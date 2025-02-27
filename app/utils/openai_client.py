"""
OpenAI 客户端工具模块
"""
import math
import os
from typing import List, Dict, Any, Union, Tuple
from openai import OpenAI
from app.core.config import settings


# 创建 OpenAI 客户端
client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

# 获取提示词
prompt = settings.OPENAI_PROMPT


def get_fees_batch(data_list: List[Dict[str, Any]]) -> List[float]:
    """
    批量获取金额计算结果
    
    将相同条件的计算进行批处理，提高效率
    
    Args:
        data_list: 包含费用信息的字典列表
        
    Returns:
        计算后的金额列表
    """
    # 过滤掉已有金额的数据
    to_calculate = []
    original_fees = []
    positions = []  # 记录需要计算的位置
    
    # 用于存储已计算过的条件和结果
    calculated_cache = {}
    
    for i, data in enumerate(data_list):
        fee = data.get('金额')
        if str(fee).replace(" ", "") != "" and not math.isnan(fee):
            original_fees.append(float(fee))
        else:
            # 确保数据中包含必要的字段
            if "次数（小时）" not in data or "标准" not in data:
                original_fees.append(math.nan)
                continue
                
            cal_data = [data["次数（小时）"], data["标准"]]
            # 将列表转换为元组以便用作字典键
            cal_key = (str(cal_data[0]), str(cal_data[1]))
            to_calculate.append((cal_key, cal_data))
            original_fees.append(None)
            positions.append(i)
    
    if not to_calculate:
        return original_fees
    
    # 将数据按40个一组进行分批，但先去重
    unique_calculations = []
    key_to_original = {}  # 记录原始数据的映射
    
    for cal_key, cal_data in to_calculate:
        if cal_key not in key_to_original:
            key_to_original[cal_key] = cal_data
            unique_calculations.append(cal_data)
    
    # 批量处理去重后的数据
    batch_size = 30
    unique_results = {}  # 存储唯一条件的计算结果
    
    for i in range(0, len(unique_calculations), batch_size):
        batch = unique_calculations[i:i + batch_size]
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(batch)}
        ]
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                stream=False
            )
            
            result_str = response.choices[0].message.content.strip()
            # 安全地解析响应结果
            try:
                batch_results = eval(result_str)
                if not isinstance(batch_results, list):
                    batch_results = [math.nan] * len(batch)
            except Exception as e:
                print(f"解析批量结果出错: {e}, 原始响应: {result_str}")
                batch_results = [math.nan] * len(batch)
            
            if len(batch_results) != len(batch):
                print(f"批量计算结果数量不匹配: 期望 {len(batch)}, 实际 {len(batch_results)}")
                batch_results = [math.nan] * len(batch)
            
            # 将结果与条件对应存储
            for cal_data, result in zip(batch, batch_results):
                cal_key = (str(cal_data[0]), str(cal_data[1]))
                unique_results[cal_key] = result
            
        except Exception as e:
            print(f"批量计算出错: {e}")
            for cal_data in batch:
                cal_key = (str(cal_data[0]), str(cal_data[1]))
                unique_results[cal_key] = math.nan
    
    # 使用缓存的结果更新最终结果
    result = original_fees.copy()
    for pos, (cal_key, _) in zip(positions, to_calculate):
        result[pos] = unique_results.get(cal_key, math.nan)
    
    return result


def get_fee_from_openai(data: Dict[str, Any]) -> float:
    """
    从 OpenAI 获取单个费用计算结果
    
    Args:
        data: 包含费用信息的字典
        
    Returns:
        计算后的金额
    """
    fee = data.get('金额')
    if str(fee).replace(" ", "") != "" and not math.isnan(fee):
        return fee
        
    # 确保数据中包含必要的字段
    if "次数（小时）" not in data or "标准" not in data:
        return math.nan
        
    cal_data = [data["次数（小时）"], data["标准"]]
    return get_answer_from_openai(cal_data)


def get_answer_from_openai(data: List[str]) -> float:
    """
    从 OpenAI 获取答案
    
    Args:
        data: 包含计算所需数据的列表
        
    Returns:
        计算后的金额
    """
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": str(data)},
            ],
            stream=False
        )

        result_str = response.choices[0].message.content.strip()
        try:
            return float(result_str)
        except (ValueError, AttributeError) as e:
            print(f"解析单个结果出错: {e}, 原始响应: {result_str}")
            return math.nan
    except Exception as e:
        print(f"调用 OpenAI API 出错: {e}")
        return math.nan
