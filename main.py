from util.process_raw import process_raw
from llm.Agent import Agent
from util.grade_sequence import grade_sequence

#QWEN official model: Agent(model_name='qwen-flash', base_url='https://dashscope.aliyuncs.com/compatible-mode/v1')

# process_raw()
grader = Agent(model_name='Qwen3-235B-2507-FW', base_url='https://api.poe.com/v1')
grade_sequence(grader=grader)