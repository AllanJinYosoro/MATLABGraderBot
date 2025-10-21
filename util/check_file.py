import os
from typing import Union

def check_process_correctness(student_name: str) -> bool:
    raw_dir = os.path.join("./data/raw", student_name)
    processed_dir = os.path.join("./data/processed", student_name)
    tasks_dir = "./data/tasks"

    return all([
        is_only_one_mlx(raw_dir=raw_dir),
        is_task_number_right(processed_dir=processed_dir, tasks_dir=tasks_dir),
        do_all_contain_answer_file(processed_dir=processed_dir)
    ])

def is_only_one_mlx(raw_dir:  Union[str, os.PathLike]) -> bool:
    mlx_files = [file for file in os.listdir(raw_dir) if file.endswith('mlx')]
    return len(mlx_files) == 1

def is_task_number_right(processed_dir:  Union[str, os.PathLike], tasks_dir:  Union[str, os.PathLike]) -> bool:
    """
    Check whether the task dir number of processed dir equals to that of tasks dir
    """
    def count_task_number(path) -> int:
        dirs = {int(d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d.isdigit()}
        if not dirs: return 0
        return min(len(dirs),max(dirs))
    
    return count_task_number(processed_dir) == count_task_number(tasks_dir)

def do_all_contain_answer_file(processed_dir:  Union[str, os.PathLike]) -> bool:
    return all(
        os.path.isfile(os.path.join(processed_dir, d, "answer.md"))
        for d in os.listdir(processed_dir)
        if os.path.isdir(os.path.join(processed_dir, d)) and d.isdigit()
    )