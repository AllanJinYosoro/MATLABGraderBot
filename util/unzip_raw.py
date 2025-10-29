import os
import zipfile
import rarfile
rarfile.UNRAR_TOOL = r".\UnRAR.exe"
import shutil
from datetime import datetime

def unzip_and_flatten(archive_path: str, log_path: str, processed_dir: str) -> None:
    """
    解压并整理结构，支持 zip / rar。
    """
    if not os.path.isfile(archive_path):
        print(f"Error: {archive_path} 不存在或不是文件。")
        return

    archive_dir = os.path.dirname(archive_path)
    archive_name = os.path.splitext(os.path.basename(archive_path))[0]
    extract_dir = os.path.join(archive_dir, archive_name)

    # Step 0: 检查目录是否存在
    if os.path.exists(extract_dir):
        os.remove(archive_path)
        print(f"🗑️ 已删除原始压缩文件（解压目录已存在）: {archive_path}")
        return

    # Step 1: 解压
    try:
        extract_archive(archive_path, extract_dir)
    except Exception as e:
        print(f"❌ 解压失败: {archive_path} - {e}")
        return
    print(f"✅ 已解压: {extract_dir}")

    # Step 2: 重命名文件夹
    new_name = archive_name.split('_', 1)[0]
    new_dir = os.path.join(archive_dir, new_name)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.rename(extract_dir, new_dir)
    os.makedirs(os.path.join(processed_dir, new_name), exist_ok=True)
    print(f"✅ 已重命名为: {new_dir}")

    # Step 3: 调整文件结构
    flatten_directory(new_dir, log_path, archive_name)

    # Step 4: 删除原始压缩包
    os.remove(archive_path)
    print(f"🗑️ 已删除原始压缩文件: {archive_path}")


def extract_archive(archive_path: str, extract_dir: str) -> None:
    """
    根据文件类型自动选择解压方法（目前支持 zip 和 rar）。
    """
    ext = os.path.splitext(archive_path)[1].lower()

    if ext == ".zip":
        with zipfile.ZipFile(archive_path, 'r') as zf:
            zf.extractall(extract_dir)
    elif ext == ".rar":
        with rarfile.RarFile(archive_path, 'r') as rf:
            rf.extractall(extract_dir)
    else:
        raise ValueError(f"🛑 不支持的文件类型: {ext}")
    
def flatten_directory(target_dir: str, log_path: str, zip_name: str) -> None:
    """
    处理解压后的目录结构：
    - 删除 __MACOSX
    - 若只有一个子文件夹，则向上提取内容
    - 若多个子文件夹，则记录警告
    """
    macosx_path = os.path.join(target_dir, "__MACOSX")
    if os.path.exists(macosx_path):
        shutil.rmtree(macosx_path)

    subitems = [f for f in os.listdir(target_dir)
                if os.path.isdir(os.path.join(target_dir, f))]

    if len(subitems) == 0:
        return  # 没有子目录，结构已平
    elif len(subitems) == 1:
        subfolder = os.path.join(target_dir, subitems[0])
        for item in os.listdir(subfolder):
            shutil.move(os.path.join(subfolder, item), target_dir)
        os.rmdir(subfolder)
        print(f"✅ 已移动内容并删除子文件夹: {subitems[0]}")
    else:
        warning_msg = (f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ⚠️ {zip_name}: "
                       f"子文件夹数量不是1（共有 {len(subitems)} 个）\n")
        print(warning_msg.strip())
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(warning_msg)


if __name__ == "__main__":
    # 示例用法（请根据需要修改路径）
    zip_file_path = r"data\raw\522111910154郭晓磊_423060_11838672_hw1.zip"
    log_file_path = r"data\raw\unzip_warnings.log"
    unzip_and_flatten(zip_file_path, log_file_path)