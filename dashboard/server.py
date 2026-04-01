#!/usr/bin/env python3
"""
AI Agent 分析工具 - 后端 API 服务器
处理 GitHub 仓库分析请求，调用 Agent 并返回分析结果
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS

# 添加 agent 目录到 Python 路径
AGENT_PATH = Path(__file__).parent.parent / "my-mini-cc-main"
sys.path.insert(0, str(AGENT_PATH))

# 导入 Agent 调用器
from agent_runner import AgentRunner

app = Flask(__name__)
CORS(app)

# 分析结果存储目录
RESULTS_DIR = Path(__file__).parent / "analysis_results"
RESULTS_DIR.mkdir(exist_ok=True)

# 本地代码仓库存储目录
LOCAL_REPOS_DIR = RESULTS_DIR / "local_repos"
LOCAL_REPOS_DIR.mkdir(exist_ok=True)


def validate_github_url(url: str) -> bool:
    """验证 GitHub URL 格式"""
    try:
        parsed = urlparse(url)
        if parsed.netloc not in ['github.com', 'www.github.com']:
            return False
        path_parts = parsed.path.strip('/').split('/')
        return len(path_parts) >= 2
    except Exception:
        return False


def is_local_path(path_str: str) -> bool:
    """检查是否为本地路径"""
    path_str = path_str.strip()

    # 绝对路径 (Windows: C:\... 或 /home/...)
    if os.path.isabs(path_str):
        return True

    # 相对路径 (包含 ./ 或 ../ 或目录名/)
    if path_str.startswith('./') or path_str.startswith('../') or ('/' in path_str and '\\' in path_str):
        return True

    # Windows 风格相对路径 (.\ 或 ..\)
    if path_str.startswith('.\\') or path_str.startswith('..\\'):
        return True

    return False


def validate_local_path(path_str: str) -> tuple[bool, str]:
    """验证本地路径是否有效

    返回: (是否有效, 错误信息/路径说明)
    """
    path_str = path_str.strip()

    try:
        path = Path(path_str)

        # 检查路径是否存在
        if not path.exists():
            return False, f"路径不存在: {path_str}"

        # 检查是否为目录
        if not path.is_dir():
            return False, f"路径不是目录: {path_str}"

        # 检查是否包含代码文件（常见的代码文件扩展名）
        code_extensions = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', '.swift', '.kt', '.scala'}
        has_code = any(file.suffix in code_extensions for file in path.rglob('*') if file.is_file())

        if not has_code:
            return False, f"目录中未找到代码文件: {path_str}"

        return True, str(path.resolve())

    except Exception as e:
        return False, f"无效的路径: {str(e)}"


def validate_input(input_str: str) -> tuple[bool, str, str]:
    """统一验证输入（GitHub URL 或本地路径）

    返回: (是否有效, 类型('github'|'local'), 标准化后的路径或错误信息)
    """
    input_str = input_str.strip()

    # 检查是否为 GitHub URL
    if validate_github_url(input_str):
        return True, 'github', input_str

    # 检查是否为本地路径
    if is_local_path(input_str):
        valid, result = validate_local_path(input_str)
        if valid:
            return True, 'local', result
        else:
            return False, 'error', result

    return False, 'error', f"无效的输入，请输入 GitHub URL 或本地项目路径"


def extract_repo_info(url: str) -> tuple[str, str]:
    """从 GitHub URL 提取 owner 和 repo"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')
    return path_parts[0], path_parts[1]


@app.route('/')
def index():
    """重定向到代码交接助手主页"""
    chat_page_path = RESULTS_DIR.parent / ".superdesign" / "design_iterations" / "chat_y2k_v1.html"
    if chat_page_path.exists():
        return send_file(chat_page_path)
    return "Chat page not found", 404


