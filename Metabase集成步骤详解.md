
## Metabase集成步骤详解

### 1. 安装和启动Metabase

**Docker方式安装（推荐）**：
```bash
docker pull metabase/metabase:latest
docker run -d -p 3000:3000 --name metabase metabase/metabase
```

**或直接下载JAR文件安装**：
```bash
curl -L -o metabase.jar https://downloads.metabase.com/latest/metabase.jar
java -jar metabase.jar
```

### 2. 初始化Metabase

1. 打开浏览器访问 http://localhost:3000
2. 根据向导完成初始设置：
   - 创建管理员账户（与.env文件中的METABASE_USERNAME和METABASE_PASSWORD保持一致）
   - 选择语言（可选中文）
   - 完成基本配置

### 3. 运行setup脚本

首先，需要确认metabase_setup.py脚本是否存在：

```bash
ls -la output/metabase_setup.py
```

如果不存在，需要先生成该脚本：

```bash
conda activate robocorp-env
python -c "from libraries.report_generator import ReportGenerator; ReportGenerator().generate_metabase_scripts()"
```

然后运行setup脚本：

```bash
conda activate robocorp-env
cd output
python metabase_setup.py
```

### 4. 查看仪表盘

1. 脚本执行成功后，会显示访问链接
2. 打开浏览器访问 http://localhost:3000
3. 使用您配置的用户名密码登录
4. 在"仪表盘"部分找到"客户投诉分析仪表盘"

### 注意事项

1. 确保.env文件中的Metabase配置正确：
   ```
   METABASE_URL=http://localhost:3000
   METABASE_USERNAME=admin@example.com
   METABASE_PASSWORD=metabase123
   ```

2. 如果使用SQLite以外的数据库（如PostgreSQL），需要修改metabase_setup.py脚本中的数据源配置。

3. 如需深度定制仪表盘，可以在Metabase界面中手动添加图表和卡片。系统已经在dashboard目录中生成了所需的CSV数据文件。

4. Metabase第一次启动可能需要几分钟来初始化数据库。

通过这些步骤，您可以将投诉分析系统与Metabase集成，获得专业的数据可视化仪表盘。
