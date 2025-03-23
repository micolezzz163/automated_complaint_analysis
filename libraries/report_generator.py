"""
报告生成器模块 - 负责生成投诉分析报告
"""
import os
import logging
import json
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
from collections import Counter
import base64
from io import BytesIO
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ReportGenerator:
    def __init__(self):
        """初始化报告生成器"""
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        self.dashboard_dir = os.path.join(self.output_dir, "dashboard")
        
        # 设置基本配置
        plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.dashboard_dir, exist_ok=True)
        
        logging.info("报告生成器初始化完成")
    
    def generate(self, complaints_data):
        """
        生成投诉分析报告
        
        Args:
            complaints_data: 投诉数据列表
            
        Returns:
            str: 报告文件路径
        """
        if not complaints_data:
            logging.warning("没有投诉数据，无法生成报告")
            return None
        
        try:
            # 转换为DataFrame方便处理
            df = pd.DataFrame(complaints_data)
            
            # 生成报告文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(self.output_dir, f"complaint_report_{timestamp}.html")
            
            # 生成HTML报告
            html_content = self._generate_html_report(df)
            
            # 保存HTML报告
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 生成JSON摘要
            summary = self._generate_summary(df)
            summary_file = os.path.join(self.output_dir, f"complaint_summary_{timestamp}.json")
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            # 生成Metabase可用的图表数据
            self._generate_dashboard_data(df, timestamp)
            
            logging.info(f"投诉分析报告生成成功: {report_file}")
            return report_file
            
        except Exception as e:
            logging.error(f"生成报告失败: {str(e)}")
            raise
    
    def _generate_summary(self, df):
        """生成数据摘要"""
        # 基本统计
        total_complaints = len(df)
        
        # 投诉类型统计
        type_counts = df['complaint_type'].value_counts().to_dict() if 'complaint_type' in df.columns else {}
        
        # 情感分析统计
        sentiment_counts = df['sentiment_label'].value_counts().to_dict() if 'sentiment_label' in df.columns else {}
        
        # 严重程度统计
        severity_counts = df['severity'].value_counts().to_dict() if 'severity' in df.columns else {}
        
        # 按日期统计
        if 'date' in df.columns:
            df['date_only'] = pd.to_datetime(df['date']).dt.date
            date_counts = df['date_only'].value_counts().to_dict()
            # 将日期转换为字符串以便JSON序列化
            date_counts = {str(k): v for k, v in date_counts.items()}
        else:
            date_counts = {}
        
        return {
            'total_complaints': total_complaints,
            'type_distribution': type_counts,
            'sentiment_distribution': sentiment_counts,
            'severity_distribution': severity_counts,
            'date_distribution': date_counts,
            'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _generate_html_report(self, df):
        """生成HTML格式的报告"""
        # 创建报告标题
        title = f"客户投诉分析报告 - {datetime.now().strftime('%Y-%m-%d')}"
        
        # 生成报告摘要
        summary = self._generate_summary(df)
        
        # 生成图表
        type_chart = self._create_chart(df, 'complaint_type', '投诉类型分布')
        sentiment_chart = self._create_chart(df, 'sentiment_label', '情感分布')
        severity_chart = self._create_chart(df, 'severity', '严重程度分布')
        
        # 生成HTML内容
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #3498db; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .chart-container {{ display: flex; flex-wrap: wrap; justify-content: space-around; }}
                .chart {{ margin: 10px; text-align: center; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            
            <div class="summary">
                <h2>摘要</h2>
                <p>总投诉数量: <strong>{summary['total_complaints']}</strong></p>
                <p>生成时间: {summary['generated_at']}</p>
            </div>
            
            <div class="chart-container">
                <div class="chart">
                    <h2>投诉类型分布</h2>
                    <img src="data:image/png;base64,{type_chart}" alt="投诉类型分布">
                </div>
                <div class="chart">
                    <h2>情感分布</h2>
                    <img src="data:image/png;base64,{sentiment_chart}" alt="情感分布">
                </div>
                <div class="chart">
                    <h2>严重程度分布</h2>
                    <img src="data:image/png;base64,{severity_chart}" alt="严重程度分布">
                </div>
            </div>
            
            <h2>最新投诉列表</h2>
            <table>
                <tr>
                    <th>主题</th>
                    <th>类型</th>
                    <th>情感</th>
                    <th>严重程度</th>
                    <th>日期</th>
                </tr>
        """
        
        # 添加最新10条投诉
        latest_complaints = df.sort_values('date', ascending=False).head(10) if 'date' in df.columns else df.head(10)
        
        for _, row in latest_complaints.iterrows():
            subject = row.get('subject', 'N/A')
            complaint_type = row.get('complaint_type', 'N/A')
            sentiment = row.get('sentiment_label', 'N/A')
            severity = row.get('severity', 'N/A')
            date = row.get('date', 'N/A')
            
            html_content += f"""
                <tr>
                    <td>{subject}</td>
                    <td>{complaint_type}</td>
                    <td>{sentiment}</td>
                    <td>{severity}</td>
                    <td>{date}</td>
                </tr>
            """
            
        html_content += """
            </table>
            
            <h2>建议措施</h2>
            <ul>
                <li>关注高严重度的投诉，优先处理</li>
                <li>针对常见投诉类型制定改进计划</li>
                <li>定期分析投诉情感变化趋势</li>
                <li>对客服团队进行培训，提高处理投诉的能力</li>
            </ul>
            
        </body>
        </html>
        """
        
        return html_content
    
    def _create_chart(self, df, column, title):
        """创建图表并返回Base64编码的图像"""
        plt.figure(figsize=(8, 5))
        
        if column in df.columns:
            # 获取列数据
            data = df[column].value_counts()
            
            # 创建饼图 - 不使用标签，改用图例
            wedges, _, _ = plt.pie(data, labels=None, autopct='%1.1f%%', startangle=90, shadow=True)
            plt.axis('equal')  # 保持饼图为圆形
            
            # 设置标题并添加图例
            plt.title(title)
            plt.legend(wedges, data.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            # 将图表保存到内存
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            
            # 转换为Base64编码
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return image_base64
        else:
            # 没有数据时的处理
            plt.text(0.5, 0.5, f"没有{title}数据", horizontalalignment='center', 
                    verticalalignment='center')
            
            # 将图表保存到内存
            buffer = BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            
            # 转换为Base64编码
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return image_base64
    
    def _generate_dashboard_data(self, df, timestamp):
        """生成Metabase仪表盘所需的数据文件"""
        try:
            # 确保目录存在
            os.makedirs(self.dashboard_dir, exist_ok=True)
            
            # 1. 投诉类型分布数据
            if 'complaint_type' in df.columns:
                type_counts = df['complaint_type'].value_counts().reset_index()
                type_counts.columns = ['complaint_type', 'count']
                type_counts.to_csv(os.path.join(self.dashboard_dir, f'type_distribution_{timestamp}.csv'), index=False, encoding='utf-8-sig')
            
            # 2. 情感分布数据
            if 'sentiment_label' in df.columns:
                sentiment_counts = df['sentiment_label'].value_counts().reset_index()
                sentiment_counts.columns = ['sentiment', 'count']
                sentiment_counts.to_csv(os.path.join(self.dashboard_dir, f'sentiment_distribution_{timestamp}.csv'), index=False, encoding='utf-8-sig')
            
            # 3. 严重程度分布数据
            if 'severity' in df.columns:
                severity_counts = df['severity'].value_counts().reset_index()
                severity_counts.columns = ['severity', 'count']
                severity_counts.to_csv(os.path.join(self.dashboard_dir, f'severity_distribution_{timestamp}.csv'), index=False, encoding='utf-8-sig')
            
            # 4. 时间趋势数据
            if 'date' in df.columns:
                df['date_only'] = pd.to_datetime(df['date']).dt.date
                date_counts = df.groupby('date_only').size().reset_index()
                date_counts.columns = ['date', 'count']
                date_counts.to_csv(os.path.join(self.dashboard_dir, f'time_trend_{timestamp}.csv'), index=False, encoding='utf-8-sig')
            
            # 5. 情感按类型分组数据
            if 'complaint_type' in df.columns and 'sentiment_label' in df.columns:
                type_sentiment = df.groupby(['complaint_type', 'sentiment_label']).size().reset_index()
                type_sentiment.columns = ['complaint_type', 'sentiment', 'count']
                type_sentiment.to_csv(os.path.join(self.dashboard_dir, f'type_sentiment_{timestamp}.csv'), index=False, encoding='utf-8-sig')
            
            logging.info(f"已生成Metabase仪表盘数据文件")
            
        except Exception as e:
            logging.error(f"生成仪表盘数据失败: {str(e)}")
    
    def generate_metabase_scripts(self):
        """生成Metabase API调用示例，用于自动创建仪表盘"""
        script_file = os.path.join(self.output_dir, "metabase_setup.py")
        
        content = """
import requests
import json
import os

# Metabase配置
METABASE_URL = os.getenv("METABASE_URL", "http://localhost:3000")
METABASE_USERNAME = os.getenv("METABASE_USERNAME", "admin@example.com")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD", "metabase123")

# 获取会话令牌
def get_session_token():
    response = requests.post(
        f"{METABASE_URL}/api/session",
        json={"username": METABASE_USERNAME, "password": METABASE_PASSWORD}
    )
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        raise Exception(f"获取会话令牌失败: {response.text}")

# 创建数据源
def create_datasource(session_token, db_path):
    headers = {"X-Metabase-Session": session_token}
    
    # 创建SQLite数据源
    payload = {
        "engine": "sqlite",
        "name": "客户投诉分析",
        "details": {
            "db": db_path
        }
    }
    
    response = requests.post(
        f"{METABASE_URL}/api/database",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        return response.json()["id"]
    else:
        raise Exception(f"创建数据源失败: {response.text}")

# 创建仪表盘
def create_dashboard(session_token, datasource_id):
    headers = {"X-Metabase-Session": session_token}
    
    # 创建仪表盘
    payload = {
        "name": "客户投诉分析仪表盘",
        "description": "展示客户投诉数据分析结果"
    }
    
    response = requests.post(
        f"{METABASE_URL}/api/dashboard",
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        dashboard_id = response.json()["id"]
        
        # 添加卡片到仪表盘
        add_cards_to_dashboard(session_token, dashboard_id, datasource_id)
        
        return dashboard_id
    else:
        raise Exception(f"创建仪表盘失败: {response.text}")

# 添加卡片到仪表盘
def add_cards_to_dashboard(session_token, dashboard_id, datasource_id):
    # 此处可以添加各种图表，如投诉类型分布、情感分析等
    # 需要针对具体需求开发，此处仅为示例
    pass

# 主函数
def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "complaints.db")
    
    try:
        # 获取会话令牌
        session_token = get_session_token()
        print("成功获取会话令牌")
        
        # 创建数据源
        datasource_id = create_datasource(session_token, db_path)
        print(f"成功创建数据源，ID: {datasource_id}")
        
        # 创建仪表盘
        dashboard_id = create_dashboard(session_token, datasource_id)
        print(f"成功创建仪表盘，ID: {dashboard_id}")
        
        print(f"Metabase仪表盘设置完成，请访问 {METABASE_URL}/dashboard/{dashboard_id}")
        
    except Exception as e:
        print(f"设置Metabase失败: {str(e)}")

if __name__ == "__main__":
    main()
        """
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return script_file 