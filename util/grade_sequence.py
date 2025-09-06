import os
from typing import List, Tuple
import asyncio
from tqdm import tqdm

from llm import Agent

async def grade_sequence(grader: Agent, processed_dir: str = "./data/processed") -> None:
    """
    依次为每个学生的每道题打分，并最终计算每个学生的总得分和最终comments

    Args:
        grader: 用以批改的Agent
        processed_dir: 处理后文件输出目录
    """
    all_tasks = []
    for student in os.listdir(processed_dir):
        student_path = os.path.join(processed_dir, student)
        if not os.path.isdir(student_path):
            continue
        for qid in os.listdir(student_path):
            q_path = os.path.join(student_path, qid)
            answer_path = os.path.join(q_path, "answer.md")
            if os.path.isdir(q_path) and os.path.exists(answer_path):
                all_tasks.append((student, qid, answer_path))

    async def grade_one(student, qid, answer_path):
        nonlocal total_tokens
        try:
            is_correct, score, reason, tokens = await grader.ainvoke(answer_path, int(qid))
            total_tokens += tokens
        except Exception as e:
            is_correct, score, reason, tokens = False, 0, f"批改失败: {e}", 0

        return student, qid, score, reason
    
    tasks = [grade_one(s, q, a) for s, q, a in all_tasks]
    total_tokens = 0
    student_results = {student: {"total": 0, "comments": []} for student, _, _ in all_tasks}

    with tqdm(total=len(all_tasks), desc="批改进度", unit="题") as pbar:
        for coro in asyncio.as_completed(tasks):
            student, qid, score, reason = await coro
            student_results[student]["total"] += score
            if reason:
                student_results[student]["comments"].append(f"Q{qid}:{reason}\n")
            pbar.update(1)

    # 写入 grade.txt
    for student, result in student_results.items():
        grade_path = os.path.join(processed_dir, student, "grade.txt")
        sorted_comments = sorted(
            result["comments"],
            key=lambda c: int(c.split(":")[0][1:])  # "Q12:..." → 12
        )
        with open(grade_path, "w", encoding="utf-8") as f:
            f.write(f"{result['total']}\n")
            f.write(" ".join(sorted_comments))
        print(f"学生 {student} 结果已保存到 {grade_path}")

