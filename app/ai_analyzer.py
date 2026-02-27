"""
AI数据分析模块
集成DeepSeek API进行数据质量分析和智能建议生成
"""

import json
import os
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI数据分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化AI分析器
        
        Args:
            api_key: DeepSeek API密钥（可选，从环境变量读取）
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com"
    
    def analyze_data_quality(self, data_report: Dict[str, Any], sample_data: List[Dict]) -> Dict[str, Any]:
        """
        分析数据质量并生成AI建议
        
        Args:
            data_report: 数据质量报告
            sample_data: 示例数据（前10行）
            
        Returns:
            Dict: AI分析报告
        """
        try:
            # 如果API密钥可用，调用真实API
            if self.api_key:
                return self._call_deepseek_api(data_report, sample_data)
            else:
                # 模拟AI分析结果（开发阶段）
                return self._simulate_ai_analysis(data_report, sample_data)
                
        except Exception as e:
            logger.error(f"AI分析失败: {str(e)}")
            return self._generate_fallback_report(data_report)
    
    def _call_deepseek_api(self, data_report: Dict[str, Any], sample_data: List[Dict]) -> Dict[str, Any]:
        """
        调用DeepSeek API进行数据分析
        
        Args:
            data_report: 数据质量报告
            sample_data: 示例数据
            
        Returns:
            Dict: API响应解析后的报告
        """
        import requests
        
        # 构建分析提示
        prompt = self._build_analysis_prompt(data_report, sample_data)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的数据分析师，擅长发现数据质量问题并提供改进建议。请用中文回答。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            ai_content = result["choices"][0]["message"]["content"]
            
            # 解析AI响应
            return self._parse_ai_response(ai_content, data_report)
            
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {str(e)}")
            return self._simulate_ai_analysis(data_report, sample_data)
    
    def _build_analysis_prompt(self, data_report: Dict[str, Any], sample_data: List[Dict]) -> str:
        """
        构建分析提示
        
        Args:
            data_report: 数据质量报告
            sample_data: 示例数据
            
        Returns:
            str: 分析提示
        """
        basic_stats = data_report.get("basic_stats", {})
        missing_values = data_report.get("missing_values", {})
        duplicate_rows = data_report.get("duplicate_rows", {})
        outlier_detection = data_report.get("outlier_detection", {})
        
        prompt = f"""
        请分析以下数据集的质量问题并提供改进建议：
        
        1. 数据集基本信息：
           - 行数：{basic_stats.get('row_count', 0)}
           - 列数：{basic_stats.get('column_count', 0)}
           - 列名：{', '.join(basic_stats.get('columns', []))}
           - 数据类型分布：{json.dumps(basic_stats.get('data_types', {}), ensure_ascii=False)}
        
        2. 缺失值情况：
           - 总缺失值数：{missing_values.get('total', 0)}
           - 缺失值占比：{missing_values.get('percentage', 0):.2f}%
           - 各列缺失情况：{json.dumps(missing_values.get('by_column', {}), ensure_ascii=False)}
        
        3. 重复数据：
           - 重复行数：{duplicate_rows.get('count', 0)}
           - 重复行占比：{duplicate_rows.get('percentage', 0):.2f}%
        
        4. 异常值检测（数值列）：
           {json.dumps(outlier_detection, ensure_ascii=False)}
        
        5. 数据样本（前{min(10, len(sample_data))}行）：
           {json.dumps(sample_data, ensure_ascii=False, indent=2)}
        
        请从以下角度提供专业分析：
        1. 数据质量综合评价（从1-5星评级）
        2. 主要问题识别（按严重程度排序）
        3. 具体改进建议（针对每个问题）
        4. 数据清洗优先级建议
        5. 潜在分析价值挖掘
        
        请用结构化格式输出，包含清晰的标题和要点。
        """
        
        return prompt
    
    def _parse_ai_response(self, ai_content: str, data_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析AI响应内容
        
        Args:
            ai_content: AI返回的文本内容
            data_report: 原始数据报告
            
        Returns:
            Dict: 结构化分析报告
        """
        # 这里可以添加更复杂的解析逻辑
        # 目前直接返回AI文本内容
        
        return {
            "ai_analysis": ai_content,
            "quality_rating": self._extract_quality_rating(ai_content),
            "key_issues": self._extract_key_issues(ai_content),
            "recommendations": self._extract_recommendations(ai_content),
            "data_report_summary": {
                "row_count": data_report.get("basic_stats", {}).get("row_count", 0),
                "missing_percentage": data_report.get("missing_values", {}).get("percentage", 0),
                "duplicate_percentage": data_report.get("duplicate_rows", {}).get("percentage", 0)
            }
        }
    
    def _extract_quality_rating(self, content: str) -> int:
        """从内容中提取质量评级（1-5星）"""
        import re
        
        # 查找星级评价
        patterns = [
            r'(\d)\s*[颗星★]',
            r'评分[:：]\s*(\d)',
            r'(\d)/5',
            r'quality.*?(\d)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    rating = int(match.group(1))
                    if 1 <= rating <= 5:
                        return rating
                except:
                    pass
        
        # 默认返回3星
        return 3
    
    def _extract_key_issues(self, content: str) -> List[str]:
        """从内容中提取关键问题"""
        import re
        
        issues = []
        
        # 查找问题列表
        lines = content.split('\n')
        in_issues_section = False
        
        issue_patterns = [
            r'^[•\-*]\s*(.+)',
            r'^\d+[\.\)]\s*(.+)',
            r'^[-]\s*(.+)'
        ]
        
        for line in lines:
            line_lower = line.lower()
            
            # 检测问题章节
            if any(keyword in line_lower for keyword in ['问题', 'issue', 'problem', '缺陷']):
                in_issues_section = True
                continue
            
            if in_issues_section:
                # 匹配问题项
                for pattern in issue_patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        issue = match.group(1).strip()
                        if len(issue) > 10:  # 过滤过短的项
                            issues.append(issue)
        
        # 如果没有找到结构化问题，返回前3个要点
        if not issues:
            bullet_points = re.findall(r'[•\-*]\s*(.+)', content)
            issues = bullet_points[:3]
        
        return issues[:5]  # 最多返回5个问题
    
    def _extract_recommendations(self, content: str) -> List[str]:
        """从内容中提取建议"""
        import re
        
        recommendations = []
        
        # 查找建议列表
        lines = content.split('\n')
        in_recommendations_section = False
        
        rec_patterns = [
            r'^[•\-*]\s*(.+)',
            r'^\d+[\.\)]\s*(.+)',
            r'^建议[:：]\s*(.+)'
        ]
        
        for line in lines:
            line_lower = line.lower()
            
            # 检测建议章节
            if any(keyword in line_lower for keyword in ['建议', 'recommendation', 'solution', '改进']):
                in_recommendations_section = True
                continue
            
            if in_recommendations_section:
                # 匹配建议项
                for pattern in rec_patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        rec = match.group(1).strip()
                        if len(rec) > 10:  # 过滤过短的项
                            recommendations.append(rec)
        
        # 如果没有找到结构化建议，返回一些通用建议
        if not recommendations:
            recommendations = [
                "清理缺失值和重复数据以提高数据质量",
                "标准化数值列以消除异常值影响",
                "验证数据类型确保分析准确性"
            ]
        
        return recommendations[:5]  # 最多返回5个建议
    
    def _simulate_ai_analysis(self, data_report: Dict[str, Any], sample_data: List[Dict]) -> Dict[str, Any]:
        """
        模拟AI分析（用于开发测试）
        
        Args:
            data_report: 数据质量报告
            sample_data: 示例数据
            
        Returns:
            Dict: 模拟分析报告
        """
        basic_stats = data_report.get("basic_stats", {})
        missing_values = data_report.get("missing_values", {})
        duplicate_rows = data_report.get("duplicate_rows", {})
        outlier_detection = data_report.get("outlier_detection", {})
        
        # 计算质量评级
        missing_percent = missing_values.get("percentage", 0)
        duplicate_percent = duplicate_rows.get("percentage", 0)
        
        quality_score = 5
        if missing_percent > 30:
            quality_score -= 2
        elif missing_percent > 10:
            quality_score -= 1
            
        if duplicate_percent > 20:
            quality_score -= 1
            
        if len(outlier_detection) > 0:
            quality_score -= 0.5
        
        quality_score = max(1, min(5, int(quality_score)))
        
        key_issues = []
        if missing_percent > 10:
            key_issues.append(f"缺失值比例较高 ({missing_percent:.1f}%)，影响分析完整性")
        if duplicate_percent > 10:
            key_issues.append(f"存在重复数据 ({duplicate_percent:.1f}%)，可能导致分析偏差")
        if len(outlier_detection) > 0:
            key_issues.append(f"数值列存在异常值，需要进一步处理")
        
        recommendations = [
            "使用适当的策略填充或删除缺失值",
            "删除完全重复的数据行",
            "对数值列进行异常值检测和处理",
            "验证并转换数据类型确保一致性",
            "考虑数据标准化或归一化处理"
        ]
        
        return {
            "ai_analysis": f"数据质量分析报告\n\n数据集包含{basic_stats.get('row_count', 0)}行，{basic_stats.get('column_count', 0)}列。\n主要问题：{'; '.join(key_issues) if key_issues else '无明显严重问题'}。\n建议按照优先级进行数据清洗。",
            "quality_rating": quality_score,
            "key_issues": key_issues,
            "recommendations": recommendations,
            "data_report_summary": {
                "row_count": basic_stats.get("row_count", 0),
                "missing_percentage": missing_percent,
                "duplicate_percentage": duplicate_percent,
                "outlier_columns_count": len(outlier_detection)
            }
        }
    
    def _generate_fallback_report(self, data_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回退报告（当所有分析都失败时）
        
        Args:
            data_report: 数据质量报告
            
        Returns:
            Dict: 基本分析报告
        """
        basic_stats = data_report.get("basic_stats", {})
        
        return {
            "ai_analysis": "数据质量分析暂时不可用，请检查API配置或网络连接。",
            "quality_rating": 3,
            "key_issues": ["无法进行AI分析"],
            "recommendations": ["请确保DeepSeek API密钥正确配置", "检查网络连接", "尝试重新分析"],
            "data_report_summary": {
                "row_count": basic_stats.get("row_count", 0),
                "column_count": basic_stats.get("column_count", 0)
            }
        }