# NotesOut - 学习笔记生成工具

## 项目概述

NotesOut 是一款基于 LLM 的学习笔记生成工具，支持将多种格式的文件（Jupyter Notebook、Python、Word、Excel、Markdown、Text、HTML）转换为 Markdown，并调用大语言模型生成高质量的阶段性学习笔记。

## 设计思路

### 核心架构

项目采用**模块化架构**设计，将功能划分为三个独立模块：

```
┌─────────────────────────────────────────────────────────────┐
│                     GUI 层 (gui.py)                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ 文件拖拽区    │  │ API 配置区   │  │ 运行日志区   │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
└─────────┼────────────────┼────────────────┼─────────────────┘
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              convert_all.py                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  convert_files_to_md(file_paths, log_fn)              │  │
│  │  ← GUI/CLI 共用的文件转换入口函数                         │  │  
│  └─────────────────────┬─────────────────────────────────┘  │
│                        ▼                                    │
┌─────────────────────────────────────────────────────────────┐
│                   converters/ 包                            │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐    │
│  │ ipynb     │ │ py        │ │ docx      │ │ xlsx      │    │
│  │ converter │ │ converter │ │ converter │ │ converter │    │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘    │
│  ┌───────────┐ ┌───────────┐       │             │          │
│  │ txt       │ │ html      │       │             │          │
│  │ converter │ │ converter │       │             │          │
│  └─────┬─────┘ └─────┬─────┘       │             │          |
│        └─────────────┴─────┬───────┴─────────────┘          │
│                            ▼                                │
│                    base.py (log 函数)                        │
└────────────────────────────┬────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                 generate_notes.py                           │
│  ┌───────────────────┐  ┌───────────────────┐               │
│  │    build_prompt   │  │    call_llm_api   │               │
│  │  (提示词构建)       │  │  (API 调用)       │               │
│  └─────────┬─────────┘  └─────────┬─────────┘               │
└────────────┼──────────────────────┼─────────────────────────┘
             ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   API 调用层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ SiliconFlow │  │  DeepSeek   │  │   ZhipuAI   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **单一职责**：每个转换器只负责一种文件格式的转换
2. **可扩展性**：支持轻松添加新的文件格式转换器和模型供应商
3. **线程安全**：UI 操作与耗时任务分离，避免界面冻结
4. **用户友好**：提供可视化反馈（进度条、日志、弹窗）
5. **代码复用**：`convert_files_to_md` 函数同时被 CLI 和 GUI 复用，通过 `log_fn` 回调实现日志统一

### 模块依赖关系

```
gui.py
  ├── from converters import log
  ├── from convert_all import convert_files_to_md
  └── from generate_notes import build_prompt, call_llm_api

convert_all.py
  ├── convert_files_to_md(file_paths, log_fn)  ← 核心转换函数（GUI/CLI共用）
  └── from converters import *

converters/
  ├── __init__.py    ← 统一导出所有转换器
  ├── base.py        ← log 函数（CLI/GUI共用）
  ├── ipynb_converter.py
  ├── py_converter.py
  ├── docx_converter.py
  ├── xlsx_converter.py
  ├── txt_converter.py
  └── html_converter.py

generate_notes.py  ← 核心逻辑模块（提示词构建、LLM API调用）
  └── from converters.base import log
```

### 统一日志机制

所有转换器和核心函数均支持可选的 `log_fn` 回调参数：

```python
def log(msg, log_fn=None):
    """统一日志输出：CLI 使用 print，GUI 传入回调函数"""
    if log_fn:
        log_fn(msg)
    else:
        print(msg)
```

## 支持的文件格式

| 文件格式 | 扩展名 | 转换方式 | 依赖库 |
|----------|--------|----------|--------|
| Jupyter Notebook | `.ipynb` | nbconvert 转换 | `nbconvert`, `nbformat` |
| Python | `.py` | 封装为代码块 | 内置 |
| Word | `.docx` | 提取段落和表格 | `python-docx` |
| Excel | `.xlsx` | 转换为 Markdown 表格 | `openpyxl` |
| Markdown | `.md` | 直接读取 | 内置 |
| Text | `.txt` | 直接读取 | 内置 |
| HTML | `.html`, `.htm` | html2text 转换 | `html2text` |

> **注意**：Excel 仅支持 `.xlsx` 格式，不支持旧版 `.xls` 格式。

## 工作流程

### 文件处理流程

```
用户上传文件 (.ipynb / .py / .md / .docx / .xlsx / .txt / .html)
        │
        ▼
