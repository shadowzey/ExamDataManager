# ExamDataManager

ExamDataManager 是一个综合性的考试数据管理工具，用于处理用户信息、考场信息和费用数据。该工具提供了一套强大的 Excel 处理功能，帮助教育机构高效管理考试相关数据。

## 功能特点

- Excel文件处理与分析
- 员工信息管理（CRUD操作）
- 异步处理大文件
- AI计算考务费用

## 技术栈

- **后端框架**: FastAPI
- **数据库**: MongoDB (通过Motor进行异步操作)
- **依赖管理**: PDM
- **容器化**: Docker
- **Excel处理**: Pandas, OpenPyXL

## 项目结构

```
ExamDataManager/
├── app/                      # 应用主目录
│   ├── api/                  # API路由
│   │   ├── endpoints/        # API端点
│   │   │   ├── excel.py      # Excel处理相关端点
│   │   │   └── employees.py  # 员工管理相关端点
│   │   └── api.py            # API路由注册
│   ├── core/                 # 核心模块
│   │   ├── config.py         # 应用配置
│   │   ├── exceptions.py     # 自定义异常
│   │   └── exception_handlers.py # 异常处理器
│   ├── db/                   # 数据库相关
│   │   ├── deps.py           # 依赖注入
│   │   └── mongodb.py        # MongoDB连接管理
│   ├── models/               # 数据模型
│   ├── services/             # 业务逻辑服务
│   │   ├── employee_service.py # 员工服务
│   │   └── fee_service.py    # 费用计算服务
│   ├── utils/                # 工具函数
│   │   └── excel.py          # Excel处理工具
│   └── main.py               # FastAPI应用实例
├── main.py                   # 应用入口点
├── pyproject.toml            # PDM项目配置
├── Dockerfile                # Docker配置
└── README.md                 # 项目说明
```

## 安装与运行

### 使用PDM（推荐）

1. 安装PDM (如果尚未安装)
   ```bash
   pip install pdm
   ```

2. 安装依赖
   ```bash
   pdm install
   ```

3. 运行应用
   ```bash
   pdm run python main.py
   ```

### 使用Docker

1. 构建Docker镜像
   ```bash
   docker build -t excel-app .
   ```

2. 运行容器
   ```bash
   docker run -p 8000:8000 excel-app
   ```

## API文档

启动应用后，访问 http://localhost:8000/docs 查看Swagger API文档。

## 主要API端点

- `POST /api/excel/upload/{sheet_name}`: 上传并处理Excel文件
- `GET /api/employees/{employee_id}`: 获取单个员工信息
- `GET /api/employees/name/{name}`: 按姓名搜索员工
- `POST /api/employees`: 创建新员工
- `PUT /api/employees/{employee_id}`: 更新员工信息
- `DELETE /api/employees/{employee_id}`: 删除员工

## 异步处理

本应用使用异步处理来处理大型Excel文件，避免阻塞主事件循环。进度跟踪功能允许客户端监控长时间运行的操作的状态。

## AI计算考务费用

本应用集成了DeepSeek计算考务费用的服务，实现了自动计算考务费用的功能，提高了处理效率。


