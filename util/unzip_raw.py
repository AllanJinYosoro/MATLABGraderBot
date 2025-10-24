import os
import zipfile
import shutil
from datetime import datetime

def unzip_and_flatten(zip_path: str, log_path: str, processed_dir: str) -> None:
    """
    解压缩指定路径的 zip 文件，并调整目录结构。

    步骤：
    0. 检查解压目录是否已存在，若存在则删除原 zip 文件并退出。
    1. 将 zip 文件解压到与 zip 名称相同的文件夹中。
    2. 将解压后的文件夹重命名为第一个下划线 (_) 之前的部分。并在processed文件夹中新建同名文件夹
    3. 在解压目录内：
       - 如果没有子文件夹，则完成过程
       - 如果只有一个子文件夹，则将其内部文件（孙子文件）移动到解压目录中，并删除孙子文件夹。
       - 如果有多个子文件夹，则打印警告信息，并将警告追加写入指定 log 文件（含时间戳）。
    4. 如果整个过程正常完成，则删除原始 zip 文件。

    参数：
        zip_path (str): zip 文件的完整路径。
        log_path (str): 日志文件的路径，用于记录警告。
    """
    if not os.path.isfile(zip_path):
        print(f"Error: {zip_path} 不存在或不是文件。")
        return

    zip_dir = os.path.dirname(zip_path)
    zip_name = os.path.splitext(os.path.basename(zip_path))[0]
    extract_dir = os.path.join(zip_dir, zip_name)

    # step 0: 检查加压缩文件夹是否已经存在
    if os.path.exists(extract_dir):
        os.remove(zip_path)
        print(f"🗑️ 已删除原始 zip 文件: {zip_path}")
        return

    # Step 1: 解压 zip 文件
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)
    print(f"✅ 已解压: {extract_dir}")

    # Step 2: 重命名文件夹为第一个下划线前部分
    new_name = zip_name.split('_', 1)[0]
    new_dir = os.path.join(zip_dir, new_name)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.rename(extract_dir, new_dir)
    os.makedirs(os.path.join(processed_dir, new_name), exist_ok=True)
    print(f"✅ 已重命名为: {new_dir}")

    # Step 3: 处理内部结构
    ## 主动忽略并删除 macOS 自动生成的 "__MACOSX" 文件夹
    macosx_path = os.path.join(new_dir, "__MACOSX")
    if os.path.exists(macosx_path) and os.path.isdir(macosx_path):
        shutil.rmtree(macosx_path)
    subitems = [f for f in os.listdir(new_dir) if os.path.isdir(os.path.join(new_dir, f))]

    if len(subitems) == 0:
        # Step 4: 正常完成后删除 zip 文件
        os.remove(zip_path)
        print(f"🗑️ 已删除原始 zip 文件: {zip_path}")
    elif len(subitems) == 1:
        subfolder = os.path.join(new_dir, subitems[0])
        for item in os.listdir(subfolder):
            shutil.move(os.path.join(subfolder, item), new_dir)
        os.rmdir(subfolder)
        print(f"✅ 已移动内容并删除子文件夹: {subitems[0]}")
        # Step 4: 正常完成后删除 zip 文件
        os.remove(zip_path)
        print(f"🗑️ 已删除原始 zip 文件: {zip_path}")
    else:
        warning_msg = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ⚠️ {zip_name}: 子文件夹数量不是1（共有 {len(subitems)} 个）\n"
        print(warning_msg.strip())
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(warning_msg)


if __name__ == "__main__":
    # 示例用法（请根据需要修改路径）
    zip_file_path = r"data\raw\522111910154郭晓磊_423060_11838672_hw1.zip"
    log_file_path = r"data\raw\unzip_warnings.log"
    unzip_and_flatten(zip_file_path, log_file_path)