┌──────────────────────┐
│  文件格式校验          │  ← 检查扩展名和文件存在性
│  去重处理             │  ← 避免重复转换
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  convert_files_to_md │  ← 根据文件类型选择对应转换器
│  (GUI/CLI共用)        │  ← 返回文件路径和正文
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  构建 Prompt          │  ← 组织文件列表和内容
│  注入生成要求          │  ← 添加格式、风格约束
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  调用 LLM API         │  ← 根据供应商选择路由
│  流式/同步响应         │  ← 120秒超时
└─────────┬────────────┘
          ▼
┌──────────────────────┐
│  保存学习笔记          │  ← 写入 Markdown 文件
│  通知用户结果          │  ← 弹窗提示保存路径
└──────────────────────┘
```

### GUI 交互流程

```
启动应用
    │
    ▼
展示主界面（拖拽区 + 文件列表 + 配置区 + 日志区）
    │
    ├─[拖拽/添加文件] → 更新文件列表
    │
    ├─[移除/清空文件] → 更新文件列表
    │
    ├─[选择供应商] → 更新配置状态
    │
    ├─[输入 API Key] → 更新配置状态
    │
    └─[点击生成]
          │
          ├─[前置校验] 文件列表非空? API Key 非空?
          │       │
          │       └─[校验失败] 弹窗提示 → 返回
          │
          ├─[UI 状态切换] 按钮禁用 + 进度条启动 + 日志清空
          │
          ├─[后台线程执行] convert_files_to_md → build_prompt → call_llm_api → save_notes
          │
          └─[完成/失败] UI 状态恢复 + 结果通知
```

## 接口说明

### 核心函数接口

#### 1. `convert_files_to_md(file_paths, log_fn=None)`

将文件列表转换为 Markdown 内容列表。（来源：`convert_all.py`，GUI/CLI 共用）

| 参数 | 类型 | 说明 |
|------|------|------|
| `file_paths` | `List[str]` | 待转换的文件路径列表 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `md_contents` | `List[Dict[str, str]]` | 包含 `{"filename": str, "content": str}` 的字典列表 |

**支持的文件类型**：`.ipynb`, `.py`, `.md`, `.docx`, `.xlsx`, `.txt`, `.html`, `.htm`

**调用示例**：
```python
from convert_all import convert_files_to_md

# CLI 模式
md_contents = convert_files_to_md(["file1.ipynb", "file2.py"])

# GUI 模式
md_contents = convert_files_to_md(file_paths, log_fn=gui_log_callback)
```

#### 2. 文件转换器（底层）

以下转换器由 `convert_files_to_md` 内部调用，也可单独使用：

##### `convert_ipynb_to_md(ipynb_path, log_fn=None)`

将 Jupyter Notebook 文件转换为 Markdown 格式。（来源：`converters/ipynb_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `ipynb_path` | `str` | .ipynb 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

##### `convert_py_to_md(py_path, log_fn=None)`

将 Python 文件转换为 Markdown 格式。（来源：`converters/py_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `py_path` | `str` | .py 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

##### `convert_docx_to_md(docx_path, log_fn=None)`

将 Word 文档转换为 Markdown 格式。（来源：`converters/docx_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `docx_path` | `str` | .docx 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

##### `convert_xlsx_to_md(xlsx_path, log_fn=None)`

将 Excel 表格转换为 Markdown 格式。（来源：`converters/xlsx_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `xlsx_path` | `str` | .xlsx 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

##### `convert_txt_to_md(txt_path, log_fn=None)`

将文本文件转换为 Markdown 格式。（来源：`converters/txt_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `txt_path` | `str` | .txt 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

##### `convert_html_to_md(html_path, log_fn=None)`

