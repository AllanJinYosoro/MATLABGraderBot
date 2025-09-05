from util.process_raw import process_raw
from llm.Agent import Agent
from util.grade_sequence import grade_sequence


# process_raw()
grader = Agent()
grade_sequence(grader=grader)