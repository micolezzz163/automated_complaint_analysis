"""
测试任务 - 使用模拟数据而不是真实邮件进行系统测试
"""
from robocorp.tasks import task
import os
import sys
import json
import logging

# 添加库目录到路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "libraries"))

# 导入必要的模块
from sentiment_analyzer import SentimentAnalyzer
from complaint_classifier import ComplaintClassifier
from database_handler import DatabaseHandler
from report_generator import ReportGenerator

# 导入测试数据生成工具
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources"))
from generate_test_data import generate_test_complaints

@task
def process_test_complaints():
    """处理模拟的客户投诉数据以测试系统功能"""
    logging.info("开始使用模拟数据测试系统")
    
    try:
        # 生成模拟投诉数据
        complaint_count = int(os.getenv("TEST_COMPLAINT_COUNT", "10"))
        complaints = generate_test_complaints(complaint_count)
        logging.info(f"已生成 {len(complaints)} 条模拟投诉数据")
        
        # 初始化组件
        sentiment_analyzer = SentimentAnalyzer()
        complaint_classifier = ComplaintClassifier()
        db_handler = DatabaseHandler()
        report_generator = ReportGenerator()
        
        # 处理每条投诉
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
            
            logging.info(f"处理投诉: {complaint['subject']} - 类型: {complaint_type}, 情感: {sentiment_label}")
        
        # 保存数据到数据库
        db_handler.save_complaints(processed_complaints)
        
        # 生成分析报告
        report_file = report_generator.generate(processed_complaints)
        
        # 同时保存处理后的数据为JSON
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        json_path = os.path.join(output_dir, "processed_complaints.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(processed_complaints, f, ensure_ascii=False, indent=2)
        
        logging.info(f"模拟数据处理完成，报告生成于: {report_file}")
        logging.info(f"处理后的数据保存于: {json_path}")
        
    except Exception as e:
        logging.error(f"测试过程中发生错误: {str(e)}")
        raise 