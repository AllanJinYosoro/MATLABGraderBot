
import re
from collections import defaultdict
from typing import List, Tuple, Optional, Dict

from bs4 import BeautifulSoup


def html2text(html_path: str) -> str:
    """
    将HTML文件转换为文本格式，提取源代码和输出结果
    
    Args:
        html_path: HTML文件路径
        
    Returns:
        转换后的文本字符串
    """
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    # 提取SOURCE区域的代码内容
    source_text = _extract_source_content(soup)
    if not source_text:
        return ""

    # 按%%分割为代码单元
    cells: List[str] = re.split(r"^%%", source_text, flags=re.MULTILINE)
    
    # 提取代码输出映射关系
    results_map: Dict[str, List[str]] = _extract_code_outputs(soup)
    
    # 构建最终文本
    return _build_output_text(cells, results_map)


def _extract_source_content(soup: BeautifulSoup) -> str:
    """提取HTML中SOURCE区域的内容"""
    source_comment = soup.find(string=re.compile("SOURCE BEGIN"))
    if not source_comment:
        return ""
    
    source_text = str(source_comment)
    source_text = re.sub(r"##### SOURCE (?:BEGIN|END) #####", "", source_text)
    return source_text.strip()


def _extract_code_outputs(soup: BeautifulSoup) -> Dict[str, List[str]]:
    """
    提取代码及其对应的输出结果
    
    Returns:
        字典，key为代码文本，value为输出结果列表（支持同一代码多个输出）
    """
    results_map = defaultdict(list)
    
    for wrapper in soup.select(".inlineWrapper.outputs"):
        code_div = wrapper.find(["div"], class_=["S1", "S3"])
        out_div = wrapper.find("div", class_="S2")
        
        if code_div and out_div:
            code_text = code_div.get_text(strip=True)
            out_text = out_div.get_text(strip=True)
            if code_text and out_text:
                results_map[code_text].append(out_text)
    
    return dict(results_map)


def _build_output_text(cells: List[str], results_map: Dict[str, List[str]]) -> str:
    """
    构建最终的输出文本
    
    Args:
        cells: 代码单元列表
        results_map: 代码到输出结果的映射字典
    """
    lines = []
    # 用于追踪每个代码的使用次数，解决重复代码的匹配问题
    code_usage_count = defaultdict(int)
    
    for cell in cells:
        cell_content = cell.strip()
        if not cell_content:
            continue
            
        lines.append("===cell开始===")
        
        for line in cell_content.splitlines():
            lines.append(line)
            
            line_stripped = line.strip()
            if line_stripped in results_map:
                outputs = results_map[line_stripped]
                # 使用计数器来处理相同代码的多次出现
                usage_index = code_usage_count[line_stripped]
                if usage_index < len(outputs):
                    lines.append(f"% 输出: {outputs[usage_index]}")
                    code_usage_count[line_stripped] += 1
        
        lines.extend(["===cell结束===", ""])
    
    return "\n".join(lines)