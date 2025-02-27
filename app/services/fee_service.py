"""
费用服务模块
"""
import math
import logging
from typing import Dict, List, Any, Tuple, Optional
from motor.motor_asyncio import AsyncIOMotorCollection
from app.utils.openai_client import get_fees_batch
from app.core.exceptions import BadRequestException, InternalServerException

# 配置日志
logger = logging.getLogger(__name__)


def _full_fee(fee_info: Dict[str, Any], user_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    补充费用信息
    
    Args:
        fee_info: 费用信息
        user_info: 用户信息
        
    Returns:
        补充后的费用信息
    """
    fee = {**fee_info}
    fee['身份证号'] = user_info.get('id_card')
    fee['银行卡号'] = user_info.get('bank_card')
    fee['电话'] = user_info.get('phone')
    fee['开户行'] = user_info.get('bank_name')
    fee['姓名'] = user_info.get('name') if user_info.get('name') else fee['姓名']
    return fee


async def supplement_fee_info(
    collection: AsyncIOMotorCollection, 
    fee_info: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[List[int]], List[int]]:
    """
    通过搜索工作人员信息表补充费用发放表信息
    
    Args:
        collection: 员工集合
        fee_info: 费用信息列表
        
    Returns:
        补充后的费用信息列表，重复项索引列表，未匹配项索引列表
    """
    if not fee_info:
        logger.warning("输入的费用信息为空")
        return [], [], []
    
    # 检查集合是否为None
    if collection is None:
        logger.error("MongoDB集合对象为None，可能是数据库连接失败")
        # 返回原始数据，不进行补充
        return fee_info, [], []
    
    fee_result = []
    repeat_list = []
    no_match_list = []
    index = 1
    
    # 验证输入数据
    valid_fee_info = []
    invalid_count = 0
    for fee in fee_info:
        if '姓名' not in fee or not fee['姓名']:
            invalid_count += 1
            continue
        valid_fee_info.append(fee)
    
    if invalid_count > 0:
        logger.warning(f"有 {invalid_count} 条费用记录缺少姓名字段，已跳过")
    
    if not valid_fee_info:
        logger.error("没有有效的费用信息记录")
        raise BadRequestException("所有费用记录均缺少姓名字段")
    
    # 按姓名批量查询用户信息
    names = [fee['姓名'] for fee in valid_fee_info]
    users_dict = {}
    try:
        async for user in collection.find({"name": {"$in": names}}):
            name = user['name']
            if name not in users_dict:
                users_dict[name] = []
            users_dict[name].append(user)
    except Exception as e:
        error_msg = f"查询用户信息出错: {str(e)}"
        logger.error(error_msg)
        raise InternalServerException(error_msg)
    
    temp_fees = []
    indices_map = []  # 记录每个费用在最终结果中的位置
    
    for i, fee in enumerate(valid_fee_info):
        try:
            name = str(fee['姓名']).replace(" ", "")
            users = users_dict.get(name, [])
            
            if len(users) > 1:
                repeat_index = []
                for user in users:
                    fee_copy = _full_fee(fee.copy(), user)
                    temp_fees.append(fee_copy)
                    index += 1
                    repeat_index.append(index)
                    indices_map.append(len(fee_result))
                    fee_result.append(fee_copy)
                repeat_list.append(repeat_index)
                logger.info(f"姓名 '{name}' 匹配到多个员工记录")
            elif len(users) == 1:
                fee_copy = _full_fee(fee.copy(), users[0])
                temp_fees.append(fee_copy)
                index += 1
                indices_map.append(len(fee_result))
                fee_result.append(fee_copy)
            else:
                fee_copy = _full_fee(fee.copy(), {})
                temp_fees.append(fee_copy)
                index += 1
                indices_map.append(len(fee_result))
                fee_result.append(fee_copy)
                no_match_list.append(index)
                logger.warning(f"姓名 '{name}' 未匹配到员工记录")
        except Exception as e:
            error_msg = f"处理费用信息出错: {str(e)}, 费用信息: {fee}"
            logger.error(error_msg)
            # 继续处理下一条记录，不中断整个流程
            continue
    
    if not temp_fees:
        logger.error("处理后没有有效的费用信息")
        return [], [], []
    
    # 批量计算金额
    try:
        calculated_fees = get_fees_batch(temp_fees)
        
        # 更新金额
        updated_count = 0
        for i, fee in enumerate(calculated_fees):
            if fee is not None and not math.isnan(fee):
                fee_result[indices_map[i]]['金额'] = fee
                updated_count += 1
        
        logger.info(f"成功计算 {updated_count}/{len(temp_fees)} 条费用记录的金额")
    except Exception as e:
        error_msg = f"计算金额出错: {str(e)}"
        logger.error(error_msg)
        # 不抛出异常，返回已处理的结果
    
    return fee_result, repeat_list, no_match_list
