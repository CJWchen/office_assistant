"""
会议纪要助手模块
实现文本处理、智能摘要、待办事项管理、时间线可视化功能
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk import pos_tag
import pandas as pd
import requests
from flask import current_app

# 设置日志
logger = logging.getLogger(__name__)

class TextProcessor:
    """文本处理基础功能"""
    
    def __init__(self, language='zh'):
        """
        初始化文本处理器
        Args:
            language: 语言代码，支持'zh'（中文）和'en'（英文）
        """
        self.language = language
        self._setup_nltk()
        
    def _setup_nltk(self):
        """下载必要的NLTK数据"""
        try:
            # 中文需要额外处理
            if self.language == 'zh':
                # 使用jieba进行中文分词
                try:
                    import jieba
                    import jieba.posseg as pseg
                    self.jieba = jieba
                    self.pseg = pseg
                    self.has_jieba = True
                except ImportError:
                    logger.warning("jieba未安装，中文分词功能受限")
                    self.has_jieba = False
            else:
                # 英文NLTK数据
                nltk_data = ['punkt', 'stopwords', 'averaged_perceptron_tagger']
                for data in nltk_data:
                    try:
                        nltk.data.find(f'tokenizers/{data}')
                    except LookupError:
                        nltk.download(data, quiet=True)
        except Exception as e:
            logger.error(f"NLTK设置失败: {e}")
    
    def parse_text_file(self, file_path: str) -> str:
        """
        解析文本文件（支持.txt, .docx格式）
        Args:
            file_path: 文件路径
        Returns:
            文本内容字符串
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif ext == '.docx':
                # 使用python-docx解析
                try:
                    import docx
                    doc = docx.Document(file_path)
                    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
                except ImportError:
                    logger.error("python-docx未安装，无法解析docx文件")
                    raise
            else:
                raise ValueError(f"不支持的文件格式: {ext}，仅支持.txt和.docx")
        except Exception as e:
            logger.error(f"文件解析失败: {e}")
            raise
    
    def preprocess_text(self, text: str) -> str:
        """
        文本预处理：清洗、去除特殊字符、标准化
        Args:
            text: 原始文本
        Returns:
            预处理后的文本
        """
        # 去除多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 去除特殊字符（保留中文、英文、数字、基本标点）
        if self.language == 'zh':
            # 中文文本：保留中文、英文、数字、常见标点
            text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？；："\'、（）《》【】]', '', text)
        else:
            # 英文文本：保留英文、数字、基本标点
            text = re.sub(r'[^a-zA-Z0-9\s.,!?;:"\'()\[\]{}]', '', text)
        
        return text
    
    def segment_text(self, text: str, mode='paragraph') -> List[str]:
        """
        文本分段
        Args:
            text: 文本内容
            mode: 分段模式，'paragraph'（段落）或'sentence'（句子）
        Returns:
            分段后的文本列表
        """
        if mode == 'paragraph':
            # 按段落分割（空行分割）
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
            return paragraphs
        elif mode == 'sentence':
            # 按句子分割
            if self.language == 'zh':
                # 中文句子分割：使用句号、问号、感叹号等分割
                sentences = re.split(r'[。！？；]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]
            else:
                # 英文句子分割：使用NLTK
                sentences = sent_tokenize(text)
            return sentences
        else:
            raise ValueError(f"不支持的mode: {mode}")
    
    def tokenize_words(self, text: str) -> List[str]:
        """
        分词
        Args:
            text: 文本内容
        Returns:
            分词结果列表
        """
        if self.language == 'zh':
            if self.has_jieba:
                return list(self.jieba.cut(text))
            else:
                # 简单按字符分割
                return list(text)
        else:
            return word_tokenize(text)
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        去除停用词
        Args:
            tokens: 分词列表
        Returns:
            去除停用词后的分词列表
        """
        if self.language == 'zh':
            # 中文停用词列表
            stop_words = set(['的', '了', '在', '是', '我', '有', '和', '就', 
                            '不', '人', '都', '一', '一个', '上', '也', '很', 
                            '到', '说', '要', '去', '你', '会', '着', '没有', 
                            '看', '好', '自己', '这'])
        else:
            # 英文停用词
            stop_words = set(stopwords.words('english'))
        
        return [token for token in tokens if token.lower() not in stop_words]
    
    def evaluate_text_quality(self, text: str) -> Dict[str, Any]:
        """
        评估文本质量
        Args:
            text: 文本内容
        Returns:
            质量评估报告
        """
        # 基本统计
        char_count = len(text)
        word_count = len(self.tokenize_words(text))
        sentence_count = len(self.segment_text(text, mode='sentence'))
        paragraph_count = len(self.segment_text(text, mode='paragraph'))
        
        # 可读性评估（简单版本）
        readability_score = 0
        if sentence_count > 0 and word_count > 0:
            # Flesch Reading Ease的简化版本
            if self.language == 'en':
                # 英文可读性：句子越短，单词越短，得分越高
                avg_sentence_length = word_count / sentence_count
                readability_score = max(0, min(100, 100 - avg_sentence_length))
            else:
                # 中文可读性：基于平均句子长度
                avg_sentence_length = char_count / sentence_count
                readability_score = max(0, min(100, 100 - avg_sentence_length / 10))
        
        # 完整性检查（是否有明显缺失）
        completeness_score = 100
        if char_count < 50:
            completeness_score = 30  # 文本太短
        elif char_count > 10000:
            completeness_score = 90  # 文本足够长
        
        # 语言检测（简单版本）
        language_detected = self.language
        if self.language == 'auto':
            # 简单检测：根据字符范围判断
            chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
            english_chars = len(re.findall(r'[a-zA-Z]', text))
            if chinese_chars > english_chars:
                language_detected = 'zh'
            else:
                language_detected = 'en'
        
        return {
            'char_count': char_count,
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'readability_score': round(readability_score, 2),
            'completeness_score': completeness_score,
            'language_detected': language_detected,
            'summary': '良好' if completeness_score > 70 and readability_score > 50 else '需要改进'
        }


class SummaryGenerator:
    """智能摘要生成系统"""
    
    def __init__(self, api_key=None):
        """
        初始化摘要生成器
        Args:
            api_key: DeepSeek API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.environ.get('DEEPSEEK_API_KEY')
        self.api_url = "https://api.deepseek.com/chat/completions"
        
    def generate_summary(self, text: str, language='zh') -> Dict[str, Any]:
        """
        生成结构化摘要
        Args:
            text: 原始文本
            language: 语言代码
        Returns:
            结构化摘要数据
        """
        try:
            # 调用DeepSeek API生成摘要
            summary_text = self._call_deepseek_api(text, language)
            
            # 解析摘要为结构化数据
            structured_data = self._parse_summary_to_structure(summary_text, language)
            
            # 提取关键信息
            key_info = self._extract_key_information(text, language)
            
            return {
                'summary_text': summary_text,
                'structured_data': structured_data,
                'key_information': key_info,
                'language': language,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            raise
    
    def _call_deepseek_api(self, text: str, language: str) -> str:
        """
        调用DeepSeek API生成摘要
        Args:
            text: 原始文本
            language: 语言代码
        Returns:
            摘要文本
        """
        # 构建提示词
        if language == 'zh':
            system_prompt = """你是一个专业的会议纪要助手。请根据以下会议文本，生成一份结构清晰的会议纪要摘要。

要求：
1. 摘要需要包含以下部分：
   - 会议主题
   - 主要讨论问题
   - 关键讨论点
   - 达成的决议
   - 待办事项（行动项）

2. 每个部分用简洁明了的语言概括
3. 保持专业性和准确性
4. 提取关键数字、时间点和责任人

请直接输出摘要内容，不要添加额外说明。"""
            
            user_prompt = f"以下是会议文本：\n\n{text}\n\n请生成会议纪要摘要："
        else:
            system_prompt = """You are a professional meeting minutes assistant. Please generate a structured meeting summary based on the following meeting text.

Requirements:
1. The summary should include the following sections:
   - Meeting Topic
   - Main Discussion Issues
   - Key Discussion Points
   - Decisions Made
   - Action Items (Todo Items)

2. Use concise and clear language for each section
3. Maintain professionalism and accuracy
4. Extract key numbers, time points, and responsible persons

Please output the summary content directly, without additional explanations."""
            
            user_prompt = f"Here is the meeting text:\n\n{text}\n\nPlease generate the meeting summary:"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            # 如果API失败，返回简化摘要
            return self._generate_fallback_summary(text, language)
    
    def _generate_fallback_summary(self, text: str, language: str) -> str:
        """
        生成回退摘要（当API不可用时）
        Args:
            text: 原始文本
            language: 语言代码
        Returns:
            简化摘要文本
        """
        # 简单分段并取前3段作为摘要
        processor = TextProcessor(language)
        paragraphs = processor.segment_text(text, mode='paragraph')
        
        if len(paragraphs) <= 3:
            return '\n\n'.join(paragraphs)
        else:
            return '\n\n'.join(paragraphs[:3]) + '\n\n...（更多内容省略）'
    
    def _parse_summary_to_structure(self, summary_text: str, language: str) -> Dict[str, Any]:
        """
        将摘要文本解析为结构化数据
        Args:
            summary_text: 摘要文本
            language: 语言代码
        Returns:
            结构化数据
        """
        # 简单的正则匹配提取结构
        structure = {
            'meeting_topic': '',
            'discussion_issues': [],
            'discussion_points': [],
            'decisions': [],
            'action_items': []
        }
        
        # 中文模式
        if language == 'zh':
            # 提取会议主题
            topic_match = re.search(r'会议主题[:：]\s*(.+?)(?=\n|$)', summary_text)
            if topic_match:
                structure['meeting_topic'] = topic_match.group(1).strip()
            
            # 提取讨论问题
            issues_matches = re.findall(r'(?:主要讨论问题|讨论议题)[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if issues_matches:
                structure['discussion_issues'] = [issue.strip() for issue in issues_matches]
            
            # 提取关键讨论点
            points_matches = re.findall(r'(?:关键讨论点|讨论要点)[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if points_matches:
                structure['discussion_points'] = [point.strip() for point in points_matches]
            
            # 提取决议
            decisions_matches = re.findall(r'(?:达成的决议|决议)[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if decisions_matches:
                structure['decisions'] = [decision.strip() for decision in decisions_matches]
            
            # 提取待办事项
            todos_matches = re.findall(r'(?:待办事项|行动项)[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if todos_matches:
                structure['action_items'] = [todo.strip() for todo in todos_matches]
        
        # 英文模式
        else:
            topic_match = re.search(r'Meeting Topic[:：]\s*(.+?)(?=\n|$)', summary_text)
            if topic_match:
                structure['meeting_topic'] = topic_match.group(1).strip()
            
            issues_matches = re.findall(r'Main Discussion Issues[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if issues_matches:
                structure['discussion_issues'] = [issue.strip() for issue in issues_matches]
            
            points_matches = re.findall(r'Key Discussion Points[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if points_matches:
                structure['discussion_points'] = [point.strip() for point in points_matches]
            
            decisions_matches = re.findall(r'Decisions Made[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if decisions_matches:
                structure['decisions'] = [decision.strip() for decision in decisions_matches]
            
            todos_matches = re.findall(r'Action Items[:：]\s*(.+?)(?=\n|$)', summary_text, re.MULTILINE)
            if todos_matches:
                structure['action_items'] = [todo.strip() for todo in todos_matches]
        
        return structure
    
    def _extract_key_information(self, text: str, language: str) -> Dict[str, Any]:
        """
        提取关键信息：人物、时间、地点、数字
        Args:
            text: 原始文本
            language: 语言代码
        Returns:
            关键信息字典
        """
        key_info = {
            'persons': [],
            'times': [],
            'locations': [],
            'numbers': [],
            'dates': []
        }
        
        # 提取时间信息
        time_patterns = [
            r'\d{1,2}[:：]\d{1,2}',  # 10:30, 10:30:00
            r'\d{1,2}\s*(?:AM|PM|am|pm)',  # 10 AM
            r'上午\s*\d{1,2}[:：]\d{1,2}',  # 上午10:30
            r'下午\s*\d{1,2}[:：]\d{1,2}'   # 下午2:30
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            key_info['times'].extend(matches)
        
        # 提取日期信息
        date_patterns = [
            r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',  # 2024-12-27
            r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',  # 12/27/2024
            r'\d{4}年\d{1,2}月\d{1,2}日',    # 2024年12月27日
            r'\d{1,2}月\d{1,2}日'            # 12月27日
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            key_info['dates'].extend(matches)
        
        # 提取数字
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, text)
        key_info['numbers'] = [float(num) if '.' in num else int(num) for num in numbers]
        
        # 提取可能的人名（简单版本）
        # 中文人名：2-4个汉字
        if language == 'zh':
            name_pattern = r'[张王李赵刘陈杨黄吴周徐孙马朱胡林郭何高罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文]+\s*[张王李赵刘陈杨黄吴周徐孙马朱胡林郭何高罗郑梁谢宋唐许韩冯邓曹彭曾萧田董袁潘于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖熊金陆郝孔白崔康毛邱秦江史顾侯邵孟龙万段雷钱汤尹黎易常武乔贺赖龚文]+'
            names = re.findall(name_pattern, text)
            key_info['persons'] = list(set(names))
        
        return key_info


class TodoManager:
    """待办事项管理工具"""
    
    def __init__(self):
        """初始化待办管理器"""
        pass
    
    def extract_todo_items(self, text: str, language='zh') -> List[Dict[str, Any]]:
        """
        从文本中提取待办事项
        Args:
            text: 文本内容
            language: 语言代码
        Returns:
            待办事项列表
        """
        todo_items = []
        
        # 使用正则匹配常见的待办表达模式
        patterns = {
            'zh': [
                r'(?:需要|要|必须|得|应该)(.+?)(?:完成|处理|解决|跟进|负责)(?:，|。|；|）|）)?',
                r'(?:由|由.*?)([^，。；]+?)(?:负责|跟进|处理)(.+?)(?:，|。|；|）|）)?',
                r'(?:截止|截至|期限)[:：]\s*([^，。；]+?)(?:，|。|；|）|）)?',
                r'(?:行动项|待办事项)[:：]\s*(.+?)(?=\n|$)',
                r'(?:TODO|todo)[:：]\s*(.+?)(?=\n|$)'
            ],
            'en': [
                r'(?:need|must|should|have to)(.+?)(?:complete|handle|solve|follow up|responsible)(?:,|.|;|\)|})?',
                r'(?:by|assigned to)\s*([^,.]+?)(?:to|for|will)(.+?)(?:,|.|;|\)|})?',
                r'(?:deadline|due date)[:：]\s*([^,.]+?)(?:,|.|;|\)|})?',
                r'(?:action item|todo item)[:：]\s*(.+?)(?=\n|$)',
                r'(?:TODO|todo)[:：]\s*(.+?)(?=\n|$)'
            ]
        }
        
        lang_patterns = patterns.get(language, patterns['zh'])
        
        for pattern in lang_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    # 处理多个捕获组的情况
                    description = ' '.join([m for m in match if m]).strip()
                else:
                    description = match.strip()
                
                if description and len(description) > 3:
                    # 提取责任人
                    assignee = self._extract_assignee(description, language)
                    
                    # 提取截止日期
                    due_date = self._extract_due_date(description, language)
                    
                    # 评估优先级
                    priority = self._evaluate_priority(description, language)
                    
                    todo_items.append({
                        'description': description,
                        'assignee': assignee,
                        'priority': priority,
                        'due_date': due_date,
                        'status': 'pending',
                        'extracted_from': description[:100]  # 保留原始文本片段
                    })
        
        # 去重
        unique_items = []
        seen_descriptions = set()
        for item in todo_items:
            desc_key = item['description'].lower().strip()
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                unique_items.append(item)
        
        return unique_items
    
    def _extract_assignee(self, text: str, language: str) -> str:
        """
        提取责任人
        Args:
            text: 文本
            language: 语言代码
        Returns:
            责任人姓名
        """
        # 简单模式匹配
        assignee_patterns = {
            'zh': [
                r'由\s*([^，。；]+?)\s*(?:负责|跟进|处理)',
                r'([^，。；]+?)\s*负责',
                r'责任人[:：]\s*([^，。；]+?)(?:，|。|；|）|）)?'
            ],
            'en': [
                r'by\s*([^,.]+?)(?:to|for|will)',
                r'assigned to\s*([^,.]+?)(?:,|.|;|\)|})?',
                r'responsible person[:：]\s*([^,.]+?)(?:,|.|;|\)|})?'
            ]
        }
        
        patterns = assignee_patterns.get(language, assignee_patterns['zh'])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_due_date(self, text: str, language: str) -> Optional[str]:
        """
        提取截止日期
        Args:
            text: 文本
            language: 语言代码
        Returns:
            截止日期字符串（ISO格式）或None
        """
        date_patterns = {
            'zh': [
                r'(?:截止|截至|期限)[:：]\s*([^，。；]+?)(?:，|。|；|）|）)?',
                r'(?:在|于)\s*([^，。；]+?)\s*(?:之前|前)完成',
                r'(?:下周一|下周二|下周三|下周四|下周五|下周六|下周日|下周)',
                r'(?:明天|后天|大后天)',
                r'\d{4}年\d{1,2}月\d{1,2}日',
                r'\d{1,2}月\d{1,2}日'
            ],
            'en': [
                r'(?:deadline|due date)[:：]\s*([^,.]+?)(?:,|.|;|\)|})?',
                r'due by\s*([^,.]+?)(?:,|.|;|\)|})?',
                r'(?:next Monday|next Tuesday|next Wednesday|next Thursday|next Friday|next Saturday|next Sunday|next week)',
                r'(?:tomorrow|day after tomorrow)',
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
                r'\d{1,2}[-/]\d{1,2}[-/]\d{4}'
            ]
        }
        
        patterns = date_patterns.get(language, date_patterns['zh'])
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1).strip() if match.groups() else match.group(0).strip()
                # 尝试解析日期
                try:
                    # 这里可以添加更复杂的日期解析逻辑
                    # 暂时返回原始字符串
                    return date_str
                except:
                    return date_str
        
        return None
    
    def _evaluate_priority(self, text: str, language: str) -> int:
        """
        评估优先级（1-低，2-中，3-高）
        Args:
            text: 文本
            language: 语言代码
        Returns:
            优先级数值
        """
        # 关键词匹配
        high_priority_keywords = {
            'zh': ['紧急', '重要', '尽快', '立即', '马上', '必须', '优先', '关键'],
            'en': ['urgent', 'important', 'asap', 'immediately', 'now', 'must', 'priority', 'critical']
        }
        
        low_priority_keywords = {
            'zh': ['可选', '次要', '不急', '后续', '将来', '有空', '方便时'],
            'en': ['optional', 'secondary', 'not urgent', 'later', 'future', 'when convenient']
        }
        
        text_lower = text.lower()
        
        # 检查高优先级关键词
        for keyword in high_priority_keywords.get(language, high_priority_keywords['zh']):
            if keyword.lower() in text_lower:
                return 3
        
        # 检查低优先级关键词
        for keyword in low_priority_keywords.get(language, low_priority_keywords['zh']):
            if keyword.lower() in text_lower:
                return 1
        
        # 默认中等优先级
        return 2
    
    def create_reminder(self, todo_item: Dict[str, Any], reminder_days: int = 1) -> Dict[str, Any]:
        """
        创建提醒
        Args:
            todo_item: 待办事项
            reminder_days: 提前提醒天数
        Returns:
            提醒信息
        """
        reminder = {
            'todo_description': todo_item['description'],
            'assignee': todo_item.get('assignee', ''),
            'due_date': todo_item.get('due_date'),
            'priority': todo_item.get('priority', 2),
            'reminder_time': datetime.now() + timedelta(days=reminder_days),
            'reminder_message': f"待办事项提醒：{todo_item['description']}"
        }
        
        if todo_item.get('assignee'):
            reminder['reminder_message'] += f"（责任人：{todo_item['assignee']}）"
        
        return reminder
    
    def export_to_calendar(self, todo_items: List[Dict[str, Any]], format_type='ical') -> str:
        """
        导出为日历格式
        Args:
            todo_items: 待办事项列表
            format_type: 格式类型，支持'ical'（iCalendar）或'csv'
        Returns:
            日历格式字符串
        """
        if format_type == 'ical':
            # 生成简单的iCalendar格式
            ical_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Meeting Minutes Assistant//EN
"""
            
            for i, item in enumerate(todo_items):
                event_id = f"todo_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                summary = item['description'][:100]
                
                ical_content += f"""BEGIN:VEVENT
UID:{event_id}
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{summary}
STATUS:CONFIRMED
"""
                
                if item.get('due_date'):
                    # 尝试解析日期
                    try:
                        # 简化处理：假设日期字符串
                        due_str = item['due_date']
                        ical_content += f"DTSTART;VALUE=DATE:{due_str.replace('-', '').replace('/', '')}\n"
                    except:
                        pass
                
                ical_content += "END:VEVENT\n"
            
            ical_content += "END:VCALENDAR"
            return ical_content
        
        elif format_type == 'csv':
            # 生成CSV格式
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(['Description', 'Assignee', 'Priority', 'Due Date', 'Status'])
            
            # 写入数据
            for item in todo_items:
                writer.writerow([
                    item['description'],
                    item.get('assignee', ''),
                    item.get('priority', 2),
                    item.get('due_date', ''),
                    item.get('status', 'pending')
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")


class TimelineVisualizer:
    """时间线可视化组件"""
    
    def __init__(self):
        """初始化时间线可视化器"""
        pass
    
    def extract_timeline_data(self, text: str, language='zh') -> List[Dict[str, Any]]:
        """
        从文本中提取时间线数据
        Args:
            text: 文本内容
            language: 语言代码
        Returns:
            时间线数据列表
        """
        timeline_items = []
        
        # 时间模式匹配
        time_patterns = [
            # 时间点
            r'(\d{1,2}[:：]\d{1,2})\s*(?:左右|许|时|分)?',
            # 时间段
            r'(\d{1,2}[:：]\d{1,2})[～~-](\d{1,2}[:：]\d{1,2})',
            # 日期+时间
            r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s+(\d{1,2}[:：]\d{1,2})',
            # 中文日期时间
            r'(\d{4}年\d{1,2}月\d{1,2}日)\s*(?:上午|下午)?\s*(\d{1,2}[:：]\d{1,2})',
            # 相对时间
            r'(?:接下来|随后|然后|接着)\s*(?:的)?\s*(\d+)\s*(?:分钟|小时|天|周|月|年)',
            r'(?:之前|以前|前)\s*(\d+)\s*(?:分钟|小时|天|周|月|年)'
        ]
        
        # 简单分词并查找时间相关上下文
        sentences = TextProcessor(language).segment_text(text, mode='sentence')
        
        for sentence in sentences:
            # 查找时间信息
            time_matches = []
            for pattern in time_patterns:
                matches = re.findall(pattern, sentence)
                if matches:
                    time_matches.extend(matches)
            
            if time_matches:
                # 提取时间点附近的上下文作为事件描述
                # 简单取句子前10个字符作为事件标题
                event_title = sentence[:50].strip()
                if len(event_title) > 50:
                    event_title = event_title[:47] + '...'
                
                timeline_items.append({
                    'time': time_matches[0] if isinstance(time_matches[0], str) else str(time_matches[0]),
                    'event': event_title,
                    'description': sentence,
                    'sentence_index': sentences.index(sentence),
                    'has_time': True
                })
            else:
                # 没有明确时间，但可能是重要事件
                # 使用启发式规则判断重要性
                importance_keywords = {
                    'zh': ['决定', '决议', '达成', '同意', '通过', '确认', '安排', '计划'],
                    'en': ['decide', 'resolution', 'agree', 'approve', 'confirm', 'arrange', 'plan']
                }
                
                keywords = importance_keywords.get(language, importance_keywords['zh'])
                for keyword in keywords:
                    if keyword.lower() in sentence.lower():
                        timeline_items.append({
                            'time': f"事件_{len(timeline_items)}",
                            'event': sentence[:50].strip(),
                            'description': sentence,
                            'sentence_index': sentences.index(sentence),
                            'has_time': False
                        })
                        break
        
        # 按句子索引排序
        timeline_items.sort(key=lambda x: x['sentence_index'])
        
        return timeline_items
    
    def create_timeline_chart(self, timeline_data: List[Dict[str, Any]], language='zh') -> Dict[str, Any]:
        """
        创建ECharts时间线图表配置
        Args:
            timeline_data: 时间线数据
            language: 语言代码
        Returns:
            ECharts配置字典
        """
        # 处理数据
        categories = []
        data = []
        
        for i, item in enumerate(timeline_data):
            categories.append(item['time'])
            
            data.append({
                'name': item['event'],
                'value': [
                    i,  # x轴索引
                    item['time'],
                    item['description'][:100],
                    '有具体时间' if item.get('has_time', False) else '无具体时间'
                ],
                'symbolSize': 10 if item.get('has_time', False) else 6
            })
        
        # 构建ECharts配置
        chart_config = {
            'title': {
                'text': '会议时间线' if language == 'zh' else 'Meeting Timeline',
                'left': 'center'
            },
            'tooltip': {
                'trigger': 'item',
                'formatter': '{b}<br/>{c}'
            },
            'grid': {
                'left': '6%',
                'right': '6%',
                'bottom': '3%',
                'containLabel': True
            },
            'xAxis': {
                'type': 'category',
                'data': categories,
                'axisLabel': {
                    'color': '#666'
                },
                'axisLine': {
                    'lineStyle': {
                        'color': '#666'
                    }
                }
            },
            'yAxis': {
                'type': 'value',
                'axisLabel': {
                    'color': '#666'
                },
                'axisLine': {
                    'lineStyle': {
                        'color': '#666'
                    }
                }
            },
            'series': [{
                'type': 'scatter',
                'data': data,
                'symbolSize': lambda val: val[3],
                'itemStyle': {
                    'color': '#5470c6'
                },
                'emphasis': {
                    'itemStyle': {
                        'color': '#ee6666'
                    }
                }
            }]
        }
        
        return chart_config
    
    def export_timeline(self, timeline_data: List[Dict[str, Any]], format_type='json') -> str:
        """
        导出时间线数据
        Args:
            timeline_data: 时间线数据
            format_type: 格式类型，支持'json'、'csv'、'html'
        Returns:
            导出格式字符串
        """
        if format_type == 'json':
            return json.dumps(timeline_data, ensure_ascii=False, indent=2)
        
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow(['Time', 'Event', 'Description', 'Has Time'])
            
            # 写入数据
            for item in timeline_data:
                writer.writerow([
                    item.get('time', ''),
                    item.get('event', ''),
                    item.get('description', '')[:200],
                    'Yes' if item.get('has_time', False) else 'No'
                ])
            
            return output.getvalue()
        
        elif format_type == 'html':
            # 生成简单的HTML表格
            html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>会议时间线</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .has-time { color: green; }
        .no-time { color: gray; }
    </style>
</head>
<body>
    <h1>会议时间线</h1>
    <table>
        <tr>
            <th>时间</th>
            <th>事件</th>
            <th>描述</th>
            <th>时间明确</th>
        </tr>
"""
            
            for item in timeline_data:
                time_class = 'has-time' if item.get('has_time', False) else 'no-time'
                time_text = item.get('time', '')
                event_text = item.get('event', '')
                desc_text = item.get('description', '')[:100]
                
                html_content += f"""
        <tr>
            <td>{time_text}</td>
            <td>{event_text}</td>
            <td>{desc_text}</td>
            <td class="{time_class}">{'是' if item.get('has_time', False) else '否'}</td>
        </tr>
"""
            
            html_content += """
    </table>
</body>
</html>
"""
            return html_content
        
        else:
            raise ValueError(f"不支持的格式类型: {format_type}")


class MeetingMinutesAssistant:
    """会议纪要助手主类"""
    
    def __init__(self, api_key=None):
        """
        初始化会议纪要助手
        Args:
            api_key: DeepSeek API密钥
        """
        self.text_processor = TextProcessor()
        self.summary_generator = SummaryGenerator(api_key)
        self.todo_manager = TodoManager()
        self.timeline_visualizer = TimelineVisualizer()
        
    def process_meeting_text(self, file_path: str, language='zh') -> Dict[str, Any]:
        """
        处理会议文本文件
        Args:
            file_path: 文件路径
            language: 语言代码
        Returns:
            完整的处理结果
        """
        try:
            # 1. 文本处理
            logger.info("开始解析文件...")
            raw_text = self.text_processor.parse_text_file(file_path)
            
            logger.info("文本预处理...")
            processed_text = self.text_processor.preprocess_text(raw_text)
            
            logger.info("评估文本质量...")
            quality_report = self.text_processor.evaluate_text_quality(processed_text)
            
            # 2. 智能摘要生成
            logger.info("生成智能摘要...")
            summary_data = self.summary_generator.generate_summary(processed_text, language)
            
            # 3. 待办事项提取
            logger.info("提取待办事项...")
            todo_items = self.todo_manager.extract_todo_items(processed_text, language)
            
            # 4. 时间线提取
            logger.info("提取时间线数据...")
            timeline_data = self.timeline_visualizer.extract_timeline_data(processed_text, language)
            
            # 5. 创建时间线图表
            logger.info("生成时间线图表...")
            timeline_chart = self.timeline_visualizer.create_timeline_chart(timeline_data, language)
            
            # 整合结果
            result = {
                'text_processing': {
                    'raw_text_sample': raw_text[:500],  # 只保留样本
                    'processed_text_sample': processed_text[:500],
                    'quality_report': quality_report
                },
                'summary': summary_data,
                'todo_items': todo_items,
                'timeline': {
                    'data': timeline_data,
                    'chart_config': timeline_chart
                },
                'processing_time': datetime.now().isoformat(),
                'language': language
            }
            
            logger.info("会议纪要处理完成")
            return result
            
        except Exception as e:
            logger.error(f"会议纪要处理失败: {e}")
            raise
    
    def export_results(self, result: Dict[str, Any], export_format: str = 'json') -> str:
        """
        导出处理结果
        Args:
            result: 处理结果
            export_format: 导出格式，支持'json'、'markdown'、'html'
        Returns:
            导出内容字符串
        """
        if export_format == 'json':
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        elif export_format == 'markdown':
            md_content = "# 会议纪要处理报告\n\n"
            
            # 基本信息
            md_content += f"## 基本信息\n"
            md_content += f"- 处理时间：{result.get('processing_time', 'N/A')}\n"
            md_content += f"- 语言：{result.get('language', 'zh')}\n\n"
            
            # 文本质量报告
            quality = result['text_processing']['quality_report']
            md_content += f"## 文本质量评估\n"
            md_content += f"- 字符数：{quality.get('char_count', 0)}\n"
            md_content += f"- 词数：{quality.get('word_count', 0)}\n"
            md_content += f"- 句子数：{quality.get('sentence_count', 0)}\n"
            md_content += f"- 段落数：{quality.get('paragraph_count', 0)}\n"
            md_content += f"- 可读性得分：{quality.get('readability_score', 0)}/100\n"
            md_content += f"- 完整性得分：{quality.get('completeness_score', 0)}/100\n"
            md_content += f"- 总体评价：{quality.get('summary', 'N/A')}\n\n"
            
            # 摘要
            summary = result['summary']
            md_content += f"## 会议摘要\n"
            md_content += f"{summary.get('summary_text', '')}\n\n"
            
            # 待办事项
            todos = result['todo_items']
            if todos:
                md_content += f"## 待办事项 ({len(todos)}项)\n\n"
                for i, todo in enumerate(todos, 1):
                    md_content += f"{i}. **{todo.get('description', '')}**\n"
                    if todo.get('assignee'):
                        md_content += f"   - 责任人：{todo.get('assignee')}\n"
                    if todo.get('priority'):
                        priority_map = {1: '低', 2: '中', 3: '高'}
                        md_content += f"   - 优先级：{priority_map.get(todo.get('priority'), todo.get('priority'))}\n"
                    if todo.get('due_date'):
                        md_content += f"   - 截止日期：{todo.get('due_date')}\n"
                    md_content += "\n"
            
            # 时间线
            timeline = result['timeline']['data']
            if timeline:
                md_content += f"## 时间线 ({len(timeline)}个事件)\n\n"
                for i, event in enumerate(timeline, 1):
                    md_content += f"{i}. **{event.get('time', '')}** - {event.get('event', '')}\n"
                    md_content += f"   - {event.get('description', '')[:100]}...\n\n"
            
            return md_content
        
        elif export_format == 'html':
            # 使用Markdown转换HTML
            import markdown
            md_content = self.export_results(result, 'markdown')
            html_content = markdown.markdown(md_content, extensions=['extra'])
            
            return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>会议纪要处理报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
        h1 {{ color: #333; border-bottom: 2px solid #eee; }}
        h2 {{ color: #555; margin-top: 30px; }}
        ul {{ padding-left: 20px; }}
        .todo-item {{ background: #f9f9f9; padding: 10px; margin: 5px 0; border-left: 4px solid #5470c6; }}
        .timeline-event {{ border: 1px solid #ddd; padding: 10px; margin: 10px 0; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
        
        else:
            raise ValueError(f"不支持的导出格式: {export_format}")