import os
from openai import OpenAI
from dotenv import load_dotenv
import json
from typing import List, Tuple, Dict

load_dotenv()

class Agent:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.question_dir = "./data/tasks"

    def invoke(self,
            answer_file_path: str,
            question_num: int) -> Tuple[bool, int, str, int]:
        
        answer = self._read(answer_file_path)
        question, solution, score = self._read_question(question_num)

        completion = self.client.chat.completions.create(
            model="qwen3-coder-flash",
            messages=[
                {'role': 'system', 'content': r"""
                    你是一位精通 MATLAB 的教授，负责批改学生的作业。你的任务是：
                    1. 公正地判断学生提交的代码是否正确。
                    2. 按照给你的总分，根据其正确程度给出分数。
                    3. 如果有错误，需要指出清晰的错误原因；如果完全正确，错误原因留空。
                    
                    输出格式必须是 JSON，且为一个三元素 tuple：[是否正确 (true/false), 分数 (整数), 错误原因 (字符串)]。
                    示例：
                        正确情况输出：[true, 95, \"\"]
                        错误情况输出：[false, 60, \"循环语句未正确结束，导致运行错误\"]
                """},
                {'role': 'user', 'content': fr"""
                    题目是：
                    {question}
                    
                    供你参考的标准答案是：
                    {solution}
                    
                    这道题的总分是：{score}

                    有一位同学的mlx文件答案是：
                    {answer}
                """}],
            )
        
        raw_output = completion.choices[0].message.content.strip()
        try:
            result = json.loads(raw_output)
            if isinstance(result, list) and len(result) == 3:
                is_correct, grade, reason = result
                return bool(is_correct), int(grade), str(reason), int(completion.usage.total_tokens)
        except Exception as e:
            print("警告，存在错误")
            return False, 0, f"解析模型输出失败: {e}. 原始输出: {raw_output}", int(completion.usage.total_tokens)
        
    @staticmethod
    def _read(file_path: str) -> str:
        encodings = ["utf-8", "gbk"]
        last_error = None
        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as file:
                    return file.read()
            except UnicodeDecodeError as e:
                last_error = e
                continue
        raise UnicodeDecodeError(
            f"无法使用以下编码读取文件 {file_path}: {encodings}. 最后错误: {last_error}"
        )
    
    def _read_question(self, question_num: int) -> Tuple[str,str,str]:
        current_question_dir = os.path.join(self.question_dir,str(question_num))

        return (
            self._read(os.path.join(current_question_dir,'task_content')),
            self._read(os.path.join(current_question_dir,'solution')),
            self._read(os.path.join(current_question_dir,'score'))
        )