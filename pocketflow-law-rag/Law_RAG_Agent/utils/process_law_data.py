import re
import json
from pathlib import Path

def is_excluded_dir(dir_name: str) -> bool:
    """检查是否为需要排除的目录"""
    excluded_dirs = {'__pycache__', '.git', 'node_modules', '.idea', '.vscode'}
    return dir_name.startswith('.') or dir_name in excluded_dirs

def extract_law_structure(content: str) -> dict:
    """
    从法律文件内容中提取结构化数据
    
    返回格式:
    {
        "法律法规名": {
            "第一章": {
                "第一条": "内容",
                "第二条": "内容",
                ...
            },
            "第二章": {
                ...
            },
            ...
        }
    }
    """
    # 提取法律名称
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    law_name = title_match.group(1) if title_match else "未知法律"
    
    result = {law_name: {}}
    
    # 按行分割内容
    lines = content.split('\n')
    
    current_chapter = None
    current_article = None
    article_content = []
    
    for line in lines:
        line = line.strip()
        
        # 匹配章节标题 (## 标题)
        chapter_match = re.match(r'^##\s+(.+)$', line)
        if chapter_match:
            # 保存上一条的内容
            if current_chapter and current_article:
                if current_article not in result[law_name][current_chapter]:
                    result[law_name][current_chapter][current_article] = ""
                result[law_name][current_chapter][current_article] = "\n".join(article_content).strip()
                article_content = []
            
            current_chapter = chapter_match.group(1)
            if current_chapter not in result[law_name]:
                result[law_name][current_chapter] = {}
            current_article = None
            continue
        
        # 匹配条款 (第X条)
        article_match = re.match(r'^第([一二三四五六七八九十百千万\d]+)条[：:]?\s*(.*)$', line)
        if article_match:
            # 保存上一条的内容
            if current_chapter and current_article:
                if current_article not in result[law_name][current_chapter]:
                    result[law_name][current_chapter][current_article] = ""
                result[law_name][current_chapter][current_article] = "\n".join(article_content).strip()
                article_content = []
            
            # 开始新条款
            article_num = article_match.group(1)
            current_article = f"第{article_num}条"
            article_content = [article_match.group(2)] if article_match.group(2) else []
            continue
        
        # 如果有当前章节和条款，添加内容
        if current_chapter and current_article and line and not line.startswith('#'):
            article_content.append(line)
    
    # 保存最后一条的内容
    if current_chapter and current_article:
        if current_article not in result[law_name][current_chapter]:
            result[law_name][current_chapter][current_article] = ""
        result[law_name][current_chapter][current_article] = "\n".join(article_content).strip()
    
    return result

def process():
    root_path = Path(__file__).parent.parent / "Laws"
    output_path = Path(__file__).parent.parent / "database" / "laws"
    
    # 确保输出目录存在
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 遍历所有的md文件，读取内容
    for category_dir in root_path.iterdir():
        if not category_dir.is_dir() or is_excluded_dir(category_dir.name):
            continue
            
        print(f"处理目录: {category_dir.name}")
        category_output_path = output_path / f"{category_dir.name}.json"
        category_data = {}
        
        for md_file in category_dir.glob("*.md"):
            if md_file.name == "_index.md":
                continue
                
            print(f"  找到文件: {md_file}")
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取结构化数据
                structured_data = extract_law_structure(content)
                
                # 检查是否能成功结构化
                can_structure = False
                for law_name, chapters in structured_data.items():
                    for chapter_name, articles in chapters.items():
                        if articles:  # 如果章节下有条款
                            can_structure = True
                            break
                    if can_structure:
                        break
                
                if can_structure:
                    # 合并到分类数据中
                    category_data.update(structured_data)
                    print(f"    成功结构化: {law_name}")
                else:
                    print(f"    跳过文件，无法结构化: {md_file.name}")
                    
            except Exception as e:
                print(f"    处理文件出错: {e}")
        
        # 保存分类数据到JSON文件
        if category_data:
            with open(category_output_path, 'w', encoding='utf-8') as f:
                json.dump(category_data, f, ensure_ascii=False, indent=2)
            print(f"  已保存到: {category_output_path}")

if __name__ == "__main__":
    process()
