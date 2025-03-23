"""
客户投诉处理与情感分析任务
"""
from robocorp.tasks import task
from robocorp import workitems
import os
import sys
import logging

# 添加库目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "libraries"))

from email_processor import EmailProcessor
from sentiment_analyzer import SentimentAnalyzer
from complaint_classifier import ComplaintClassifier
from database_handler import DatabaseHandler
from report_generator import ReportGenerator

@task
def process_complaints():
    """处理客户投诉邮件并生成分析报告"""
    logging.info("开始处理客户投诉")
    
    try:
        # 初始化组件
        email_processor = EmailProcessor()
        sentiment_analyzer = SentimentAnalyzer()
        complaint_classifier = ComplaintClassifier()
        db_handler = DatabaseHandler()
        report_generator = ReportGenerator()
        
        # 1. 从邮箱获取投诉邮件
        complaints = email_processor.fetch_emails()
        logging.info(f"成功获取{len(complaints)}封投诉邮件")
        
        # 2. 处理每封投诉邮件
        processed_complaints = []
        for complaint in complaints:
            # 分类投诉类型
            complaint_type = complaint_classifier.classify(complaint['content'])
            
            # 情感分析
            sentiment_score, sentiment_label = sentiment_analyzer.analyze(complaint['content'])
            
            # 提取关键信息（订单号、产品名等）
            extracted_info = complaint_classifier.extract_key_info(complaint['content'])
            
            # 合并处理结果
            processed_complaint = {
                **complaint,
                'complaint_type': complaint_type,
                'sentiment_score': sentiment_score,
                'sentiment_label': sentiment_label,
                **extracted_info
            }
            
            processed_complaints.append(processed_complaint)
        
        # 3. 保存数据到数据库
        db_handler.save_complaints(processed_complaints)
        
        # 4. 生成分析报告
        report_generator.generate(processed_complaints)
        
        logging.info("客户投诉处理完成")
        
    except Exception as e:
        logging.error(f"处理过程中发生错误: {str(e)}")
        raise 