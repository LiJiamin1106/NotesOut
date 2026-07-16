import os
from converters import *


def convert_files_to_md(file_paths, log_fn=None):
    md_contents = []
    for idx, file_path in enumerate(file_paths, 1):
        filename = os.path.basename(file_path)
        if file_path.endswith('.md'):
            log(f"[{idx}/{len(file_paths)}] 读取: {filename}", log_fn)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                md_contents.append({"filename": filename, "content": content})
                log(f"✓ 已读取: {filename}", log_fn)
            except Exception as e:
                log(f"✗ 读取失败: {filename} - {str(e)}", log_fn)
                raise RuntimeError(f"文件读取失败: {filename} - {str(e)}")
        elif file_path.endswith('.ipynb'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_ipynb_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        elif file_path.endswith('.py'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_py_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        elif file_path.endswith('.docx'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_docx_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        elif file_path.endswith('.xlsx'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_xlsx_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        elif file_path.endswith('.txt'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_txt_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        elif file_path.endswith('.html') or file_path.endswith('.htm'):
            log(f"[{idx}/{len(file_paths)}] 转换: {filename}", log_fn)
            result = convert_html_to_md(file_path, log_fn=log_fn)
            if result is None:
                raise RuntimeError(f"文件转换失败: {filename}")
            md_path, body = result
            md_contents.append({"filename": os.path.basename(md_path), "content": body})
        else:
            log(f"⚠ 跳过不支持的文件: {filename}", log_fn)
            continue
    return md_contents


def main():
    current_dir = os.getcwd()
    ipynb_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.ipynb')]
    py_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.py') and f != os.path.basename(__file__)]
    docx_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.docx')]
    xlsx_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.xlsx')]
    txt_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.txt')]
    html_files = [os.path.join(current_dir, f) for f in os.listdir(current_dir) if f.endswith('.html') or f.endswith('.htm')]

    all_files = ipynb_files + py_files + docx_files + xlsx_files + txt_files + html_files

    if not all_files:
        print("未找到任何.ipynb、.py、.docx、.xlsx、.txt或.html文件")
        return

    print(f"找到 {len(all_files)} 个文件，开始转换...\n")

    try:
        md_contents = convert_files_to_md(all_files)
        print(f"\n转换完成！成功: {len(md_contents)}/{len(all_files)}")
    except RuntimeError as e:
        print(f"\n转换失败: {e}")


if __name__ == '__main__':
    main()