import os
import json
from typing import Union, Dict, Tuple
import asyncio
from tqdm import tqdm
from datetime import datetime

from llm import Agent
from .check_file import count_task_number

async def grade_sequence(grader: Agent, processed_dir: str = "./data/processed",
                         overlap_mode: bool = False) -> None:
    """
    依次为每个学生的每道题打分，并最终计算每个学生的总得分和最终comments

    Args:
        grader: 用以批改的Agent
        processed_dir: 处理后文件输出目录
        overlap_mode: 如果为 True，无论 log 中是否已有结果，全部重新批改
    """
    all_tasks = []
    log_paths = {}
    q_num: int = count_task_number(os.path.join("./data/tasks"))

    for student in os.listdir(processed_dir):
        student_path = os.path.join(processed_dir, student)
        if not os.path.isdir(student_path):
            continue

        log_path = os.path.join(student_path, "grade.log")
        if not os.path.exists(log_path):
            grade_log = init_grade_log(student_path, q_num=q_num)
        else:
            try:
                with open(log_path, "r", encoding="utf-8") as f:
                    grade_log = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ {student}/grade.log 格式损坏，重新初始化")
                grade_log = init_grade_log(student_path, q_num=q_num)

        log_paths[student] = (log_path, grade_log)

        for qid, (score, comment) in grade_log.items():
            q_path = os.path.join(student_path, qid)
            answer_path = os.path.join(q_path, "answer.md")
            if os.path.isdir(q_path) and os.path.exists(answer_path):
                # 仅在需要重新批改的情况下建立任务
                if overlap_mode or score is None:
                    all_tasks.append((student, qid, answer_path))

    async def grade_one(student, qid, answer_path):
        nonlocal total_tokens
        try:
            is_correct, score, reason, tokens = await grader.ainvoke(answer_path, int(qid))
            total_tokens += tokens
        except Exception as e:
            is_correct, score, reason, tokens = False, None, f"批改失败: {e}", 0

        log_path, grade_log = log_paths[student]
        grade_log[qid] = [score, reason]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(grade_log, f, ensure_ascii=False, indent=2)
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

    # === 检查缺漏并汇总日志 ===
    warn_log_path = os.path.join(processed_dir, "grade_warning.log")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    missing_records = []

    for student, (log_path, log_obj) in log_paths.items():
        missing = [qid for qid, (score, _) in log_obj.items() if score is None]
        if missing:
            record = f"[{now}] 学生 {student} 未批改题目: {', '.join(missing)}\n"
            missing_records.append(record)

    if missing_records:
        with open(warn_log_path, "a", encoding="utf-8") as f:
            f.writelines(missing_records)
        print(f"⚠️ 已生成警告日志 {warn_log_path}")
    else:
        print("✅ 所有题目均已批改完成。")

    print(f"\n🔹 总 tokens 消耗: {total_tokens}")

def init_grade_log(student_path: str, q_num: int) -> Dict[str, Tuple[Union[int, None], Union[str, None]]]:
    """
    初始化学生的 grade.log 文件。
    格式:
    {
        "1": [null, null],
        "2": [null, null],
        ...
    }
    """
    log_path = os.path.join(student_path, "grade.log")
    grade_log = {str(qid): [None, None] for qid in range(1, q_num + 1)}

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(grade_log, f, ensure_ascii=False, indent=2)

    return grade_log

