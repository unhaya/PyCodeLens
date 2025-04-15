# simple_json_converter.py

import json
import os

def text_to_json_structure(text_content):
    """テキスト形式の解析結果をJSON構造に変換する"""
    result = {
        "directory_structure": [],
        "classes": [],
        "functions": [],
        "imports": []
    }
    
    current_section = None
    current_class = None
    
    # 行ごとに解析
    for line in text_content.split('\n'):
        line = line.rstrip()
        
        # セクションヘッダーの検出
        if line.startswith('# '):
            section_name = line[2:].lower()
            if 'ディレクトリ' in section_name:
                current_section = 'directory'
            elif 'クラス' in section_name:
                current_section = 'classes'
            elif '関数' in section_name:
                current_section = 'functions'
            elif 'インポート' in section_name:
                current_section = 'imports'
            else:
                current_section = None
            continue
            
        # 各セクションごとの処理
        if current_section:
            if current_section == 'directory':
                result["directory_structure"].append(line)
            elif current_section == 'imports':
                result["imports"].append(line)
            elif current_section == 'classes':
                # クラス定義の解析
                if line.startswith('class '):
                    class_name = line[6:].split('(')[0].split(':')[0].strip()
                    current_class = {"name": class_name, "methods": []}
                    result["classes"].append(current_class)
                elif line.startswith('    def ') and current_class:
                    method_name = line.strip()[4:].split('(')[0]
                    current_class["methods"].append(method_name)
            elif current_section == 'functions':
                if line.startswith('def '):
                    func_name = line[4:].split('(')[0]
                    result["functions"].append(func_name)
    
    return result

def save_as_json(data, output_path):
    """データをJSONファイルとして保存する"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return f"JSONファイルを保存しました: {output_path}"