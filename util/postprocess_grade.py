import os
import json
from datetime import datetime
from typing import Dict, List, Tuple


def join_comments(comments: List[str]) -> str:
    """
    将多个 comment 使用 【, 】 拼接成一句话。
    """
    comments = [c.strip() for c in comments if c and c.strip()]
    return ", ".join(comments) if comments else ""


def load_grade_log(path: str) -> Dict[str, Tuple[int, str]]:
    """
    加载单个学生的 grade.log。
    若文件不存在或损坏，返回空 dict。
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"⚠️ grade.log 格式损坏: {path}")
        return {}


def collect_student_results(processed_dir: str, total_questions: int):
    """
    遍历所有学生目录，检查批改完成情况，汇总成绩与评论。
    """
    all_students = [d for d in os.listdir(processed_dir)
                    if os.path.isdir(os.path.join(processed_dir, d))
                    and not d.startswith(".") and d != "example"]

    warning_students = []
    results = []
    warn_log_path = os.path.join(processed_dir, "grade_warning.log")

    print(f"\n📋 正在检查 {len(all_students)} 位学生的批改结果...\n")

    for idx, student in enumerate(sorted(all_students), start=1):
        log_path = os.path.join(processed_dir, student, "grade.log")
        grade_log = load_grade_log(log_path)

        if not grade_log:
            warning_students.append(student)
            total_score = 0
            comments = ["未发现 grade.log"]
        else:
            scores = []
            comments = []

            for qid, (score, comment) in grade_log.items():
                scores.append(score if isinstance(score, (int, float)) and score is not None else 0)
                if comment:
                    comments.append(f"Q{qid}:{comment}")

            total_score = sum(scores)

            missing = [qid for qid, (score, _) in grade_log.items() if score is None]
            if missing:
                warning_students.append(student)
                comments.append(f"[未批改题目: {', '.join(missing)}]")

        results.append({
            "Index": idx,
            "Name": student,
            "Score": total_score,
            "Comments": join_comments(comments),
        })

    # 输出警告日志
    if warning_students:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(warn_log_path, "a", encoding="utf-8") as f:
            header = f"\n[{now}] 以下学生存在未批改的题目或损坏的日志：\n"
            f.write(header)
            f.writelines([f"- {name}\n" for name in warning_students])
        print(f"⚠️ 发现未批改记录，请查看 {warn_log_path}")
    else:
        print("✅ 所有学生的题目均已批改完成。")

    return results


def export_summary(results: List[Dict], output_path: str = "./processed/summary.csv"):
    """
    将结果导出为 CSV 文件。
    """
    import csv
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "学生姓名", "总分", "扣分点"])
        for r in results:
            writer.writerow([r["Index"], r["Name"], r["Score"], r["Comments"]])
    print(f"\n📄 已生成汇总表: {output_path}")