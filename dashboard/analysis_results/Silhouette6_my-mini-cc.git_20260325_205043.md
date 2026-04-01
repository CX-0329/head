完成! 我已经使用 project-code-understanding 技能系统地分析了 GitHub 仓库 https://github.com/Silhouette6/my-mini-cc.git。

## 分析总结

该项目是一个基于 Google ADK 的模块化 AI 编码智能体,具有以下特点:

### 架构亮点
1. **Coordinator + Sub-agent 模式**: 主协调器自动将任务委派给 explore/coder/shell 三个专门的子智能体
2. **动态系统提示词**: 每轮调用前注入最新的上下文压力、任务状态和技能信息
3. **插件式技能系统**: 支持通过 manifest.json 自动发现和加载技能,渐进式披露信息
4. **统一任务板**: 支持依赖关系、持久化和自动解阻塞

### 技术栈
- **核心框架**: Google ADK (Agent Development Kit)
- **LLM 接口**: LiteLLM (支持 OpenAI/Anthropic/Zhipu 多提供商)
- **配置管理**: Pydantic Settings
- **代码索引**: code-index-mcp (支持按需深度索引和缓存)

### 关键功能
- 交互式 REPL 界面
- 文件读写和编辑(工作区安全保护)
- 命令执行(危险命令拦截)
- 代码索引(get_symbol_body 高效提取符号)
- 任务管理(最多 20 个任务,依赖关系支持)
- 技能加载和运行

项目结构清晰,模块职责分离明确,具有良好的扩展性和可维护性。