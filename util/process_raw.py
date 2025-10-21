import os
import re
from typing import Optional, List, Tuple, Dict

from .mlx2others import mlx2others, matlab_engine
from .check_file import check_process_correctness
from .unzip_raw import unzip_and_flatten

def process_raw(
        overlap_mode: bool = False,
        raw_dir: str = "./data/raw", 
        processed_dir: str = "./data/processed") -> None:
    """
    批量处理原始目录中的MLX文件、
    1. 将raw文件夹中压缩包解压缩 （详细逻辑在unzip_and_flatten）
    2. 检查是否已经完成初始化（除非overlap_mode=True）（详细逻辑在check_process_correctness）
    3. 转化为Markdown格式
    4. 按照题号进行切分
    
    Args:
        raw_dir: 原始文件目录
        processed_dir: 处理后文件输出目录
    """
    for file in os.listdir(raw_dir):
        if file.endswith(".zip") and os.path.isfile(os.path.join(raw_dir, file)):
            zip_path = os.path.join(raw_dir, file)
            log_path = os.path.join(raw_dir, "unzip_warnings.log")
            unzip_and_flatten(zip_path, log_path, processed_dir)

    with matlab_engine() as eng:
        for root, dirs, files in os.walk(raw_dir):

            # check if alerady processed
            subdir_name = os.path.relpath(root, raw_dir)
            if subdir_name == '.': continue
            if not overlap_mode and check_process_correctness(subdir_name):
                print(f"Skip {subdir_name}, already processed correctly.")
                continue
            
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
                    split_by_question(root, md_output_path, question_output_dir)


                    print(f"Processed {mlx_input_path} to {md_output_path}")
    

def split_by_question(m_dir: str, md_file: str, output_dir: str) -> None:
    """
    按题目切分markdown文件
    
    Args:
        m_dir: 原始文件路径（提供.m funciton file)
        md_file: 输入的markdown文件路径
        output_dir: 输出目录路径
    """
    # 读取markdown文件内容
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取所有题目内容
    questions: List[Tuple[int, str]] = _extract_questions(content)
    m_func_dict: Dict[str,str] = _collect_m_function_files(m_dir)
    questions = [(question_num, _append_m_dependencies(code_block,m_func_dict))
                  for (question_num, code_block) in questions]
    
    # 为每个题目创建目录并保存文件
    for question_num, code_block in questions:
        question_dir = os.path.join(output_dir, str(question_num))
        os.makedirs(question_dir, exist_ok=True)
        
        answer_file = os.path.join(question_dir, "answer.md")
        with open(answer_file, 'w', encoding='utf-8') as f:
            f.write(code_block.strip())


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
    pattern = r'#\s*[以上以下]{2}[开始结束]{2}第(\d+)题\s*\n(.*?)\n#\s*[以上以下]{2}[开始结束]{2}第\1题'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for question_num_str, question_content in matches:
        question_num = int(question_num_str)
        questions.append((question_num, question_content))
    
    return questions

def _append_m_dependencies(code_block: str, m_func_dict: Dict[str,str]) -> str:
    """
    给定一段 MATLAB 代码块和文件夹路径，
    如果代码块中调用了外部 .m 文件定义的主函数，
    就把对应的函数源码附加到代码块后面。

    Args:
        code_block : 切分后的question code block
        m_func_dict: function_name:function_code

    Returns:
        str: 原始代码 + 附加的依赖函数源码
    """
    result = code_block

    # 1. 在代码块中查找调用了哪些函数
    called_funcs = []
    for name in m_func_dict:
        # 匹配 “名字(” 的模式，避免混淆变量
        if (
            re.search(rf'\b{name}\s*\(', code_block) or
            re.search(rf'@\s*{name}\b', code_block)
        ):
            called_funcs.append(name)

    # 2. 按顺序附加源码
    for cf in called_funcs:
        result += f"\n\n% === Dependency: {cf}.m ===\n```matlab"
        result += m_func_dict[cf]
        result += "```"

    return result

def _collect_m_function_files(folder: str) -> Dict[str,str]:
    """
    收集所有外部.m function file
    """
    func_dict = {}
    for fn in os.listdir(folder):
        if fn.endswith(".m"):
            func_name = os.path.splitext(fn)[0]
            file_path = os.path.join(folder, fn)
            try:
                with open(file_path, encoding="utf-8") as f:
                    func_code = f.read()
                func_dict[func_name] = func_code
            except Exception as e:
                print(f"读取 {file_path} 出错: {e}")
    return func_dict