将 HTML 文件转换为 Markdown 格式。（来源：`converters/html_converter.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `html_path` | `str` | .html 或 .htm 文件的绝对路径 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `(md_path, body)` | `tuple` | 成功时返回 (MD文件路径, 正文内容) |
| `None` | - | 失败时返回 None |

#### 3. `build_prompt(md_contents, custom_prompt=None)`

构建用于 LLM 调用的完整提示词。（来源：`generate_notes.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `md_contents` | `List[Dict[str, str]]` | 包含 filename 和 content 的字典列表 |
| `custom_prompt` | `str` (可选) | 自定义提示词，默认为学习笔记生成指令 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `prompt` | `str` | 完整的提示词文本 |

**输入数据格式**：
```python
md_contents = [
    {"filename": "chapter1.md", "content": "# 第一章..."},
    {"filename": "chapter2.md", "content": "# 第二章..."}
]
```

#### 4. `call_llm_api(prompt, api_provider, api_key, log_fn=None)`

调用指定供应商的 LLM API 生成笔记内容。（来源：`generate_notes.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `prompt` | `str` | 完整的提示词 |
| `api_provider` | `str` | 供应商标识：`siliconflow` / `deepseek` / `zhipu` |
| `api_key` | `str` | API 密钥 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `content` | `str` | LLM 返回的笔记内容 |
| `None` | - | 调用失败时返回 None |

**异常处理**：
- `ValueError`：不支持的 API 提供商
- `RuntimeError`：API 请求失败或返回格式错误

#### 5. `load_all_md_files(directory=None, log_fn=None)`

从指定目录加载所有 Markdown 文件。（来源：`generate_notes.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `directory` | `str` (可选) | 目标目录路径，默认为当前工作目录 |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `md_contents` | `List[Dict[str, str]]` 或 `None` | 文件内容列表，无文件时返回 `None` |
| `md_files` | `List[str]` | 文件名列表 |

#### 6. `save_notes(content, filename="学习笔记.md", log_fn=None)`

将生成的笔记保存到文件。（来源：`generate_notes.py`）

| 参数 | 类型 | 说明 |
|------|------|------|
| `content` | `str` | 笔记内容 |
| `filename` | `str` (可选) | 保存文件名，默认 `学习笔记.md` |
| `log_fn` | `Callable[[str], None]` (可选) | 日志回调函数 |

| 返回值 | 类型 | 说明 |
|--------|------|------|
| `success` | `bool` | 保存成功返回 `True`，失败返回 `False` |

### API 供应商配置

| 供应商 | 标识 | Base URL | 默认模型 |
|--------|------|----------|----------|
| 硅基流动 | `siliconflow` | `https://api.siliconflow.cn/v1/chat/completions` | `Qwen/Qwen3-8B` |
| 深度求索 | `deepseek` | `https://api.deepseek.com/v1/chat/completions` | `deepseek-chat` |
| 智谱 AI | `zhipu` | `https://open.bigmodel.cn/api/paas/v4/chat/completions` | `glm-4.7-flash` |

**统一请求格式**：
```json
{
  "model": "<model_name>",
  "messages": [{"role": "user", "content": "<prompt>"}],
  "temperature": 0.7,
  "max_tokens": 32000
}
```

**统一响应格式**：
```json
{
  "choices": [
    {
      "message": {
        "content": "<generated_notes>"
      }
    }
  ]
}
```

### GUI 类接口

#### `NotesOutApp` 类

| 方法 | 说明 |
|------|------|
| `__init__(root)` | 初始化应用，设置窗口属性和状态 |
| `_setup_style()` | 配置 ttk 样式 |
| `_build_ui()` | 构建完整的 UI 布局 |
| `_on_drop(event)` | 处理文件拖拽事件 |
| `_choose_files(event)` | 处理文件选择对话框 |
| `_start_generate()` | 启动笔记生成流程 |
| `_run_generate(files, provider, api_key)` | 后台线程执行生成逻辑 |
| `_log(message)` | 向日志面板输出消息 |

## 文件结构

