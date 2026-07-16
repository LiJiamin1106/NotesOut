import os
import requests
from converters.base import log

def load_all_md_files(directory=None, log_fn=None):
    if directory is None:
        directory = os.getcwd()
    
    md_files = sorted([f for f in os.listdir(directory) if f.endswith('.md')])
    
    if not md_files:
        log("未找到任何.md文件", log_fn)
        return None, []
    
    all_content = []
    for md_file in md_files:
        file_path = os.path.join(directory, md_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            all_content.append({
                'filename': md_file,
                'content': content
            })
            log(f"✓ 已读取: {md_file}", log_fn)
        except Exception as e:
            log(f"✗ 读取失败: {md_file} - {str(e)}", log_fn)
    
    return all_content, md_files


def build_prompt(md_contents, custom_prompt=None):
    if custom_prompt is None:
        custom_prompt = "请基于以下学习资料，帮我生成一份生动有趣的阶段性学习笔记"
    
    file_list = "\n".join([f"- {item['filename']}" for item in md_contents])
    
    content_separator = "\n\n" + "="*80 + "\n\n"
    all_text = content_separator.join([f"【文件: {item['filename']}】\n\n{item['content']}" for item in md_contents])
    
    prompt = f"""{custom_prompt}

资料列表：
{file_list}

资料内容：
{all_text}

请发挥你的专业能力，帮我整理一份高质量的学习笔记。要求：
- 内容要全面，涵盖核心知识点、关键代码和重要概念
- 形式要灵活多样，可以使用思维导图、表格对比、要点清单、代码示例等多种形式
- 语言要通俗易懂，避免过于死板的格式
- 结构要清晰，但不要局限于固定模板，根据内容自由组织
- 代码块要标注正确的语言类型

输出格式：
- 使用Markdown格式
- 标题层级清晰合理
- 可以自由发挥排版风格

开始创作吧！"""
    
    return prompt


def call_llm_api(prompt, api_provider="siliconflow", api_key=None, log_fn=None):
    providers = {
        "siliconflow": {
            "base_url": "https://api.siliconflow.cn/v1/chat/completions",
            "model": "Qwen/Qwen3-8B",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "data": {
                "model": "Qwen/Qwen3-8B",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 32000
            }
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "data": {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 32000
            }
        },
        "zhipu": {
            "base_url": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "model": "glm-4.7-flash",
            "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            "data": {
                "model": "glm-4.7-flash",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 32000
            }
        }
    }
    
    if api_provider not in providers:
        log(f"不支持的API提供商: {api_provider}", log_fn)
        return None
    
    config = providers[api_provider]
    
    try:
        log(f"\n正在调用 {api_provider} API...", log_fn)
        log(f"模型: {config['model']}", log_fn)
        log("请稍候，生成学习笔记需要一些时间...", log_fn)
        
        response = requests.post(
            config['base_url'],
            headers=config['headers'],
            json=config['data'],
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and result['choices']:
                return result['choices'][0]['message']['content']
            else:
                log(f"API返回格式错误: {result}", log_fn)
                return None
        else:
            log(f"API请求失败: {response.status_code}", log_fn)
            log(f"错误信息: {response.text}", log_fn)
            return None
    except requests.exceptions.Timeout:
        log("请求超时，请检查网络连接或增加超时时间", log_fn)
        return None
    except Exception as e:
        log(f"调用失败: {str(e)}", log_fn)
        return None


def save_notes(content, filename="学习笔记.md", log_fn=None):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        log(f"\n✓ 学习笔记已保存到: {filename}", log_fn)
        return True
    except Exception as e:
        log(f"✗ 保存失败: {str(e)}", log_fn)
        return False


def main():
    print("="*60)
    print("          学习笔记生成工具")
    print("="*60)
    
    md_contents, md_files = load_all_md_files()
    
    if not md_contents:
        return
    
    print(f"\n共读取 {len(md_files)} 个文件")
    
    api_key = input("\n请输入您的API密钥: ").strip()
    
    if not api_key:
        print("API密钥不能为空")
        return
    
    api_provider = input("请选择API提供商 (siliconflow/deepseek/zhipu) [默认: siliconflow]: ").strip().lower() or "siliconflow"
    
    prompt = build_prompt(md_contents)
    
    result = call_llm_api(prompt, api_provider, api_key)
    
    if result:
        save_notes(result)
        print("\n" + "="*60)
        print("          生成完成！")
        print("="*60)
    else:
        print("\n生成失败，请检查API密钥和网络连接")


if __name__ == '__main__':
    main()
