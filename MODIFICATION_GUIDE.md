# OpenAkita 功能修改指南

本指南将帮助您了解如何修改 OpenAkita 项目的功能。

---

## 目录

1. [开发环境搭建](#开发环境搭建)
2. [项目结构概览](#项目结构概览)
3. [常见功能修改场景](#常见功能修改场景)
4. [测试与验证](#测试与验证)
5. [提交代码](#提交代码)

---

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/openakita/openakita.git
cd openakita
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装开发依赖

```bash
pip install -e ".[dev,all]"
```

### 4. 安装 pre-commit hooks（推荐）

```bash
pip install pre-commit
pre-commit install
```

### 5. 初始化配置

```bash
openakita init
```

---

## 项目结构概览

### 核心模块位置

| 功能模块 | 文件路径 | 说明 |
|---------|---------|------|
| **Agent 核心** | [src/openakita/core/agent.py](file:///workspace/src/openakita/core/agent.py) | 主 Agent 类 |
| **推理引擎** | [src/openakita/core/reasoning_engine.py](file:///workspace/src/openakita/core/reasoning_engine.py) | ReAct 推理循环 |
| **Brain (LLM)** | [src/openakita/core/brain.py](file:///workspace/src/openakita/core/brain.py) | LLM 交互层 |
| **记忆系统** | [src/openakita/memory/](file:///workspace/src/openakita/memory/) | 记忆管理 |
| **多Agent系统** | [src/openakita/agents/](file:///workspace/src/openakita/agents/) | 多Agent协作 |
| **工具系统** | [src/openakita/tools/](file:///workspace/src/openakita/tools/) | 内置工具 |
| **技能系统** | [src/openakita/skills/](file:///workspace/src/openakita/skills/) | 技能管理 |
| **LLM集成** | [src/openakita/llm/](file:///workspace/src/openakita/llm/) | LLM 提供商 |
| **IM通道** | [src/openakita/channels/](file:///workspace/src/openakita/channels/) | 聊天平台 |
| **REST API** | [src/openakita/api/](file:///workspace/src/openakita/api/) | HTTP API |
| **配置管理** | [src/openakita/config.py](file:///workspace/src/openakita/config.py) | 配置项 |

---

## 常见功能修改场景

### 场景 1：修改 Agent 的核心行为

如果您需要修改 Agent 的核心逻辑，如对话流程、工具调用策略等。

#### 关键文件
- [src/openakita/core/agent.py](file:///workspace/src/openakita/core/agent.py) - 主 Agent 类
- [src/openakita/core/reasoning_engine.py](file:///workspace/src/openakita/core/reasoning_engine.py) - 推理引擎

#### 修改步骤

1. **定位要修改的方法**
   ```python
   # 例如修改 chat 方法
   async def chat(self, message: str) -> str:
       # 您的修改
   ```

2. **添加必要的日志**
   ```python
   logger.info(f"Processing message: {message}")
   ```

3. **运行测试验证**
   ```bash
   pytest tests/component/test_agent.py -v
   ```

---

### 场景 2：添加新的工具

如果您需要添加一个新的内置工具。

#### 关键文件
- [src/openakita/tools/definitions/](file:///workspace/src/openakita/tools/definitions/) - 工具定义
- [src/openakita/tools/handlers/](file:///workspace/src/openakita/tools/handlers/) - 工具处理器

#### 修改步骤

1. **在 tools/definitions/ 中创建工具定义**

   创建新文件，例如 `my_new_tool.py`：
   ```python
   from .base import ToolDefinition

   MY_NEW_TOOL: ToolDefinition = {
       "name": "my_new_tool",
       "description": "工具的简短描述",
       "detail": "工具的详细说明",
       "category": "System",
       "input_schema": {
           "type": "object",
           "properties": {
               "param1": {
                   "type": "string",
                   "description": "参数1说明"
               }
           },
           "required": ["param1"]
       }
   }
   ```

2. **在 tools/handlers/ 中创建工具处理器**

   创建新文件，例如 `my_new_tool.py`：
   ```python
   import logging
   from typing import Any

   logger = logging.getLogger(__name__)

   async def handle_my_new_tool(params: dict[str, Any]) -> str:
       """处理 my_new_tool 的调用"""
       param1 = params.get("param1", "")
       
       try:
           # 实现工具逻辑
           result = f"处理结果: {param1}"
           return result
       except Exception as e:
           logger.error(f"my_new_tool 执行失败: {e}")
           return f"错误: {str(e)}"

   def create_handler():
       """创建处理器（供 registry 使用）"""
       return handle_my_new_tool
   ```

3. **在 tools/definitions/__init__.py 中导出工具**

   ```python
   from .my_new_tool import MY_NEW_TOOL

   BASE_TOOLS = [
       # ... 现有工具
       MY_NEW_TOOL,
   ]
   ```

4. **在 tools/handlers/__init__.py 中注册处理器**

   ```python
   from .my_new_tool import create_handler as create_my_new_tool_handler

   HANDLER_REGISTRY = {
       # ... 现有处理器
       "my_new_tool": create_my_new_tool_handler,
   }
   ```

5. **在 core/agent.py 中导入并注册**

   查看 Agent 类的初始化部分，确保新工具被正确加载。

6. **添加测试**

   在 `tests/component/` 或 `tests/unit/` 中添加测试用例。

---

### 场景 3：修改 LLM 集成

如果您需要修改 LLM 调用逻辑、添加新的 LLM 提供商等。

#### 关键文件
- [src/openakita/llm/client.py](file:///workspace/src/openakita/llm/client.py) - 统一 LLM 客户端
- [src/openakita/llm/providers/](file:///workspace/src/openakita/llm/providers/) - 提供商适配器
- [src/openakita/llm/registries/](file:///workspace/src/openakita/llm/registries/) - 端点注册表

#### 修改步骤

**添加新的 LLM 提供商：**

1. **在 llm/providers/ 中创建提供商适配器**

   例如创建 `my_provider.py`：
   ```python
   import logging
   from typing import Any, AsyncIterator

   from .base import LLMProvider, LLMRequest, LLMResponse

   logger = logging.getLogger(__name__)

   class MyProvider(LLMProvider):
       """我的 LLM 提供商"""

       def __init__(self, config: dict):
           super().__init__(config)
           self.api_key = config.get("api_key", "")
           self.base_url = config.get("base_url", "https://api.myprovider.com/v1")

       async def chat(self, request: LLMRequest) -> LLMResponse:
           """非流式对话"""
           # 实现调用逻辑
           pass

       async def chat_stream(self, request: LLMRequest) -> AsyncIterator[LLMResponse]:
           """流式对话"""
           # 实现流式调用逻辑
           pass
   ```

2. **在 llm/registries/ 中创建端点模板**

   例如创建 `my_provider.py`：
   ```python
   from ..types import EndpointConfig

   MY_PROVIDER_ENDPOINTS = [
       EndpointConfig(
           name="my-provider-default",
           provider_type="my_provider",
           model="my-model",
           api_key="",
           base_url="https://api.myprovider.com/v1",
           capabilities=["text", "tools"],
           priority=10,
       )
   ]
   ```

3. **在 llm/client.py 中注册新提供商**

   更新 `LLMClient.__init__` 方法以支持新的提供商类型。

4. **添加配置示例**

   在 `data/llm_endpoints.json.example` 中添加配置示例。

---

### 场景 4：添加新的 IM 通道

如果您需要添加新的聊天平台支持。

#### 关键文件
- [src/openakita/channels/adapters/](file:///workspace/src/openakita/channels/adapters/) - 通道适配器
- [src/openakita/channels/base.py](file:///workspace/src/openakita/channels/base.py) - 基础适配器类

#### 修改步骤

1. **在 channels/adapters/ 中创建适配器**

   例如创建 `my_platform.py`：
   ```python
   import logging
   from typing import Any

   from ..base import BaseChannel, Message

   logger = logging.getLogger(__name__)

   class MyPlatformAdapter(BaseChannel):
       """我的平台适配器"""

       def __init__(self, credential1: str, credential2: str):
           self.credential1 = credential1
           self.credential2 = credential2
           self._running = False

       async def start(self) -> None:
           """启动适配器"""
           self._running = True
           logger.info("MyPlatform adapter started")

       async def stop(self) -> None:
           """停止适配器"""
           self._running = False
           logger.info("MyPlatform adapter stopped")

       async def receive_message(self) -> Message | None:
           """接收消息"""
           # 实现接收逻辑
           pass

       async def send_response(self, message: str, context: dict | None = None) -> None:
           """发送响应"""
           # 实现发送逻辑
           pass

       @property
       def is_running(self) -> bool:
           return self._running
   ```

2. **在 channels/registry.py 中注册适配器**

   ```python
   from .adapters.my_platform import MyPlatformAdapter

   ADAPTER_REGISTRY = {
       # ... 现有适配器
       "my_platform": lambda creds, **kwargs: MyPlatformAdapter(
           credential1=creds.get("credential1", ""),
           credential2=creds.get("credential2", ""),
       ),
   }
   ```

3. **在 config.py 中添加配置项**

   添加必要的配置字段。

4. **在 API 中添加配置端点**

   在 `api/routes/im.py` 中添加配置接口。

---

### 场景 5：修改前端界面

如果您需要修改桌面端或移动端的 UI。

#### 关键文件
- [apps/setup-center/src/](file:///workspace/apps/setup-center/src/) - 前端源代码
- [apps/setup-center/src-tauri/](file:///workspace/apps/setup-center/src-tauri/) - Tauri Rust 代码

#### 修改步骤

1. **进入前端目录**
   ```bash
   cd apps/setup-center
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```

4. **修改代码**
   - React 组件在 `src/` 目录
   - 样式使用 Tailwind CSS
   - 类型定义在 `src/types.ts`

5. **构建前端**
   ```bash
   # Web 端
   VITE_BUILD_TARGET=web npm run build:web

   # Tauri 桌面端
   npm run tauri build
   ```

---

### 场景 6：修改记忆系统

如果您需要修改记忆提取、存储或检索逻辑。

#### 关键文件
- [src/openakita/memory/manager.py](file:///workspace/src/openakita/memory/manager.py) - 记忆管理器
- [src/openakita/memory/extractor.py](file:///workspace/src/openakita/memory/extractor.py) - 记忆提取器
- [src/openakita/memory/retrieval.py](file:///workspace/src/openakita/memory/retrieval.py) - 检索引擎
- [src/openakita/memory/storage.py](file:///workspace/src/openakita/memory/storage.py) - 存储层

#### 修改步骤

**修改记忆提取逻辑：**

1. 编辑 [src/openakita/memory/extractor.py](file:///workspace/src/openakita/memory/extractor.py)
2. 修改 `extract_from_turn_v2` 方法
3. 添加或修改提取提示词
4. 运行测试：`pytest tests/component/test_memory_manager.py -v`

**修改检索逻辑：**

1. 编辑 [src/openakita/memory/retrieval.py](file:///workspace/src/openakita/memory/retrieval.py)
2. 修改 `RetrievalEngine.search` 方法
3. 调整多路召回策略
4. 运行测试：`pytest tests/component/test_retrieval_engine.py -v`

---

## 测试与验证

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/unit/test_config.py -v

# 运行特定测试用例
pytest tests/ -v -k "test_my_feature"

# 运行并生成覆盖率报告
pytest tests/ --cov=src/openakita --cov-report=html
```

### 测试层级

| 层级 | 目录 | 说明 |
|------|------|------|
| L1 单元测试 | `tests/unit/` | 独立模块测试 |
| L2 组件测试 | `tests/component/` | 多模块交互测试 |
| L3 集成测试 | `tests/integration/` | API/通道集成测试 |
| L4 E2E 测试 | `tests/e2e/` | 端到端完整流程 |

### 代码质量检查

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Format code
ruff format src/

# All checks
pytest && mypy src/ && ruff check src/
```

### 手动测试

```bash
# 启动开发模式
openakita serve --dev

# 或者启动交互式 CLI
openakita
```

---

## 提交代码

### 1. 创建分支

```bash
git checkout -b feature/my-awesome-feature
```

### 2. 提交更改

遵循 Conventional Commits 规范：

```bash
git add .
git commit -m "feat(scope): description of the feature"
```

**提交类型：**
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具相关

### 3. 推送到远程

```bash
git push origin feature/my-awesome-feature
```

### 4. 创建 Pull Request

在 GitHub 上创建 PR，使用提供的模板：
- 清晰描述更改
- 勾选相关的检查项
- 链接相关的 Issue（如果有）
- 添加截图（如果是 UI 更改）

---

## 调试技巧

### 启用调试日志

```bash
# 设置环境变量
export LOG_LEVEL=DEBUG

# 或者在代码中
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 使用 Python 调试器

```python
import pdb; pdb.set_trace()  # 在代码中添加断点
```

或者使用更现代的调试器：

```python
import breakpoint; breakpoint()  # Python 3.7+
```

### 查看 LLM 交互日志

LLM 交互日志保存在：
```
data/logs/llm/
```

### 使用 Tracing 系统

在配置中启用 tracing：

```python
# settings.tracing_enabled = True
```

追踪文件保存在：
```
data/traces/
```

---

## 常见问题

### Q: 如何添加新的配置项？

A: 在 [src/openakita/config.py](file:///workspace/src/openakita/config.py) 中添加新的配置字段，使用 Pydantic 的 `Field` 定义。

### Q: 如何修改系统提示词？

A: 系统提示词位于：
- [src/openakita/prompt/models/](file:///workspace/src/openakita/prompt/models/) - 不同模型的提示词
- [identity/SOUL.md](file:///workspace/identity/SOUL.md) - 核心价值观
- [identity/AGENT.md](file:///workspace/identity/AGENT.md) - 行为规范

### Q: 如何处理数据库迁移？

A: 数据库相关代码在 [src/openakita/storage/database.py](file:///workspace/src/openakita/storage/database.py)，修改时请确保向后兼容。

### Q: 如何添加新的技能？

A: 技能系统遵循 Agent Skills 规范，参考 [docs/skills.md](file:///workspace/docs/skills.md) 了解详细信息。

---

## 更多资源

- [CONTRIBUTING.md](file:///workspace/CONTRIBUTING.md) - 贡献指南
- [PROJECT_DOCUMENTATION.md](file:///workspace/PROJECT_DOCUMENTATION.md) - 完整项目文档
- [docs/](file:///workspace/docs/) - 详细文档目录
- [specs/](file:///workspace/specs/) - 技术规范

---

## 寻求帮助

如果您在修改过程中遇到问题：

1. 查看 [GitHub Discussions](https://github.com/openakita/openakita/discussions)
2. 提交 [Issue](https://github.com/openakita/openakita/issues)
3. 加入社区群聊（详见 README）
