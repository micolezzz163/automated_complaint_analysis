"""
邮件处理模块 - 负责连接邮箱、获取并解析投诉邮件
"""
import imaplib
import email
from email.header import decode_header
import os
import logging
import re
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class EmailProcessor:
    def __init__(self):
        """初始化邮件处理器"""
        self.imap_server = os.getenv("IMAP_SERVER", "imap.gmail.com")
        self.imap_port = int(os.getenv("IMAP_PORT", 993))
        self.email_address = os.getenv("EMAIL_ADDRESS")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.complaint_folder = os.getenv("COMPLAINT_FOLDER", "INBOX")
        
        if not self.email_address or not self.email_password:
            raise ValueError("邮箱地址和密码必须在环境变量中设置")
            
        logging.info(f"邮件处理器初始化完成，邮箱: {self.email_address}")
    
    def _connect_to_imap(self):
        """连接到IMAP服务器"""
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(self.email_address, self.email_password)
            return mail
        except Exception as e:
            logging.error(f"连接IMAP服务器失败: {str(e)}")
            raise
    
    def _extract_order_number(self, text):
        """从文本中提取订单号"""
        # 假设订单号格式为ORD-开头加8位数字
        order_pattern = r'ORD-\d{8}'
        match = re.search(order_pattern, text)
        return match.group(0) if match else None
    
    def _decode_email_content(self, msg):
        """解码邮件内容"""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # 跳过附件
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        content = part.get_payload(decode=True).decode('utf-8')
                        return content
                    except:
                        try:
                            return part.get_payload(decode=True).decode('latin-1')
                        except:
                            logging.warning("无法解码邮件内容")
                            return ""
        else:
            try:
                content = msg.get_payload(decode=True).decode('utf-8')
                return content
            except:
                try:
                    return msg.get_payload(decode=True).decode('latin-1')
                except:
                    logging.warning("无法解码邮件内容")
                    return ""
    
    def fetch_emails(self, max_emails=100, only_unread=True):
        """
        从邮箱获取投诉邮件
        
        Args:
            max_emails: 最大获取邮件数量
            only_unread: 是否只获取未读邮件
            
        Returns:
            list: 包含投诉邮件信息的字典列表
        """
        mail = self._connect_to_imap()
        
        try:
            # 选择邮件文件夹
            mail.select(self.complaint_folder)
            
            # 搜索邮件
            search_criteria = "UNSEEN" if only_unread else "ALL"
            status, messages = mail.search(None, search_criteria)
            
            if status != 'OK':
                logging.error(f"搜索邮件失败: {status}")
                return []
            
            # 获取邮件ID列表
            email_ids = messages[0].split()
            
            # 限制获取数量
            if len(email_ids) > max_emails:
                email_ids = email_ids[:max_emails]
            
            complaints = []
            
            # 处理每封邮件
            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    logging.warning(f"获取邮件 {email_id} 失败")
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # 解析邮件头
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else 'utf-8')
                
                from_, encoding = decode_header(msg.get("From"))[0]
                if isinstance(from_, bytes):
                    from_ = from_.decode(encoding if encoding else 'utf-8')
                
                # 提取发件人邮箱
                from_email = re.search(r'<(.+?)>', from_)
                sender_email = from_email.group(1) if from_email else from_
                
                # 获取日期
                date_str = msg.get("Date")
                try:
                    # 尝试解析邮件日期
                    date_tuple = email.utils.parsedate_tz(date_str)
                    date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
                    date_formatted = date.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    date_formatted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # 获取邮件内容
                content = self._decode_email_content(msg)
                
                # 提取订单号
                order_number = self._extract_order_number(content)
                
                # 创建投诉记录
                complaint = {
                    'id': email_id.decode(),
                    'sender': sender_email,
                    'subject': subject,
                    'date': date_formatted,
                    'content': content,
                    'order_number': order_number
                }
                
                complaints.append(complaint)
                
                # 标记邮件为已读
                mail.store(email_id, '+FLAGS', '\\Seen')
            
            return complaints
            
        finally:
            # 关闭连接
            mail.close()
            mail.logout() 