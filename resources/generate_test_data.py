"""
测试数据生成工具 - 用于生成模拟客户投诉数据进行系统测试
"""
import os
import random
import json
import datetime
import argparse
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from libraries.database_handler import DatabaseHandler, Complaint

# 模拟投诉内容模板
COMPLAINT_TEMPLATES = [
    "我在{date}订购的{product}至今还未收到，订单号是{order_number}。我已经等了{days}天，远超预期送达时间。请尽快处理或者退款。",
    "我收到的{product}已经损坏了，包装也很差。订单号{order_number}，价格{amount}元。这样的质量太差了，我要求退货退款。",
    "我对贵公司的客服态度非常不满。我多次联系关于订单{order_number}的{product}问题，但总是得不到及时回复。这种服务太差了。",
    "我购买的{product}和描述完全不符，质量非常差。订单号{order_number}，价格{amount}元。我要求退货并全额退款。",
    "{product}收到后发现是假货，与官方产品相差很大。订单号{order_number}，希望尽快给我答复，否则我将投诉消费者协会。",
    "我在{date}参加了你们的促销活动，购买了{product}，订单号{order_number}，但没有享受到承诺的折扣{amount}元。请解释清楚。",
    "你们的App系统有问题，我无法查看我的订单{order_number}，也无法联系客服。这已经是本月第三次出现这种问题了。",
    "我想退货退款我在{date}买的{product}（订单号{order_number}），但是系统一直提示错误，客服也联系不上，太让人失望了。"
]

# 模拟商品列表
PRODUCTS = [
    "iPhone 13", "华为 P50", "小米11", "三星 Galaxy S21", 
    "苹果耳机", "罗技鼠标", "机械键盘", "游戏显示器",
    "Nike运动鞋", "Adidas外套", "Puma背包", "New Balance跑鞋",
    "索尼相机", "佳能打印机", "戴尔笔记本", "华硕显卡",
    "电饭煲", "微波炉", "洗衣机", "冰箱"
]

def generate_order_number():
    """生成随机订单号"""
    return f"ORD-{random.randint(10000000, 99999999)}"

def generate_random_date(days_back=30):
    """生成随机日期"""
    today = datetime.datetime.now()
    random_days = random.randint(1, days_back)
    random_date = today - datetime.timedelta(days=random_days)
    return random_date.strftime("%Y-%m-%d")

def generate_test_complaints(count=20):
    """生成指定数量的模拟投诉数据"""
    complaints = []
    
    for i in range(count):
        # 基础数据
        product = random.choice(PRODUCTS)
        order_number = generate_order_number()
        date = generate_random_date()
        days = random.randint(3, 15)
        amount = random.randint(100, 5000) + random.randint(0, 99) / 100
        
        # 随机选择投诉模板
        template = random.choice(COMPLAINT_TEMPLATES)
        
        # 填充模板
        content = template.format(
            product=product,
            order_number=order_number,
            date=date,
            days=days,
            amount=amount
        )
        
        # 生成主题
        subject_templates = [
            f"关于{product}的投诉",
            f"订单{order_number}问题反馈",
            f"对{product}质量的投诉",
            f"客服服务投诉",
            f"退款请求：{order_number}",
            f"产品质量问题：{product}"
        ]
        subject = random.choice(subject_templates)
        
        # 生成发件人
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "qq.com", "163.com", "126.com"]
        names = ["zhang", "li", "wang", "chen", "liu", "yang", "huang", "zhao", "wu", "zhou"]
        sender = f"{random.choice(names)}{random.randint(100, 999)}@{random.choice(domains)}"
        
        # 生成时间戳
        now = datetime.datetime.now()
        random_minutes = random.randint(1, 60 * 24 * days)
        timestamp = now - datetime.timedelta(minutes=random_minutes)
        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # 创建投诉记录
        complaint = {
            'id': f"TEST{i+1}",
            'sender': sender,
            'subject': subject,
            'content': content,
            'date': date_str,
            'order_number': order_number
        }
        
        complaints.append(complaint)
    
    return complaints

def save_to_json(complaints, filename="test_complaints.json"):
    """保存投诉数据到JSON文件"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(complaints, f, ensure_ascii=False, indent=2)
    
    print(f"已生成{len(complaints)}条测试数据，保存至: {file_path}")
    return file_path

def save_to_database(complaints):
    """保存投诉数据到数据库"""
    db_handler = DatabaseHandler()
    saved_count = db_handler.save_complaints(complaints)
    print(f"已将{saved_count}条测试数据保存到数据库")

def main():
    parser = argparse.ArgumentParser(description="生成模拟客户投诉数据")
    parser.add_argument("-c", "--count", type=int, default=20, help="生成的投诉数量，默认20条")
    parser.add_argument("-o", "--output", type=str, default="test_complaints.json", help="输出JSON文件名")
    parser.add_argument("-d", "--database", action="store_true", help="是否保存到数据库")
    
    args = parser.parse_args()
    
    # 生成测试数据
    complaints = generate_test_complaints(args.count)
    
    # 保存到JSON
    save_to_json(complaints, args.output)
    
    # 如果需要，保存到数据库
    if args.database:
        save_to_database(complaints)

if __name__ == "__main__":
    main() 