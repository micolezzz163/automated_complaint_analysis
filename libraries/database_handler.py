"""
数据库处理模块 - 负责保存投诉数据并支持分析查询
"""
import os
import logging
import json
from datetime import datetime
import pandas as pd
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 定义ORM基类
Base = declarative_base()

class Complaint(Base):
    """投诉数据表模型"""
    __tablename__ = 'complaints'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String(50), unique=True, index=True)
    sender = Column(String(100))
    subject = Column(String(200))
    content = Column(Text)
    date_received = Column(DateTime)
    order_number = Column(String(20), index=True)
    complaint_type = Column(String(50), index=True)
    sentiment_score = Column(Float)
    sentiment_label = Column(String(20))
    product_name = Column(String(100))
    amount = Column(Float)
    incident_date = Column(String(20))
    severity = Column(String(10))
    processed_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, type={self.complaint_type})>"

class DatabaseHandler:
    def __init__(self):
        """初始化数据库处理器"""
        self.db_type = os.getenv("DB_TYPE", "sqlite").lower()
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化数据库连接
        self._initialize_db()
        
        logging.info(f"数据库处理器初始化完成，使用 {self.db_type} 数据库")
    
    def _initialize_db(self):
        """初始化数据库连接"""
        if self.db_type == "sqlite":
            db_path = os.path.join(self.output_dir, "complaints.db")
            self.engine = create_engine(f"sqlite:///{db_path}")
        elif self.db_type == "postgresql":
            # 从环境变量获取PostgreSQL连接信息
            pg_host = os.getenv("PG_HOST", "localhost")
            pg_port = os.getenv("PG_PORT", "5432")
            pg_user = os.getenv("PG_USER", "postgres")
            pg_pass = os.getenv("PG_PASS", "postgres")
            pg_db = os.getenv("PG_DB", "complaints")
            
            self.engine = create_engine(
                f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
            )
        else:
            # 默认使用SQLite
            db_path = os.path.join(self.output_dir, "complaints.db")
            self.engine = create_engine(f"sqlite:///{db_path}")
        
        # 创建表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.Session = sessionmaker(bind=self.engine)
    
    def save_complaints(self, complaints_data):
        """
        保存投诉数据到数据库
        
        Args:
            complaints_data: 包含投诉信息的字典列表
        
        Returns:
            int: 成功保存的投诉数量
        """
        if not complaints_data:
            logging.warning("没有投诉数据需要保存")
            return 0
        
        session = self.Session()
        saved_count = 0
        
        try:
            for complaint_data in complaints_data:
                # 检查邮件ID是否已存在
                if session.query(Complaint).filter_by(email_id=complaint_data['id']).first():
                    logging.info(f"投诉邮件 {complaint_data['id']} 已存在，跳过")
                    continue
                
                # 解析日期
                try:
                    date_received = datetime.strptime(complaint_data['date'], "%Y-%m-%d %H:%M:%S")
                except:
                    date_received = datetime.now()
                
                # 创建投诉对象
                complaint = Complaint(
                    email_id=complaint_data['id'],
                    sender=complaint_data['sender'],
                    subject=complaint_data['subject'],
                    content=complaint_data['content'],
                    date_received=date_received,
                    order_number=complaint_data.get('order_number'),
                    complaint_type=complaint_data.get('complaint_type', '未分类'),
                    sentiment_score=complaint_data.get('sentiment_score', 0.0),
                    sentiment_label=complaint_data.get('sentiment_label', '中性'),
                    product_name=complaint_data.get('product_name'),
                    amount=complaint_data.get('amount'),
                    incident_date=complaint_data.get('incident_date'),
                    severity=complaint_data.get('severity', '中'),
                    processed_at=datetime.now()
                )
                
                session.add(complaint)
                saved_count += 1
            
            # 提交事务
            session.commit()
            logging.info(f"成功保存 {saved_count} 条投诉记录")
            
            # 同时保存为CSV备份
            self._export_to_csv()
            
            return saved_count
            
        except Exception as e:
            session.rollback()
            logging.error(f"保存投诉数据失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def get_complaints_by_type(self, complaint_type=None, days=30):
        """
        按类型获取投诉数据
        
        Args:
            complaint_type: 投诉类型，为None时获取所有类型
            days: 获取最近几天的数据，默认30天
            
        Returns:
            list: 投诉数据列表
        """
        session = self.Session()
        try:
            query = session.query(Complaint)
            
            # 筛选类型
            if complaint_type:
                query = query.filter(Complaint.complaint_type == complaint_type)
            
            # 筛选时间
            if days:
                cutoff_date = datetime.now().date()
                query = query.filter(Complaint.date_received >= cutoff_date)
            
            # 执行查询
            complaints = query.all()
            
            # 转换为字典列表
            result = []
            for complaint in complaints:
                result.append({
                    'id': complaint.id,
                    'email_id': complaint.email_id,
                    'sender': complaint.sender,
                    'subject': complaint.subject,
                    'date_received': complaint.date_received.strftime("%Y-%m-%d %H:%M:%S") if complaint.date_received else None,
                    'complaint_type': complaint.complaint_type,
                    'sentiment_score': complaint.sentiment_score,
                    'sentiment_label': complaint.sentiment_label,
                    'severity': complaint.severity,
                    'order_number': complaint.order_number,
                    'product_name': complaint.product_name
                })
            
            return result
            
        finally:
            session.close()
    
    def get_summary_stats(self):
        """
        获取投诉数据的摘要统计信息
        
        Returns:
            dict: 包含统计信息的字典
        """
        session = self.Session()
        try:
            # 获取总投诉数
            total_count = session.query(Complaint).count()
            
            # 获取各类型投诉数量
            type_counts = {}
            types = session.query(Complaint.complaint_type).distinct().all()
            for complaint_type in types:
                count = session.query(Complaint).filter(Complaint.complaint_type == complaint_type[0]).count()
                type_counts[complaint_type[0]] = count
            
            # 获取情感分布
            sentiment_counts = {
                '正面': session.query(Complaint).filter(Complaint.sentiment_label == '正面').count(),
                '负面': session.query(Complaint).filter(Complaint.sentiment_label == '负面').count(),
                '中性': session.query(Complaint).filter(Complaint.sentiment_label == '中性').count()
            }
            
            # 按严重程度统计
            severity_counts = {
                '高': session.query(Complaint).filter(Complaint.severity == '高').count(),
                '中': session.query(Complaint).filter(Complaint.severity == '中').count(),
                '低': session.query(Complaint).filter(Complaint.severity == '低').count()
            }
            
            return {
                'total_count': total_count,
                'type_counts': type_counts,
                'sentiment_counts': sentiment_counts,
                'severity_counts': severity_counts
            }
            
        finally:
            session.close()
    
    def _export_to_csv(self):
        """将数据库中的投诉导出为CSV文件"""
        try:
            # 使用原生SQLite导出数据
            if self.db_type == "sqlite":
                # 创建SQL连接
                db_path = os.path.join(self.output_dir, "complaints.db")
                conn = sqlite3.connect(db_path)
                
                # 读取数据
                df = pd.read_sql("SELECT * FROM complaints", conn)
                
                # 关闭连接
                conn.close()
            else:
                # 对于PostgreSQL尝试从会话获取数据
                session = self.Session()
                complaints = session.query(Complaint).all()
                session.close()
                
                # 转换为DataFrame
                data = []
                for c in complaints:
                    data.append({
                        'id': c.id,
                        'email_id': c.email_id,
                        'sender': c.sender,
                        'subject': c.subject,
                        'content': c.content,
                        'date_received': c.date_received,
                        'order_number': c.order_number,
                        'complaint_type': c.complaint_type,
                        'sentiment_score': c.sentiment_score,
                        'sentiment_label': c.sentiment_label,
                        'product_name': c.product_name,
                        'amount': c.amount,
                        'incident_date': c.incident_date,
                        'severity': c.severity,
                        'processed_at': c.processed_at
                    })
                df = pd.DataFrame(data)
            
            # 导出为CSV
            csv_path = os.path.join(self.output_dir, f"complaints_{datetime.now().strftime('%Y%m%d')}.csv")
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            logging.info(f"成功导出数据到CSV文件: {csv_path}")
            
        except Exception as e:
            logging.error(f"导出CSV失败: {str(e)}")
            
    def get_complaints_dataframe(self, days=None):
        """
        获取投诉数据作为Pandas DataFrame
        
        Args:
            days: 获取最近几天的数据，默认为None获取所有数据
            
        Returns:
            DataFrame: 包含投诉数据的DataFrame
        """
        query = "SELECT * FROM complaints"
        
        if days:
            cutoff_date = (datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            query += f" WHERE date_received >= '{cutoff_date}'"
            
        df = pd.read_sql_query(query, self.engine)
        return df 