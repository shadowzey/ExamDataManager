"""
测试 API 端点功能
"""
import asyncio
import os
import sys
import time
import httpx
import pandas as pd
from pathlib import Path
from io import BytesIO
import socket

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))


def is_mongodb_running(host='localhost', port=27017, timeout=1):
    """检查MongoDB服务是否运行"""
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return True
    except socket.error:
        return False


def test_excel_file_creation():
    """测试Excel文件创建功能（不依赖于API服务）"""
    print("\n测试Excel文件创建...")
    
    # 创建测试Excel文件
    df = pd.DataFrame({
        '姓名': [f'测试姓名 {i}' for i in range(10)],
        '身份证号': [f'1234567890{i:02d}' for i in range(10)],
        '电话': [f'1380000{i:04d}' for i in range(10)],
        '银行卡号': [f'6225880000{i:06d}' for i in range(10)],
        '开户行': ['测试银行'] * 10,
        '分院': ['测试学院'] * 10,
        '次数（小时）': [8] * 10,  # 工作小时数
        '标准': [100] * 10,  # 每小时费用标准
        '金额': [800] * 10,  # 初始金额
        '备注': ['测试备注'] * 10
    })
    
    # 将DataFrame保存为Excel文件
    test_file_path = "test_output.xlsx"
    df.to_excel(test_file_path, sheet_name='TestSheet', index=False)
    
    # 验证文件是否创建成功
    if os.path.exists(test_file_path):
        file_size = os.path.getsize(test_file_path)
        print(f"Excel文件创建成功: {test_file_path}, 大小: {file_size} 字节")
        
        # 读取并验证文件内容
        df_read = pd.read_excel(test_file_path)
        if len(df_read) == 10:
            print(f"Excel文件内容验证成功，包含 {len(df_read)} 行数据")
        else:
            print(f"Excel文件内容验证失败，期望 10 行，实际 {len(df_read)} 行")
            
        # 清理测试文件
        os.remove(test_file_path)
        print(f"测试文件已清理: {test_file_path}")
    else:
        print(f"Excel文件创建失败: {test_file_path}")


async def test_excel_upload_endpoint():
    """测试Excel上传端点"""
    # 检查MongoDB是否运行
    if not is_mongodb_running():
        print("\nMongoDB服务未运行，跳过API测试")
        return
        
    # 检查API服务是否运行
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get('http://localhost:8000/health', timeout=2.0)
            if response.status_code != 200:
                print("\nAPI服务未正常运行，跳过API测试")
                return
    except Exception:
        print("\nAPI服务未运行，跳过API测试")
        return
        
    print("\n开始测试API端点...")
    
    # 创建测试Excel文件
    df = pd.DataFrame({
        '姓名': [f'测试姓名 {i}' for i in range(100)],
        '身份证号': [f'1234567890{i:02d}' for i in range(100)],
        '电话': [f'1380000{i:04d}' for i in range(100)],
        '银行卡号': [f'6225880000{i:06d}' for i in range(100)],
        '开户行': ['测试银行'] * 100,
        '分院': ['测试学院'] * 100,
        '次数（小时）': [8] * 100,  # 工作小时数
        '标准': [100] * 100,  # 每小时费用标准
        '金额': [None] * 100,  # 初始金额为空，由系统计算
        '备注': ['测试备注'] * 100
    })
    
    # 将DataFrame保存为Excel文件
    excel_file = BytesIO()
    df.to_excel(excel_file, sheet_name='TestSheet', index=False)
    excel_file.seek(0)
    
    # 设置API基础URL
    base_url = 'http://localhost:8000'
    
    # 测试同步上传端点
    print("\n测试同步上传端点...")
    try:
        async with httpx.AsyncClient() as client:
            files = {'file': ('test.xlsx', excel_file.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            start_time = time.time()
            response = await client.post(
                f'{base_url}/api/excel/upload/TestSheet',
                files=files,
                timeout=30.0
            )
            
            if response.status_code == 200:
                print(f"同步上传成功，耗时: {time.time() - start_time:.2f} 秒")
                # 保存返回的Excel文件
                with open('test_sync_result.xlsx', 'wb') as f:
                    f.write(response.content)
                print("结果已保存到 test_sync_result.xlsx")
            else:
                print(f"同步上传失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"测试同步上传端点时出错: {e}")
    
    # 重置Excel文件指针
    excel_file.seek(0)
    
    # 测试异步上传端点
    print("\n测试异步上传端点...")
    try:
        async with httpx.AsyncClient() as client:
            files = {'file': ('test.xlsx', excel_file.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            start_time = time.time()
            response = await client.post(
                f'{base_url}/api/excel/upload-async/TestSheet',
                files=files
            )
            
            if response.status_code == 200:
                result = response.json()
                task_id = result['data']['task_id']
                print(f"异步上传成功，任务ID: {task_id}")
                
                # 轮询任务进度
                completed = False
                while not completed and time.time() - start_time < 60:  # 最多等待60秒
                    await asyncio.sleep(1)
                    progress_response = await client.get(f'{base_url}/api/excel/task/{task_id}')
                    
                    if progress_response.status_code == 200:
                        progress_data = progress_response.json()['data']
                        print(f"任务状态: {progress_data['status']}, 进度: {progress_data['progress']}%")
                        
                        if progress_data['status'] == 'completed':
                            completed = True
                            # 下载处理后的文件
                            download_response = await client.get(f'{base_url}/api/excel/download/{task_id}')
                            
                            if download_response.status_code == 200:
                                with open('test_async_result.xlsx', 'wb') as f:
                                    f.write(download_response.content)
                                print("结果已保存到 test_async_result.xlsx")
                                print(f"总耗时: {time.time() - start_time:.2f} 秒")
                            else:
                                print(f"下载文件失败，状态码: {download_response.status_code}")
                        elif progress_data['status'] == 'error':
                            print(f"任务出错: {progress_data.get('error', '未知错误')}")
                            completed = True
                
                if not completed:
                    print("任务超时，未能在60秒内完成")
            else:
                print(f"异步上传失败，状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"测试异步上传端点时出错: {e}")


async def main():
    """主函数"""
    print("开始测试...")
    
    # 运行不依赖于API服务的测试
    test_excel_file_creation()
    
    # 运行依赖于API服务的测试
    await test_excel_upload_endpoint()
    
    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
