import os
import asyncio
import json
from typing import List, Tuple, Dict

from openai import AsyncOpenAI
from aiolimiter import AsyncLimiter
from dotenv import load_dotenv

from .llm_error import ResponseParseError

load_dotenv()

class Agent:
    def __init__(self, model_name: str, base_url: str, rate_limit: AsyncLimiter):
        self.client = AsyncOpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url=base_url
        )
        self.question_dir = "./data/tasks"
        self.model_name = model_name
        self.rate_limit = rate_limit
        self.try_again_time = 1

    async def ainvoke(self,
            answer_file_path: str,
            question_num: int) -> Tuple[bool, int, str, int]:
        
        answer = self._read(answer_file_path)
        question, solution, score = self._read_question(question_num)

        for attempt in range(self.try_again_time + 1):
            try:
                completion = await self._invoke(question=question,solution=solution,score=score,answer=answer)
        
                return self._process_response(completion)
            
            except Exception as e:
                print(f"[尝试 {attempt+1}] 调用失败: {e}")
                if attempt < self.try_again_time:
                    continue
                else:
                    if isinstance(e, ResponseParseError):
                        return (False,0,f"{e}. 原始输出: {e.raw_output}",e.tokens,)
                    else:
                        return False, 0, f"多次调用失败: {e}", 0
    
    async def _invoke(self,
            question: str,
            solution: str,
            score: str,
            answer: str):
        async with self.rate_limit:
            completion = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': r"""
                        你是一位精通 MATLAB 的教授，负责批改学生的作业。你的任务是：
                        1. 判断学生提交的代码是否正确。学生们都是初学者，请大体上放水一点，可以对不重要的错误睁一只眼闭一只眼。只要其大体功能实现，便可认为其完成作答。
                        2. 按照给你的总分，根据其正确程度给出分数。不重要的小错误就象征性扣一点点分数。
                        3. 如果有错误，需要指出清晰的错误原因；如果完全正确，错误原因留空。
                        
                        输出格式必须是 JSON，且为一个三元素 tuple：[是否正确 (true/false), 分数 (整数), 错误原因 (字符串)]。
                        不要输出json ```，而是直接输出一个合法json。如果你需要在文本中使用双引号，需要使用\" 以符合json语法
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
            return completion
        
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
    
    def _process_response(self, completion):
        raw_output = completion.choices[0].message.content.strip()
        try:
            result = json.loads(raw_output)
            if isinstance(result, list) and len(result) == 3:
                is_correct, grade, reason = result
                return bool(is_correct), int(grade), str(reason), int(completion.usage.total_tokens)
        except Exception as e:
            raise ResponseParseError(
            f"解析模型输出失败: {e}",
            raw_output,
            int(completion.usage.total_tokens),
        )