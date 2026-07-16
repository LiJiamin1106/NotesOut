import os
import html2text
from .base import log


def convert_html_to_md(html_path, log_fn=None):
    md_path = html_path.replace('.html', '.md').replace('.htm', '.md')
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0
        converter.ignore_emphasis = False

        body = f"""# {os.path.basename(html_path)}

{converter.handle(html_content)}"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(body)

        log(f"✓ 转换成功: {html_path} -> {md_path}", log_fn)
        return md_path, body
    except Exception as e:
        log(f"✗ 转换失败: {html_path}", log_fn)
        log(f"  错误: {str(e)}", log_fn)
        return None