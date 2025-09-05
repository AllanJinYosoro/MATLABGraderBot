import os
import re
from typing import Optional, List, Tuple

from .mlx2others import mlx2others, matlab_engine

def process_raw(raw_dir: str = "./data/raw", processed_dir: str = "./data/processed") -> None:
    """
    批量处理原始目录中的MLX文件
    1. 转化为Markdown格式
    2. 按照题号进行切分
    
    Args:
        raw_dir: 原始文件目录
        processed_dir: 处理后文件输出目录
    """
    with matlab_engine() as eng:
        for root, dirs, files in os.walk(raw_dir):
            for file in files:
                if file.endswith(".mlx"):
                    mlx_input_path = os.path.join(root, file)
                    relative_path = os.path.relpath(mlx_input_path, raw_dir)
                    md_output_path = os.path.join(processed_dir, os.path.splitext(relative_path)[0] + ".md")
                    
                    os.makedirs(os.path.dirname(md_output_path), exist_ok=True)
                    
                    #1. 转化为markdown
                    mlx2others(eng, mlx_input_path, md_output_path)

                    #2. 切分markdown
                    question_output_dir = os.path.dirname(md_output_path)
                    split_by_question(md_output_path, question_output_dir)


                    print(f"Processed {mlx_input_path} to {md_output_path}")
    

def split_by_question(md_file: str, output_dir: str) -> None:
    """
    按题目切分markdown文件
    
    Args:
        md_file: 输入的markdown文件路径
        output_dir: 输出目录路径
    """
    # 读取markdown文件内容
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有题目内容
    questions: List[Tuple[int, str]] = _extract_questions(content)
    
    # 为每个题目创建目录并保存文件
    for question_num, question_content in questions:
        question_dir = os.path.join(output_dir, str(question_num))
        os.makedirs(question_dir, exist_ok=True)
        
        answer_file = os.path.join(question_dir, "answer.md")
        with open(answer_file, 'w', encoding='utf-8') as f:
            f.write(question_content.strip())


def _extract_questions(content: str) -> List[Tuple[int, str]]:
    """
    从markdown内容中提取题目
    
    Args:
        content: markdown文件内容
        
    Returns:
        题目列表，每个元素为(题目编号, 题目内容)
    """
    questions = []
    
    # 使用正则表达式匹配题目开始和结束标记
    pattern = r'# 以下开始第(\d+)题\s*\n(.*?)\n# 以上结束第\1题'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for question_num_str, question_content in matches:
        question_num = int(question_num_str)
        questions.append((question_num, question_content))
    
    return questions