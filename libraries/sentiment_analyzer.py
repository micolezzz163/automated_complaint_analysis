"""
情感分析模块 - 使用Hugging Face Transformers进行情感分析
"""
import os
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        """初始化情感分析器"""
        # 模型设置
        self.model_name = os.getenv("SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.max_length = 512  # 输入文本最大长度
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "models")
        
        # 确保缓存目录存在
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # 加载模型和分词器
        try:
            logging.info(f"正在加载情感分析模型: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=self.cache_dir)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name, cache_dir=self.cache_dir)
            self.model.to(self.device)
            self.model.eval()  # 设置为评估模式
            logging.info("情感分析模型加载成功")
        except Exception as e:
            logging.error(f"加载情感分析模型失败: {str(e)}")
            raise

    def analyze(self, text):
        """
        分析文本情感
        
        Args:
            text: 要分析的文本
            
        Returns:
            tuple: (情感分数, 情感标签)
                情感分数是-1到1之间的浮点数，-1表示极度负面，1表示极度正面
                情感标签是字符串，为"正面"、"负面"或"中性"
        """
        try:
            # 处理长文本
            if len(text) > self.max_length * 10:  # 如果文本非常长
                # 截取前后部分进行分析
                first_part = text[:self.max_length * 2]
                last_part = text[-self.max_length * 2:]
                
                # 分析两部分并取平均值
                first_score, _ = self._analyze_text(first_part)
                last_score, _ = self._analyze_text(last_part)
                score = (first_score + last_score) / 2
            else:
                # 对整个文本进行分析
                score, _ = self._analyze_text(text)
            
            # 确定情感标签
            if score > 0.2:
                label = "正面"
            elif score < -0.2:
                label = "负面"
            else:
                label = "中性"
                
            return score, label
            
        except Exception as e:
            logging.error(f"情感分析失败: {str(e)}")
            return 0.0, "中性"  # 发生错误时返回中性
            
    def _analyze_text(self, text):
        """对文本进行情感分析，返回原始分数和类别ID"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=self.max_length, padding=True)
        inputs = {key: val.to(self.device) for key, val in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # 获取情感预测分数
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=1)
        probabilities = probabilities.cpu().numpy()[0]
        
        # 对于二分类模型（如sst-2）
        if len(probabilities) == 2:
            # 将[0,1]范围的正面概率转换为[-1,1]范围的情感分数
            score = (probabilities[1] - 0.5) * 2
            class_id = 1 if probabilities[1] > probabilities[0] else 0
        # 对于多分类模型
        else:
            # 假设标签按负面到正面排序
            weighted_sum = sum(i * p for i, p in enumerate(probabilities))
            normalized_score = (weighted_sum / (len(probabilities) - 1) - 0.5) * 2
            score = normalized_score
            class_id = np.argmax(probabilities)
            
        return float(score), int(class_id) 