```
NotesOut/
├── gui.py                      # GUI 主程序
├── convert_all.py              # 文件转换模块（GUI/CLI共用）
│   └── convert_files_to_md()   # ← 核心转换函数
├── generate_notes.py           # 核心逻辑：LLM 调用、提示词构建
├── requirements.txt            # 项目依赖列表
├── NotesOut.bat                # Windows 快捷启动脚本
├── converters/                 # 文件转换器包
│   ├── __init__.py             # 包初始化，统一导出所有转换器
│   ├── base.py                 # 共享工具：log 函数
│   ├── ipynb_converter.py      # .ipynb → .md 转换器
│   ├── py_converter.py         # .py → .md 转换器
│   ├── docx_converter.py       # .docx → .md 转换器
│   ├── xlsx_converter.py       # .xlsx → .md 转换器
│   ├── txt_converter.py        # .txt → .md 转换器
│   └── html_converter.py       # .html → .md 转换器
└── __pycache__/                # Python 缓存目录（自动生成）
```

> **架构说明**：`gui.py` 从 `convert_all` 导入 `convert_files_to_md` 函数，该函数内部调用 `converters/` 包中的各个转换器，通过统一的 `log_fn` 回调支持 CLI 和 GUI 两种模式。

## 运行方式

### 环境准备

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境（Windows PowerShell）
.venv\Scripts\Activate.ps1

# 激活虚拟环境（Windows CMD）
.venv\Scripts\activate.bat

# 安装依赖
pip install -r requirements.txt
```

### GUI 版本（推荐）

**方式一**：直接运行批处理文件（Windows）

```bash
NotesOut.bat
```

**方式二**：使用命令行运行

```bash
python gui.py
```

### 命令行版本

1. 批量转换文件：
```bash
python convert_all.py
```

2. 生成学习笔记：
```bash
python generate_notes.py
```

## 依赖说明

| 依赖库 | 版本 | 用途 |
|--------|------|------|
| `tkinter` | - | Python 内置，GUI 基础框架 |
| `tkinterdnd2` | 0.3.0+ | 文件拖拽功能支持 |
| `nbformat` | 5.0.0+ | 读取 Jupyter Notebook 文件 |
| `nbconvert` | 7.0.0+ | 将 ipynb 转换为 Markdown |
| `python-docx` | 1.1.0+ | 读取 Word 文档 |
| `openpyxl` | 3.1.0+ | 读取 Excel 表格 |
| `html2text` | 2020.0.0+ | 将 HTML 转换为 Markdown |
| `requests` | 2.0.0+ | HTTP 请求，调用 LLM API |

**安装命令**：
```bash
pip install -r requirements.txt
```

## 扩展指南

### 添加新的文件格式转换器

在 `converters/` 目录下创建新的转换器文件（如 `pdf_converter.py`），实现 `convert_pdf_to_md` 函数：

```python
from .base import log

def convert_pdf_to_md(pdf_path, log_fn=None):
    md_path = pdf_path.replace('.pdf', '.md')
    # ... 转换代码 ...
    return md_path, body
```

然后在 `converters/__init__.py` 中导出新函数：

```python
from .pdf_converter import convert_pdf_to_md

__all__ = [
    # ... 现有导出 ...
    'convert_pdf_to_md'
]
```

最后在 `convert_all.py` 的 `convert_files_to_md` 函数中添加对应的文件类型处理分支。

### 添加新的模型供应商

在 `generate_notes.py` 的 `call_llm_api` 函数中，找到 `providers` 字典，添加新的供应商配置：

```python
providers = {
    # 现有供应商...

    "new_provider": {
        "base_url": "https://api.example.com/v1/chat/completions",
        "model": "model-name",
        "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        "data": {
            "model": "model-name",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 32000
        }
    }
}
```

然后在 `gui.py` 的 `PROVIDERS` 字典中添加 UI 显示名称：

```python
PROVIDERS = {
    # 现有供应商...
    "新供应商名称": "new_provider"
}
```

> **注意**：所有 API 需要兼容 OpenAI 格式（`/v1/chat/completions`）。

---

*NotesOut - 让学习笔记生成更轻松*#   N o t e s O u t 
 
 