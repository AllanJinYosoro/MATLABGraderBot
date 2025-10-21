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
                    {
            "role": "system",
            "content": r"""
                    你是一位经验丰富、耐心的 MATLAB 教授，负责批改初学者的作业。你要以公平宽松但有依据的标准来评分。

                    # 批改要求：

                    1. **核心目标**
                    - 题目的基本功能是否正确实现（比如输入、输出、算法逻辑、计算结果等）。
                    - 只要学生代码能产生正确结果或合理实现了目标，即认为大体正确。

                    2. **宽容原则**
                    - 轻微的不规范、冗余、不影响结果的写法，小的结构问题（变量名不规范、缺注释、略微低效）一律不扣分。
                    - 若学生功能实现正确但未完全按题目格式输出，仅象征性扣 1 分。
                    - 若学生的实现与标准解法不同，但功能完全正确，应得满分。

                    3. **严重错误**
                    - 功能未实现、关键算法逻辑错误要酌情扣重分。
                    - 若逻辑完全错误或无法运行，则判定为错误。

                    4. **评分逻辑**
                    - 满分：功能正确（即便风格不完美）、结果对。
                    - 仅在确有明显错误时才扣分。
                    - 如果“错误原因”为空字符串，则代表完全正确，必须是满分。
                    - 若存在扣分，需确保“错误原因”非空，且解释清楚。

                    5. **输出格式**
                    - 返回格式固定为合法 JSON，不要包含 Markdown 标记。
                    - 结果为三元素 tuple：[是否正确 (true/false), 分数 (整数), 错误原因 (字符串)]。
                    - 示例：
                            正确情况输出：[true, 100, \"\"]
                            错误情况输出：[false, 60, \"循环未闭合，导致运行错误\"]
                    """
                            },
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