import os
from .base import log


def convert_py_to_md(py_path, log_fn=None):
    md_path = py_path.replace('.py', '.md')
    try:
        with open(py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        body = f"""# {os.path.basename(py_path)}

```python
{content}
```
"""

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(body)

        log(f"✓ 转换成功: {py_path} -> {md_path}", log_fn)
        return md_path, body
    except Exception as e:
        log(f"✗ 转换失败: {py_path}", log_fn)
        log(f"  错误: {str(e)}", log_fn)
        return None