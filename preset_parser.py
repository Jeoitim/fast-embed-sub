import os
import re
import yaml

class PresetParser:
    @staticmethod
    def parse_preset(file_path):
        """
        解析预设文件。支持传统命令行预设与新型 Vpy 预设。
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"预设文件不存在: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        lines = content.splitlines()
        
        # 1. 提取首行说明
        desc = ""
        if lines and lines[0].strip().startswith('#'):
            desc = lines[0].strip().lstrip('#').strip()
            
        # 2. 判断是否为 Vpy 预设
        is_vpy = '$vpy-start' in content
        
        metadata = {}
        vpy_template = ""
        cmd_template = ""
        
        if is_vpy:
            # 提取 YAML 元数据
            custom_match = re.search(r'\$custom-start(.*?)\$custom-end', content, re.DOTALL)
            if custom_match:
                try:
                    metadata = yaml.safe_load(custom_match.group(1)) or {}
                except Exception as e:
                    print(f"解析 YAML 元数据失败: {e}")
                    
            # 提取 Vpy 模板
            vpy_match = re.search(r'\$vpy-start(.*?)\$vpy-end', content, re.DOTALL)
            if vpy_match:
                vpy_template = vpy_match.group(1).strip()
                
            # 提取命令行模板
            remaining = content
            remaining = re.sub(r'\$custom-start.*?\$custom-end', '', remaining, flags=re.DOTALL)
            remaining = re.sub(r'\$vpy-start.*?\$vpy-end', '', remaining, flags=re.DOTALL)
            
            for line in remaining.splitlines():
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#') and not line_stripped.startswith('$'):
                    cmd_template = line_stripped
                    break
        else:
            # 传统命令行预设：第一行之后的所有非空且非注释行拼接为命令模板
            cmd_lines = []
            for line in lines[1:]:
                line_stripped = line.strip()
                if line_stripped and not line_stripped.startswith('#'):
                    cmd_lines.append(line_stripped)
            cmd_template = " ".join(cmd_lines)
            
        return {
            "is_vpy": is_vpy,
            "desc": desc,
            "metadata": metadata, # 内部包含 parameters 列表
            "vpy_template": vpy_template,
            "cmd_template": cmd_template
        }

    @staticmethod
    def compile_vpy_script(template, values):
        """
        编译 Vpy 模板，将 {parameter_id} 替换为用户输入的实际 Python 类型值或系统绝对路径。
        """
        path_keys = {"input_v", "input_s", "preset_dir", "components_dir", "preset_components_dir"}
        
        def replace_placeholder(match):
            param_id = match.group(1).strip()
            # 如果占位符里有默认提示/类型，例如 {denoise_sigma:1.5}，只取前半段作为 ID
            if ":" in param_id:
                param_id = param_id.split(":", 1)[0].strip()
                
            if param_id in values:
                val = values[param_id]
                if val is None:
                    return "None"
                
                # 如果是路径类参数，模板中已写在双引号内，直接返回斜杠转义后的 raw 字符串
                if param_id in path_keys:
                    return str(val).replace("\\", "/")
                
                # 其它类型处理
                if isinstance(val, bool):
                    return "True" if val else "False"
                elif isinstance(val, str):
                    # 对普通字符串参数进行转义，并包上双引号
                    escaped_str = val.replace('\\', '\\\\').replace('"', '\\"')
                    return f'"{escaped_str}"'
                else:
                    return str(val)
            return match.group(0)
            
        return re.sub(r'\{([^}]+)\}', replace_placeholder, template)