@app.route('/input')
def input_page():
    """输入页面（保留备用）"""
    input_page_path = RESULTS_DIR.parent / ".superdesign" / "design_iterations" / "input_page_y2k.html"
    if input_page_path.exists():
        return send_file(input_page_path)
    return "Input page not found", 404


# 全局 AgentRunner 实例（保持会话状态）
_agent_runner = None


def get_agent_runner():
    """获取或创建 AgentRunner 实例"""
    global _agent_runner
    if _agent_runner is None:
        _agent_runner = AgentRunner(workdir=AGENT_PATH)
    return _agent_runner


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    聊天 API
    接收用户消息，调用 Agent 进行对话
    """
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': '请提供消息内容'}), 400

    try:
        # 处理特殊命令
        if message == '/reset':
            runner = get_agent_runner()
            runner.reset()
            return jsonify({
                'success': True,
                'response': '✨ **Chat context has been reset.** Starting a fresh conversation!'
            })

        # 使用 Agent 调用器进行聊天
        runner = get_agent_runner()

        def on_status(s: str) -> None:
            # 可以在这里处理状态更新（用于流式响应）
            pass

        result = runner.chat(message)

        return jsonify({
            'success': True,
            'response': result,
            'tokens_used': None  # 可以在后续添加 token 统计
        })

    except Exception as e:
        return jsonify({'error': f'聊天出错: {str(e)}'}), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_repository():
    """
    分析 GitHub 仓库或本地项目
    支持：
    1. GitHub URL (https://github.com/owner/repo)
    2. 本地路径 (绝对路径或相对路径)
    """
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': '请提供 GitHub 仓库 URL 或本地项目路径'}), 400

    # 统一验证输入
    is_valid, input_type, result = validate_input(url)

    if not is_valid:
        return jsonify({'error': result}), 400

    try:
        if input_type == 'github':
            # 处理 GitHub URL
            owner, repo = extract_repo_info(result)
            analysis_id = f"{owner}_{repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_file = RESULTS_DIR / f"{analysis_id}.md"

            # 使用 Agent 调用器进行分析
            runner = AgentRunner(workdir=AGENT_PATH)
            report_content = runner.analyze_repository(result)

            # 保存报告
            output_file.write_text(report_content, encoding='utf-8')

            return jsonify({
                'success': True,
                'analysis_id': analysis_id,
                'message': '分析完成',
                'redirect_url': f'/report/{analysis_id}',
                'input_type': 'github'
            })

        elif input_type == 'local':
            # 处理本地路径
            local_path = Path(result)
            project_name = local_path.name

            # 生成 analysis_id（使用路径哈希避免冲突）
            path_hash = abs(hash(str(local_path)))
            analysis_id = f"local_{project_name}_{path_hash}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            output_file = RESULTS_DIR / f"{analysis_id}.md"

            # 使用 Agent 调用器分析本地路径
            runner = AgentRunner(workdir=AGENT_PATH)
            report_content = runner.analyze_local_path(str(local_path))

            # 保存报告
            output_file.write_text(report_content, encoding='utf-8')

            return jsonify({
                'success': True,
                'analysis_id': analysis_id,
                'message': f'本地项目分析完成: {project_name}',
                'redirect_url': f'/report/{analysis_id}',
                'input_type': 'local',
                'project_name': project_name
            })

    except Exception as e:
        return jsonify({'error': f'分析出错: {str(e)}'}), 500


@app.route('/api/analyze/async', methods=['POST'])
def analyze_repository_async():
    """
    异步分析 GitHub 仓库
    返回任务 ID，客户端可以轮询任务状态
    """
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': '请提供 GitHub 仓库 URL'}), 400

    if not validate_github_url(url):
        return jsonify({'error': '无效的 GitHub URL 格式'}), 400

    owner, repo = extract_repo_info(url)
    analysis_id = f"{owner}_{repo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # 创建任务状态文件
    status_file = RESULTS_DIR / f"{analysis_id}_status.json"
    status_file.write_text(json.dumps({
        'status': 'pending',
        'url': url,
        'created_at': datetime.now().isoformat()
    }))

    # 在后台运行分析任务
    def run_analysis():
        try:
            runner = AgentRunner(workdir=AGENT_PATH)
            report_content = runner.analyze_repository(url)

            output_file = RESULTS_DIR / f"{analysis_id}.md"
            output_file.write_text(report_content, encoding='utf-8')

            status_file.write_text(json.dumps({
                'status': 'completed',
                'url': url,
                'created_at': datetime.now().isoformat()
            }))
        except Exception as e:
            status_file.write_text(json.dumps({
                'status': 'failed',
                'error': str(e),
                'created_at': datetime.now().isoformat()
            }))

    import threading
    thread = threading.Thread(target=run_analysis)
    thread.start()

    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'message': '分析任务已启动',
        'status_url': f'/api/status/{analysis_id}'
    })


@app.route('/api/status/<analysis_id>', methods=['GET'])
def get_analysis_status(analysis_id: str):
    """获取分析任务状态"""
    status_file = RESULTS_DIR / f"{analysis_id}_status.json"

    if not status_file.exists():
        return jsonify({'error': '任务不存在'}), 404

    status_data = json.loads(status_file.read_text())
    return jsonify(status_data)


@app.route('/api/report/<analysis_id>', methods=['GET'])
def get_report(analysis_id: str):
    """获取分析报告内容 - 同时返回原始文本和结构化数据"""
    report_file = RESULTS_DIR / f"{analysis_id}.md"

    if not report_file.exists():
        return jsonify({'error': '报告不存在'}), 404

    content = report_file.read_text(encoding='utf-8')

    # 解析 Markdown 内容为原始 sections
    sections = parse_markdown_sections(content)

    # 解析 Markdown 内容为结构化数据
    structured_data = parse_markdown_to_structured(content)

    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'sections': sections,
        'structured_data': structured_data,
        'raw_content': content
    })


@app.route('/api/download/<analysis_id>', methods=['GET'])
def download_report(analysis_id: str):
    """下载分析报告"""
    report_file = RESULTS_DIR / f"{analysis_id}.md"

    if not report_file.exists():
        return jsonify({'error': '报告不存在'}), 404

    return send_file(
        report_file,
        as_attachment=True,
        download_name=f"{analysis_id}_analysis.md",
        mimetype='text/markdown'
    )


@app.route('/report/<analysis_id>')
def view_report(analysis_id: str):
    """查看分析报告页面"""
    report_page_path = RESULTS_DIR.parent / ".superdesign" / "design_iterations" / "report.html"

    if not report_page_path.exists():
        return "<h1>Report page not found</h1>", 404

    # 返回报告页面
    return send_file(report_page_path)


@app.route('/api/analysis/<analysis_id>/info', methods=['GET'])
def get_analysis_info(analysis_id: str):
    """获取分析项目的信息（用于可视化工具）"""
    report_file = RESULTS_DIR / f"{analysis_id}.md"

    if not report_file.exists():
        return jsonify({'error': '分析不存在'}), 404

    # 尝试从 analysis_id 或文件中提取项目路径信息
    # 对于本地项目，analysis_id 包含路径信息
    if analysis_id.startswith('local_'):
        # 本地项目，从文件内容中提取路径
        content = report_file.read_text(encoding='utf-8')
        import re
        path_match = re.search(r'项目路径[：:]\s*(.+?)(?:\n|$)', content)
        if path_match:
            project_path = path_match.group(1).strip()
        else:
            project_path = ""
        input_type = 'local'
    else:
        # GitHub 项目
        parts = analysis_id.split('_')
        if len(parts) >= 2:
            project_path = f"https://github.com/{parts[0]}/{parts[1]}"
        else:
            project_path = ""
        input_type = 'github'

    # 检查是否有对应的分析元数据文件
    metadata_file = RESULTS_DIR / f"{analysis_id}_meta.json"
    metadata = {}
    if metadata_file.exists():
        try:
            metadata = json.loads(metadata_file.read_text())
        except:
            pass

    return jsonify({
        'success': True,
        'analysis_id': analysis_id,
        'input_type': input_type,
        'project_path': project_path,
        'metadata': metadata
    })


def parse_markdown_sections(content: str) -> dict:
    """
    解析 Markdown 文件，提取各个模块内容
    返回包含六个模块的字典
    """
    sections = {
        'overview': '',
        'directory': '',
        'entrypoints': '',
        'modules': '',
        'dependencies': '',
        'team': ''
    }

    lines = content.split('\n')
    current_section = None
    current_content = []

    # 新的映射关系，支持更多格式
    section_mapping = {
        '项目概述': 'overview',
        '分析完成情况': 'overview',
        '项目核心亮点': 'overview',
        '项目背景与目标': 'overview',

        '目录结构': 'directory',
        '文件组织': 'directory',

        '入口点': 'entrypoints',
        '启动流程': 'entrypoints',

        '核心模块': 'modules',
        '模块分析': 'modules',
        '技术架构': 'modules',

        '依赖关系': 'dependencies',
        '技术栈': 'dependencies',
        '技术依赖': 'dependencies',

        '项目人员': 'team',
        '团队信息': 'team',
        '贡献者': 'team'
    }

    for line in lines:
        # 检测二级标题（## 标题）
        if line.startswith('## '):
            # 保存之前的内容
            if current_section and current_section in section_mapping:
                section_key = section_mapping[current_section]
                # 如果目标section已经有内容，追加内容
                if sections[section_key]:
                    sections[section_key] += '\n\n' + '\n'.join(current_content).strip()
                else:
                    sections[section_key] = '\n'.join(current_content).strip()

            # 开始新章节
            current_section = line[3:].strip()
            current_content = []
        elif current_section and current_section in section_mapping:
            current_content.append(line)
        else:
            # 如果标题不在映射中，收集所有内容到 overview
            if current_section:
                current_content.append(line)

    # 保存最后一个章节
    if current_section and current_section in section_mapping:
        section_key = section_mapping[current_section]
        if sections[section_key]:
            sections[section_key] += '\n\n' + '\n'.join(current_content).strip()
        else:
            sections[section_key] = '\n'.join(current_content).strip()

    # 如果所有section都是空的，把整个内容放到overview
    if all(not sections[key] for key in sections):
        sections['overview'] = content

    return sections


def parse_markdown_to_structured(content: str) -> dict:
    """
    解析 Markdown 内容为结构化 JSON 数据
    用于前端按照六个页面的模板进行动态渲染
    """
    import re

    sections = parse_markdown_sections(content)

    # 解析项目概述
    def parse_overview(text: str) -> dict:
        result = {
            'project_name': '',
            'description': '',
            'subprojects': [],
            'stats': [],
            'scenarios': []
        }

        lines = text.split('\n')
        for i, line in enumerate(lines):
            # 提取项目名称（第一个一级标题）
            if line.startswith('# ') and not result['project_name']:
                result['project_name'] = line[2:].strip()
            # 提取简短描述（通常在开头）
            elif not result['description'] and line.strip() and not line.startswith('#'):
                result['description'] = line.strip()
            # 提取子项目（### 或 - 开头）
            elif line.startswith('### ') or line.startswith('- **'):
                name_match = re.search(r'\*\*(.+?)\*\*|\*\*(.+?)\*\*', line)
                if name_match:
                    name = name_match.group(1) or name_match.group(2)
                    desc = ''
                    if i + 1 < len(lines):
                        desc = lines[i + 1].strip()
                    result['subprojects'].append({'name': name, 'description': desc})

        # 尝试提取统计信息（数字相关）
        stats_match = re.findall(r'(\d+)\s*([\u4e00-\u9fa5a-zA-Z]+)', text)
        if stats_match:
            for num, label in stats_match[:4]:  # 最多4个统计
                result['stats'].append({'value': num, 'label': label})

        return result

    # 解析目录结构
    def parse_directory(text: str) -> dict:
        result = {
            'tree_structure': '',
            'description': '',
            'stats': []
        }

        lines = text.split('\n')
        tree_lines = []
        desc_lines = []

        in_tree = False
        for line in lines:
            # 检测目录树结构（包含 └、├、│ 等字符）
            if any(c in line for c in ['└', '├', '│', '│', '┌', '┐', '┘']):
                in_tree = True
                tree_lines.append(line)
            elif in_tree and line.strip():
                desc_lines.append(line)
            elif line.strip():
                tree_lines.append(line)

        result['tree_structure'] = '\n'.join(tree_lines)
        result['description'] = '\n'.join(desc_lines)

        # 提取统计信息
        stats_match = re.findall(r'(\d+)\s*([\u4e00-\u9fa5a-zA-Z]+)', text)
        if stats_match:
            for num, label in stats_match[:4]:
                result['stats'].append({'value': num, 'label': label})

        return result

    # 解析入口点
    def parse_entrypoints(text: str) -> dict:
        result = {
            'subprojects': [],
            'summary': ''
        }

        lines = text.split('\n')
        current_subproject = None

        for line in lines:
            # 检测子项目标题（### 或 **）
            if line.startswith('### ') or '**' in line:
                if current_subproject:
                    result['subprojects'].append(current_subproject)
                name_match = re.search(r'###\s+(.+?)$|\"\*\*(.+?)\*\*\"|\*\*(.+?)\*\*', line)
                if name_match:
                    name = name_match.group(1) or name_match.group(2) or name_match.group(3)
                    current_subproject = {'name': name.strip(' "\'*'), 'files': []}
            # 检测文件（.py, .js, .go 等）
            elif current_subproject and any(ext in line for ext in ['.py', '.js', '.ts', '.go', '.rs', '.java']):
                file_match = re.search(r'`?([\w\-.]+\.(?:py|js|ts|go|rs|java))`?', line)
                if file_match:
                    filename = file_match.group(1)
                    desc = line.replace(filename, '').strip('`*: -')
                    current_subproject['files'].append({'name': filename, 'description': desc})

        if current_subproject:
            result['subprojects'].append(current_subproject)

        # 提取总结段落
        if '总结' in text or '说明' in text:
            summary_match = re.search(r'(?:总结|说明)[：:]\s*(.+?)(?:\n\n|\n|$)', text, re.DOTALL)
            if summary_match:
                result['summary'] = summary_match.group(1).strip()

        return result

    # 解析核心模块
    def parse_modules(text: str) -> dict:
        result = {
            'subprojects': []
        }

        lines = text.split('\n')
        current_subproject = None
        current_module = None

        for line in lines:
            # 检测子项目标题
            if line.startswith('### ') or line.startswith('## '):
                if current_subproject:
                    if current_module:
                        current_subproject['modules'].append(current_module)
                    result['subprojects'].append(current_subproject)
                name = re.sub(r'^#+\s+', '', line).strip()
                current_subproject = {'name': name, 'modules': []}
                current_module = None
            # 检测模块标题（- ** 或 **开头）
            elif '- **' in line or line.startswith('- '):
                if current_module and current_subproject:
                    current_subproject['modules'].append(current_module)
                module_match = re.search(r'\*\*(.+?)\*\*', line)
                if module_match:
                    module_name = module_match.group(1)
                    # 尝试提取文件名
                    file_match = re.search(r'`([\w\-.]+\.\w+)`', line)
                    filename = file_match.group(1) if file_match else ''
                    current_module = {
                        'name': module_name,
                        'file': filename,
                        'description': '',
                        'features': []
                    }
            # 检测特性列表（- 或 • 开头）
            elif line.strip().startswith('-') and current_module:
                feature = line.strip().lstrip('-*• ').strip()
                if feature:
                    current_module['features'].append(feature)
            # 描述内容
            elif line.strip() and current_module and not line.startswith('#'):
                if current_module['description']:
                    current_module['description'] += ' ' + line.strip()
                else:
                    current_module['description'] = line.strip()

        if current_module and current_subproject:
            current_subproject['modules'].append(current_module)
        if current_subproject:
            result['subprojects'].append(current_subproject)

        return result

    # 解析依赖关系
    def parse_dependencies(text: str) -> dict:
        result = {
            'external_deps': [],
            'internal_deps': [],
            'description': ''
        }

        lines = text.split('\n')
        in_external = False
        in_internal = False

        for line in lines:
            if '外部' in line or 'External' in line:
                in_external = True
                in_internal = False
            elif '内部' in line or 'Internal' in line:
                in_internal = True
                in_external = False
            elif '- **' in line or '`' in line:
                dep_match = re.search(r'\*\*([a-zA-Z0-9_\-]+)\*\*', line)
                if dep_match:
                    name = dep_match.group(1)
                    # 尝试提取版本号
                    version_match = re.search(r'([>==~!][\d.]+|v?\d+\.\d+)', line)
                    version = version_match.group(1) if version_match else ''
                    desc = re.sub(r'\*\*.*?\*\*|`.*?`', '', line).strip(' -:')
                    dep_info = {'name': name, 'version': version, 'description': desc}
                    if in_external:
                        result['external_deps'].append(dep_info)
                    else:
                        result['internal_deps'].append(dep_info)

        return result

    # 解析项目人员
    def parse_team(text: str) -> dict:
        result = {
            'contributors': [],
            'timeline': '',
            'stats': []
        }

        lines = text.split('\n')
        current_contributor = None

        for line in lines:
            # 检测贡献者名称（**开头）
            if '**' in line and any(word in line for word in ['贡献者', '开发者', 'Contributor', 'Developer']):
                if current_contributor:
                    result['contributors'].append(current_contributor)
                name_match = re.search(r'\*\*(.+?)\*\*', line)
                if name_match:
                    name = name_match.group(1)
                    role_match = re.search(r'[（(]?(.+?)[）)]?', line[name_match.end():])
                    role = role_match.group(1) if role_match else '开发者'
                    current_contributor = {'name': name, 'role': role, 'contributions': []}
            # 检测贡献内容（- 开头）
            elif line.strip().startswith('-') and current_contributor:
                contribution = line.strip().lstrip('-*• ').strip()
                if contribution:
                    current_contributor['contributions'].append(contribution)
            # 检测时间线
            elif '时间' in line or 'Timeline' in line or '20' in line:
                result['timeline'] += line + '\n'

        if current_contributor:
            result['contributors'].append(current_contributor)

        # 提取统计信息
        stats_match = re.findall(r'(\d+)\s*([\u4e00-\u9fa5a-zA-Z]+)', text)
        if stats_match:
            for num, label in stats_match[:4]:
                result['stats'].append({'value': num, 'label': label})

        return result

    # 组装所有解析结果
    return {
        'overview': parse_overview(sections.get('overview', '')),
        'directory': parse_directory(sections.get('directory', '')),
        'entrypoints': parse_entrypoints(sections.get('entrypoints', '')),
        'modules': parse_modules(sections.get('modules', '')),
        'dependencies': parse_dependencies(sections.get('dependencies', '')),
        'team': parse_team(sections.get('team', ''))
    }


if __name__ == '__main__':
    print("=" * 60)
    print("  AI Agent 分析工具 - 后端服务器")
    print("=" * 60)
    print(f"服务器地址: http://localhost:5000")
    print(f"Agent 路径: {AGENT_PATH}")
    print(f"结果存储: {RESULTS_DIR}")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
