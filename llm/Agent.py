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
                        return (False,None,f"{e}. 原始输出: {e.raw_output}",e.tokens,)
                    else:
                        return False, None, f"多次调用失败: {e}", 0
    
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
                    你是一位**严格但宽容且公正的 MATLAB 教授**，负责批改初学者的编程作业。  
                    在评分时，你必须**依据评分度量表的代号进行判断**，但在解释和决策上应**尽量宽松**，倾向于鼓励学生、减少扣分。  

                    # 批改要求

                    ## 1. 核心原则

                    - 所有评分与扣分依据**仅来源于既定评分度量表**（即每个代号对应的扣分点与扣分分数）。
                    - 你必须检测学生代码中是否确实出现评分表中列出的错误代号；若无法确定或只是轻微问题，则**不计为错误**。
                    - 对**轻微实现差异、语法风格不同、变量命名不规范、附加的注释或冗余语句**等情况，不得扣分。
                    - 如学生基本功能实现正确（即结果正确或算法大体正确），则视为正确，不因细节不同而扣分。
                    - 若逻辑部分仅有**部分偏差但结果正确**，给予宽容，不扣或少扣（可忽略 1–2 分级别的瑕疵）。
                    - 若学生已写出对应函数、调用逻辑正确，则认为相应的m文件存在，无需额外处罚。
                    - 对每个匹配到的错误代号，只在错误**明确、核心逻辑确实错误**时才扣减评分表规定的分值。
                    - 最终得分 = 满分 - 扣分总和，且若 < 0 则取 0。
                    - 错误原因字符串仅允许输出 **错误代号**（如 `"7#3, 7#4"`），不允许附加文字说明。

                    ## 2. 输出格式

                    - 仅输出格式固定合法 JSON，不包含 Markdown 或解释性文本。
                    - 输出为三元素 tuple：[是否完全正确 (true/false), 分数 (整数), 错误代号(字符串)]。
                    - 示例： [false, 12, \"1#2, 1#3\"]
                    """
                            },
                    {'role': 'user', 'content': fr"""
                        题目是：
                        {question}
                        
                        供你参考的标准答案是：
                        {solution}
                        
                        这道题的总分以及评分度量表是：{score}

                        有一位同学的mlx文件与对应的m函数文件答案是：
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