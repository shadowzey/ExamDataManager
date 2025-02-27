"""
测试异步Excel处理功能
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.excel import read_excel_to_dict_list_async, write_dict_list_to_excel


async def test_excel_read_write_performance():
    """测试Excel读写性能"""
    # 创建测试数据
    test_data = []
    for i in range(10000):  # 创建一个大数据集来测试性能
        test_data.append({
            "id": i,
            "name": f"Test Name {i}",
            "department": "Test Department",
            "position": "Test Position",
            "salary": 5000 + i % 1000,
            "bonus": 1000 + i % 500,
            "date": "2025-01-01"
        })
    
    print(f"Created {len(test_data)} test data items")
    
    # 创建重复列表和不匹配列表
    repeat_list = [[1, 2]]  # 使用整数索引
    no_match_list = [3, 4]  # 使用整数索引
    
    # 测试异步写入性能
    print("Starting async Excel write test...")
    start_time = time.time()
    excel_data = await write_dict_list_to_excel(test_data, "TestSheet", repeat_list, no_match_list)
    write_time = time.time() - start_time
    print(f"Async write completed, time: {write_time:.2f} seconds")
    
    # 将数据写入临时文件以便测试读取
    temp_file_path = "temp_test_excel.xlsx"
    with open(temp_file_path, "wb") as f:
        f.write(excel_data)
    
    # 测试异步读取性能
    print("Starting async Excel read test...")
    with open(temp_file_path, "rb") as f:
        file_content = f.read()
    
    start_time = time.time()
    read_data = await read_excel_to_dict_list_async(file_content, "TestSheet")
    read_time = time.time() - start_time
    print(f"Async read completed, time: {read_time:.2f} seconds, read {len(read_data)} items")
    
    # 清理临时文件
    os.remove(temp_file_path)
    
    # 验证数据完整性
    assert len(read_data) > 0, "No data was read from the Excel file"
    print("Data integrity check passed!")
    
    return {
        "write_time": write_time,
        "read_time": read_time,
        "data_count": len(test_data)
    }


async def main():
    """主函数"""
    print("Starting Excel async processing performance test...")
    results = await test_excel_read_write_performance()
    print("\nTest results summary:")
    print(f"Data count: {results['data_count']}")
    print(f"Write time: {results['write_time']:.2f} seconds")
    print(f"Read time: {results['read_time']:.2f} seconds")
    print(f"Total time: {results['write_time'] + results['read_time']:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())
