import asyncio

from aiolimiter import AsyncLimiter

from util.process_raw import process_raw
from llm.Agent import Agent
from util.grade_sequence import grade_sequence

#QWEN official model: Agent(model_name='qwen-flash', base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')

process_raw()
rate_limit = AsyncLimiter(500, 60) #POE API Requests are rate-limited to 500 requests per minute per user

grader = Agent(model_name='Qwen3-235B-2507-FW', base_url='https://api.poe.com/v1', rate_limit=rate_limit)
asyncio.run(grade_sequence(grader=grader))