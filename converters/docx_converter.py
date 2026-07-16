import os
from docx import Document
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from docx.text.paragraph import Paragraph
from docx.table import Table
from .base import log

def convert_docx_to_md(docx_path, log_fn=None):

    md_path = docx_path.replace('.docx', '.md')
    try:
        doc = Document(docx_path)
        body = f"# {os.path.basename(docx_path)}\n\n"

        for element in doc.element.body:
            tag_name = element.tag.split('}')[-1]

            if tag_name == 'p':
                para = Paragraph(element, doc._body)
                style = para.style.name if para.style else ''

                if 'Heading' in style:
                    level = style.replace('Heading ', '')
                    if level.isdigit():
                        body += f"{'#' * int(level)} {para.text}\n\n"
                    else:
                        body += f"# {para.text}\n\n"
                elif para.text.strip():
                    body += f"{para.text}\n\n"

            elif tag_name == 'tbl':
                table = Table(element, doc._body)
                md_table = "| " + " | ".join(cell.text for cell in table.rows[0].cells) + " |\n"
                md_table += "| " + " | ".join("---" for _ in table.rows[0].cells) + " |\n"

                for row in table.rows[1:]:
                    md_table += "| " + " | ".join(cell.text for cell in row.cells) + " |\n"

                body += md_table + "\n"

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(body)

        log(f"✓ 转换成功: {docx_path} -> {md_path}", log_fn)
        return md_path, body
    except Exception as e:
        log(f"✗ 转换失败: {docx_path}", log_fn)
        log(f"  错误: {str(e)}", log_fn)
        return None