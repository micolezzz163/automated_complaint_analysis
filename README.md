# 客户投诉自动化处理与情感分析系统

该系统基于Robocorp（RPA）、Hugging Face Transformers（AI）和Metabase（数据分析）技术栈，实现了以下主要功能：

## 系统主要功能
1. **邮件处理自动化**：自动获取客户投诉邮件并解析
2. **投诉分类**：使用AI模型或关键词匹配对投诉进行分类
3. **情感分析**：分析客户投诉的情感倾向（正面/负面/中性）
4. **关键信息提取**：提取订单号、产品名称、金额等关键信息
5. **数据存储与管理**：将处理结果保存到数据库
6. **报告生成**：生成投诉分析HTML报告和可视化图表
7. **Metabase集成**：支持将数据导出到Metabase进行高级分析

## 项目结构
- **tasks/**：包含主要任务脚本
  - `process_complaints.py`：处理真实邮件投诉的主任务
  - `test_with_mock_data.py`：使用模拟数据测试系统功能

- **libraries/**：核心功能模块
  - `email_processor.py`：邮件处理模块
  - `sentiment_analyzer.py`：情感分析模块
  - `complaint_classifier.py`：投诉分类模块
  - `database_handler.py`：数据库处理模块
  - `report_generator.py`：报告生成模块

- **resources/**：资源文件
  - `complaint_categories.json`：投诉类别配置
  - `generate_test_data.py`：测试数据生成工具

- **配置文件**：
  - `robot.yaml`：Robocorp任务配置
  - `conda.yaml`：依赖管理
  - `.env`：环境变量配置



## 系统特色
1. **模块化设计**：各功能模块相互独立，便于维护和扩展
2. **AI支持**：使用预训练模型进行情感分析和零样本分类
3. **可视化报告**：自动生成包含图表的HTML报告
4. **数据库支持**：支持SQLite和PostgreSQL数据库
5. **灵活配置**：通过环境变量和配置文件实现灵活配置
6. **测试支持**：提供模拟数据生成工具方便测试

## 技术栈

- **RPA**: Robocorp自动化框架
- **AI**: Hugging Face Transformers用于NLP任务
- **数据分析**: Pandas, Matplotlib
- **数据库**: SQLite/PostgreSQL
- **数据可视化**: Metabase

## 安装与配置

### 环境要求

- Python 3.9+
- Robocorp
- Hugging Face Transformers
- Metabase (可选，用于高级数据分析)

### 安装步骤

1. 克隆仓库：
   ```
   git clone [仓库URL]
   cd automated_complaint_analysis
   ```

2. 安装conda虚拟环境:
   ```
   conda env create -f conda.yaml
   conda activate  robocorp-env
   ```

3. 配置环境变量：
   您需要在`.env`文件中配置以下邮箱信息：
   - `EMAIL_ADDRESS`: 您的邮箱地址
   - `EMAIL_PASSWORD`: 邮箱密码或应用专用密码
   - `IMAP_SERVER`: IMAP服务器地址
   - `IMAP_PORT`: IMAP服务器端口
   - `COMPLAINT_FOLDER`: 投诉邮件所在文件夹



## 运行系统

### 处理真实邮件投诉：
```
python -m robocorp.tasks run tasks/process_complaints.py
```
或使用Robocorp命令：
```
robocorp run -t "Process Complaints"
```

### 使用测试数据运行系统：
```
python -m robocorp.tasks run tasks/test_with_mock_data.py
```
或使用Robocorp命令：
```
robocorp run -t "Run Test With Mock Data"
```

## 查看结果

1. **查看生成报告**：
   - 运行后，打开`output`目录查看自动生成的报告
   - 可查看HTML报告、CSV数据文件和JSON摘要

2. **数据库检查**：
   - 如使用SQLite，可使用SQLite工具查看生成的数据库文件
   - 如使用PostgreSQL，可通过pgAdmin或其他客户端查看数据

3. **Metabase集成**（可选）：
   - 安装并启动Metabase
   - 运行`output/metabase_setup.py`脚本配置数据源和仪表盘
   - 访问配置的Metabase URL（默认http://localhost:3000）查看仪表盘

## 故障排除

- **邮件连接失败**：检查`.env`文件中的邮箱配置是否正确
- **模型下载问题**：首次运行时需要网络连接下载模型，可能需要较长时间，或手动下载模型到`resources/models`目录
- **依赖冲突**：如遇依赖问题，请确保使用更新后的conda.yaml（robocorp-tasks版本为2.2.0）

## 定制与扩展

- 修改`resources/complaint_categories.json`可自定义投诉类别
- 调整`.env`中的`SENTIMENT_MODEL`变量可使用不同的情感分析模型
- 编辑`libraries/report_generator.py`可自定义报告格式和内容



## 目录结构

```
automated_complaint_analysis/
├── tasks/                  # 任务脚本
│   └── process_complaints.py  # 主任务脚本
├── libraries/              # 功能模块
│   ├── email_processor.py     # 邮件处理
│   ├── sentiment_analyzer.py  # 情感分析
│   ├── complaint_classifier.py # 投诉分类
│   ├── database_handler.py    # 数据库处理
│   └── report_generator.py    # 报告生成
├── resources/              # 资源文件
│   ├── models/                # 模型缓存
│   └── complaint_categories.json # 投诉类别配置
├── output/                 # 输出文件
├── robot.yaml              # Robocorp配置
├── conda.yaml              # 依赖配置
├── .env                    # 环境变量
└── README.md               # 项目说明
```


## 贡献

欢迎提交问题报告和改进建议。

# License

This repository is licensed under the [Apache-2.0 License](LICENSE).