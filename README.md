# MATLAB Grader Bot

> 一个基于大语言模型的 MATLAB 自动批改机器人。

## 功能简介

- 自动读取题目与标准答案
- 自动批改学生提交的 `.mlx` 文件
- 根据标准答案与题目分数，给出最终得分与错误原因
- 输出统一的 JSON 格式，便于后续分析与统计

---

## 环境配置

本项目推荐使用 [`uv`](https://github.com/astral-sh/uv) 管理依赖。

### 安装依赖

```bash
# 同步依赖
uv sync
```


### 环境变量管理
本项目通过 `python-dotenv` 加载 API Key，避免将 Key 写死在代码中。

请在项目根目录新建 `.env` 文件，并写入以下内容：

```
OPENAI_API_KEY=your_api_key_here
```
`.env` 文件 不要提交到 Git 仓库，请务必添加到 `.gitignore` 里。

## 数据准备
所有数据存放在 data 文件夹下。

### 题目数据
在 data/tasks/ 文件夹下，每道题建立一个子文件夹，文件夹名为题号（整数）。

例如：第一题为 data/tasks/1/，其中包含：

task_content：题目文本
solution：参考答案（MATLAB 代码）
score：该题分值（整数）
目录结构示例：

```
data/tasks/
├── 1/
│   ├── task_content
│   ├── solution
│   └── score
├── 2/
│   ├── task_content
│   ├── solution
│   └── score
```

### 学生提交
在 data/raw/ 文件夹下，每个学生对应一个子文件夹，名称可为学号或姓名缩写。

每个学生文件夹中 必须仅有一个 .mlx 文件，该文件为该学生的提交。

例如：

```
data/raw/
├── studentA/
│   └── answer.mlx
├── studentB/
│   └── homework.mlx
```

📌 提交文件需参考项目中提供的 template.mlx。

# TODO
1. 增加logger
2. 如果批改错误，则尝试重复批改依次
3. 对图片的多模态识别