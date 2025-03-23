"""
投诉分类器模块 - 负责对投诉进行分类并提取关键信息
"""
import os
import logging
import re
import json
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from transformers import pipeline
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ComplaintClassifier:
    def __init__(self):
        """初始化投诉分类器"""
        # 初始化NLTK资源
        self._download_nltk_resources()
        
        # 获取停用词
        self.stop_words = set(stopwords.words('english'))
        
        # 加载分类模型
        self.use_transformer = os.getenv("USE_TRANSFORMER_CLASSIFIER", "True").lower() == "true"
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "models")
        
        # 确保资源目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载投诉类别信息
        self.complaint_categories = self._load_complaint_categories()
        
        # 初始化关键词提取器
        if self.use_transformer:
            self._initialize_transformer_model()
        
        logging.info("投诉分类器初始化完成")

    def _download_nltk_resources(self):
        """下载NLTK资源"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt', quiet=True)
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords', quiet=True)
    
    def _initialize_transformer_model(self):
        """初始化Transformer模型用于零样本分类"""
        try:
            logging.info("正在加载零样本分类模型")
            self.classifier = pipeline(
                "zero-shot-classification", 
                model="facebook/bart-large-mnli",
                cache_dir=self.cache_dir
            )
            logging.info("零样本分类模型加载成功")
        except Exception as e:
            logging.error(f"加载分类模型失败: {str(e)}")
            self.use_transformer = False
            
    def _load_complaint_categories(self):
        """加载投诉类别和关键词"""
        categories_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            "resources", 
            "complaint_categories.json"
        )
        
        # 如果文件不存在，创建默认类别
        if not os.path.exists(categories_file):
            categories = {
                "物流延迟": ["延迟", "还没到", "运输时间", "配送慢", "物流", "快递", "发货", "到达", "等待"],
                "商品损坏": ["损坏", "破损", "不完整", "质量问题", "有缺陷", "坏了", "不能用"],
                "退款问题": ["退款", "退钱", "不退", "退换", "取消订单", "不给退"],
                "商品质量": ["质量", "不好", "差", "不符合", "假货", "不如描述", "不如预期"],
                "客服体验": ["客服", "服务", "态度", "回复", "沟通", "联系不上", "没人理"],
                "账户问题": ["账户", "登录", "密码", "无法访问", "注册", "个人信息"],
                "促销争议": ["优惠券", "折扣", "促销", "活动", "降价", "价格", "广告"],
                "系统故障": ["网站", "App", "系统", "错误", "故障", "无法", "不能", "崩溃", "加载"]
            }
            
            # 创建资源目录
            os.makedirs(os.path.dirname(categories_file), exist_ok=True)
            
            # 保存默认类别
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)
        else:
            # 加载已有类别
            with open(categories_file, 'r', encoding='utf-8') as f:
                categories = json.load(f)
                
        logging.info(f"加载了 {len(categories)} 个投诉类别")
        return categories
        
    def classify(self, text):
        """
        对投诉文本进行分类
        
        Args:
            text: 投诉文本内容
            
        Returns:
            str: 投诉类别
        """
        if not text:
            return "未分类"
            
        # 使用Transformer模型进行零样本分类
        if self.use_transformer:
            try:
                candidate_labels = list(self.complaint_categories.keys())
                result = self.classifier(text, candidate_labels, multi_label=False)
                return result['labels'][0]  # 返回最可能的类别
            except Exception as e:
                logging.warning(f"使用Transformer分类失败: {str(e)}, 回退到关键词匹配")
                # 失败时回退到关键词匹配
        
        # 关键词匹配方法
        word_counts = {category: 0 for category in self.complaint_categories}
        
        # 对文本进行分词
        try:
            tokens = word_tokenize(text.lower())
            # 移除停用词
            tokens = [word for word in tokens if word.isalpha() and word not in self.stop_words]
        except:
            # 如果分词失败，使用简单的空格分割
            tokens = text.lower().split()
        
        # 计算每个类别的关键词匹配数
        for category, keywords in self.complaint_categories.items():
            for keyword in keywords:
                keyword_lower = keyword.lower()
                if keyword_lower in text.lower():
                    word_counts[category] += 1
                    
        # 找到匹配关键词最多的类别
        max_count = max(word_counts.values())
        
        if max_count == 0:
            return "未分类"
        
        # 如果有多个类别匹配相同数量的关键词，返回第一个
        for category, count in word_counts.items():
            if count == max_count:
                return category
    
    def extract_key_info(self, text):
        """
        从投诉文本中提取关键信息
        
        Args:
            text: 投诉文本内容
            
        Returns:
            dict: 包含提取的关键信息
        """
        info = {}
        
        # 提取产品名称 (假设产品名称是引号中的内容或全大写的单词)
        product_pattern = r'"([^"]+)"|\'([^\']+)\'|[A-Z]{2,}'
        products = re.findall(product_pattern, text)
        if products:
            # 处理不同类型的匹配结果
            product_list = []
            for p in products:
                if isinstance(p, tuple):
                    # 如果是引号匹配，找到非空的匹配组
                    for item in p:
                        if item:
                            product_list.append(item)
                else:
                    product_list.append(p)
            
            if product_list:
                info['product_name'] = product_list[0]  # 取第一个匹配项作为产品名
        
        # 提取金额
        amount_pattern = r'\$\s*(\d+(?:\.\d{2})?)|(\d+(?:\.\d{2})?)\s*美元|(\d+(?:\.\d{2})?)\s*元'
        amounts = re.findall(amount_pattern, text)
        if amounts:
            # 处理不同类型的匹配结果
            for amount_match in amounts:
                if isinstance(amount_match, tuple):
                    # 找到非空的匹配组
                    for amount in amount_match:
                        if amount:
                            info['amount'] = float(amount)
                            break
                else:
                    info['amount'] = float(amount_match)
                    
                if 'amount' in info:
                    break
        
        # 提取日期
        date_pattern = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4}|\d{1,2}[-/]\d{1,2}[-/]\d{2}'
        dates = re.findall(date_pattern, text)
        if dates:
            info['incident_date'] = dates[0]
            
        # 提取投诉严重程度（基于关键词）
        severity_keywords = {
            '高': ['紧急', '立即', '非常不满', '极其', '要求', '投诉', '退款', '起诉', '举报', '丢失'],
            '中': ['不满', '问题', '失望', '退换', '损坏', '延迟', '错误'],
            '低': ['咨询', '建议', '希望', '改进', '询问', '请问']
        }
        
        severity_scores = {'高': 0, '中': 0, '低': 0}
        for severity, keywords in severity_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    severity_scores[severity] += 1
        
        max_severity = max(severity_scores, key=severity_scores.get)
        if severity_scores[max_severity] > 0:
            info['severity'] = max_severity
        else:
            info['severity'] = '中'  # 默认严重程度
            
        return info 