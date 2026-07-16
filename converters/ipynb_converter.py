import os
from nbconvert import MarkdownExporter
import nbformat
from .base import log

def convert_ipynb_to_md(ipynb_path, log_fn=None):
    md_path = ipynb_path.replace('.ipynb', '.md')
    try:
        with open(ipynb_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)

        exporter = MarkdownExporter()
        body, resources = exporter.from_notebook_node(nb)

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(body)

        log(f"✓ 转换成功: {ipynb_path} -> {md_path}", log_fn)
        return md_path, body
    except Exception as e:
        log(f"✗ 转换失败: {ipynb_path}", log_fn)
        log(f"  错误: {str(e)}", log_fn)
        return None