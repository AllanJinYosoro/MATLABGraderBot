import os
from typing import List, Tuple
import json
from tqdm import tqdm

from llm import Agent

def grade_sequence(grader: Agent, processed_dir: str = "./data/processed") -> None:
    """
    依次为每个学生的每道题打分，并最终计算每个学生的总得分和最终comments

    Args:
        grader: 用以批改的Agent
        processed_dir: 处理后文件输出目录
    """
    # 收集所有任务 (student, qid, answer_path)
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

    total_tokens = 0

    # 学生汇总结果
    student_results = {student: {"total": 0, "comments": []} for student, _, _ in all_tasks}

    with tqdm(total=len(all_tasks), desc="批改进度", unit="题") as pbar:
        for student, qid, answer_path in sorted(all_tasks, key=lambda x: (x[0], int(x[1]))):
            try:
                is_correct, score, reason, tokens = grader.invoke(answer_path, int(qid))
                total_tokens += tokens
            except Exception as e:
                print(f"批改失败 for {student}第{qid}题")
                is_correct, score, reason, tokens = False, 0, f"批改失败: {e}", 0

            # 累加分数
            student_results[student]["total"] += score
            if reason:
                student_results[student]["comments"].append(f"Q{qid}:{reason}\n")

            # 更新进度条
            pbar.set_postfix({
                "学生": student,
                "题目": qid,
                "总tokens": total_tokens
            })
            pbar.update(1)

    # 写入 grade.txt
    for student, result in student_results.items():
        grade_path = os.path.join(processed_dir, student, "grade.txt")
        with open(grade_path, "w", encoding="utf-8") as f:
            f.write(f"{result['total']}\n")
            f.write(" ".join(result["comments"]))
        print(f"学生 {student} 结果已保存到 {grade_path}")