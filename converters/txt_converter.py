import os
from .base import log


def convert_txt_to_md(txt_path, log_fn=None):
    md_path = txt_path.replace('.txt', '.md')
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        body = f"""# {os.path.basename(txt_path)}

{content}
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(body)

        log(f"✓ 转换成功: {txt_path} -> {md_path}", log_fn)
        return md_path, body
    except Exception as e:
        log(f"✗ 转换失败: {txt_path}", log_fn)
        log(f"  错误: {str(e)}", log_fn)
        return None