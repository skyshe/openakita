# OpenAkita 项目文档

## 1. 项目概述

OpenAkita 是一个全能自进化 AI 助手，基于 Ralph Wiggum 模式，永不放弃。它是一个功能强大的 AI 代理系统，能够执行各种任务，包括对话、工具调用、记忆管理、技能学习等。

### 核心特性
- 🔄 任务未完成绝不终止
- 🧠 自动学习和进化
- 🔧 动态安装新技能
- 📝 持续记录经验
- 🌐 多通道支持（Telegram、飞书、企业微信、钉钉等）
- 🖥️ 桌面自动化
- 📱 移动应用支持
- 🔍 Web 搜索和浏览器自动化

## 2. 目录结构

OpenAkita 项目采用模块化设计，清晰地分离了不同功能模块。以下是主要目录结构：

```
/workspace/
├── apps/                  # 应用程序
│   └── setup-center/      # 设置中心
├── auth_api/              # 认证 API
├── build/                 # 构建脚本
├── channels/              # 云服务通道
├── data/                  # 数据目录
├── docker/                # Docker 配置
├── docs/                  # 文档
├── docs-site/             # 文档网站
├── examples/              # 示例
├── identity/              # 身份系统
├── mcps/                  # MCP 服务器
├── openakita-plugin-sdk/  # 插件 SDK
├── plugins/               # 插件
├── prompts/               # 提示词
├── research/              # 研究
├── scripts/               # 脚本
├── skills/                # 技能
├── specs/                 # 规格说明
├── src/                   # 源代码
│   └── openakita/         # 核心代码
├── tests/                 # 测试
└── tools/                 # 工具
```

### 核心源代码结构

`src/openakita/` 目录包含了项目的核心代码，结构如下：

```
src/openakita/
├── agents/                # 代理管理
├── api/                   # HTTP API
├── channels/              # 消息通道
├── core/                  # 核心功能
├── evaluation/            # 评估系统
├── evolution/             # 进化系统
├── hub/                   # 平台 hub
├── integrations/          # 集成
├── llm/                   # LLM 客户端
├── logging/               # 日志系统
├── mcp_servers/           # MCP 服务器
├── memory/                # 记忆系统
├── orgs/                  # 组织管理
├── plugins/               # 插件系统
├── prompt/                # 提示词系统
├── scheduler/             # 调度系统
├── sessions/              # 会话管理
├── setup/                 # 安装设置
├── setup_center/          # 设置中心
├── skills/                # 技能系统
├── storage/               # 存储系统
├── testing/               # 测试系统
├── tools/                 # 工具系统
├── tracing/               # 追踪系统
├── utils/                 # 工具函数
└── workspace/             # 工作区
```

## 3. 核心模块分析

### 3.1 Agent 模块

Agent 是 OpenAkita 的核心类，负责协调所有模块，处理用户输入，执行工具调用，管理对话和记忆等。

**主要功能**：
- 接收和处理用户输入
- 协调各个模块的工作
- 执行工具调用
- 执行 Ralph 循环（任务重试机制）
- 管理对话历史和记忆
- 自我进化（技能搜索、安装、生成）

**核心组件**：
- `Brain`：与 LLM 交互的接口
- `MemoryManager`：管理长期记忆
- `SkillManager`：管理技能
- `ReasoningEngine`：推理引擎
- `ContextManager`：上下文管理
- `ResponseHandler`：响应处理

### 3.2 Brain 模块

Brain 模块是 LLM 交互层，是 LLMClient 的薄包装，提供向后兼容的接口。

**主要功能**：
- 与 LLM API 交互
- 处理能力分流（图片/视频自动选择支持的端点）
- 故障切换
- 格式转换
- 支持 thinking 模式

**核心方法**：
- `messages_create`：调用 LLM API
- `think`：发送思考请求到 LLM
- `compiler_think`：Prompt Compiler 专用 LLM 调用

### 3.3 Memory 模块

Memory 模块负责管理 OpenAkita 的记忆系统，包括长期记忆和短期记忆。

**主要功能**：
- 存储和检索记忆
- 向量检索
- 记忆 consolidation
- 实体解析

**核心组件**：
- `MemoryManager`：记忆管理器
- `VectorStore`：向量存储
- `RetrievalEngine`：检索引擎
- `Consolidator`：记忆 consolidation

### 3.4 Skills 模块

Skills 模块负责管理 OpenAkita 的技能系统，包括技能加载、执行和管理。

**主要功能**：
- 加载和管理技能
- 执行技能脚本
- 技能搜索和安装
- 技能生成

**核心组件**：
- `SkillRegistry`：技能注册表
- `SkillLoader`：技能加载器
- `SkillCatalog`：技能目录
- `SkillGenerator`：技能生成器

### 3.5 Channels 模块

Channels 模块负责管理 OpenAkita 的消息通道，包括 Telegram、飞书、企业微信等。

**主要功能**：
- 消息接收和发送
- 通道管理
- 媒体处理
- 消息格式转换

**支持的通道**：
- Telegram
- 飞书
- 企业微信（HTTP 和 WebSocket）
- 钉钉
- OneBot
- QQ 官方机器人
- 微信

### 3.6 API 模块

API 模块提供 HTTP API 接口，用于与 OpenAkita 交互。

**主要功能**：
- 聊天接口
- 模型管理
- 技能管理
- 文件上传
- 健康检查

**API 端点**：
- `/api/chat`：聊天接口
- `/api/models`：模型列表
- `/api/skills`：技能管理
- `/api/memory`：记忆管理
- `/api/config`：配置管理

## 4. 接口设计和实现

### 4.1 HTTP API

OpenAkita 使用 FastAPI 构建 HTTP API，提供了丰富的端点用于与系统交互。

**主要接口**：

| 模块 | 路径 | 功能 | 方法 |
|------|------|------|------|
| 认证 | `/api/auth/*` | 登录、登出、Token 刷新 | POST |
| 对话 | `/api/chat/*` | 聊天交互、消息控制 | POST |
| 智能体 | `/api/agents/*` | Agent 配置文件、Bot 管理 | GET/POST |
| 模型 | `/api/models` | 可用模型/端点列表 | GET |
| 配置 | `/api/config/*` | 工作区配置、环境变量 | GET/POST |
| 技能 | `/api/skills/*` | 技能市场、安装、配置 | GET/POST |
| 记忆 | `/api/memory/*` | 长期记忆 CRUD 与向量检索 | GET/POST |
| 会话 | `/api/sessions/*` | 会话历史管理 | GET/POST |
| 文件 | `/api/files/*` | 文件浏览与上传 | GET/POST |
| 健康检查 | `/api/health` | 服务健康、诊断、调试 | GET |

### 4.2 工具接口

OpenAkita 提供了丰富的工具接口，用于执行各种任务。

**主要工具类别**：
- 文件系统工具：读取、写入、编辑文件
- 浏览器工具：导航、点击、填写表单
- 桌面自动化工具：截图、鼠标键盘控制
- 记忆工具：添加、搜索记忆
- 技能工具：列出、运行技能
- Web 搜索工具：搜索 Web 内容
- MCP 工具：调用 MCP 服务器

## 5. 技术栈和依赖

### 5.1 核心技术栈

| 类别 | 技术/库 | 版本 | 用途 |
|------|---------|------|------|
| 编程语言 | Python | >= 3.11 | 核心开发语言 |
| LLM 接口 | anthropic | >= 0.40.0 | Claude API 客户端 |
| LLM 接口 | openai | >= 1.0.0 | OpenAI 兼容 API |
| MCP 协议 | mcp | >= 1.0.0 | Model Context Protocol 支持 |
| Web 搜索 | ddgs | >= 8.0.0 | 多引擎聚合搜索 |
| CLI 框架 | typer | >= 0.12.0 | 命令行接口 |
| 终端输出 | rich | >= 13.7.0 | 富文本终端输出 |
| 异步 HTTP | httpx | >= 0.27.0 | 异步 HTTP 客户端 |
| 数据库 | aiosqlite | >= 0.20.0 | 异步 SQLite |
| 数据验证 | pydantic | >= 2.5.0 | 数据模型验证 |
| 配置管理 | pydantic-settings | >= 2.1.0 | 配置管理 |
| Git 操作 | gitpython | >= 3.1.40 | Git 操作 |
| 浏览器自动化 | playwright | >= 1.40.0 | 浏览器自动化 |
| API 框架 | fastapi | >= 0.110.0 | HTTP API 框架 |
| ASGI 服务器 | uvicorn | >= 0.27.0 | ASGI 服务器 |
| 消息通道 | python-telegram-bot | >= 21.0 | Telegram Bot API |

### 5.2 可选依赖

| 类别 | 技术/库 | 版本 | 用途 |
|------|---------|------|------|
| 飞书 | lark-oapi | >= 1.3.0 | 飞书官方 SDK |
| 企业微信 | aiohttp | >= 3.9.0 | 企业微信 HTTP 回调 |
| 企业微信 | pycryptodome | >= 3.19.0 | 企业微信消息加解密 |
| 钉钉 | dingtalk-stream | >= 0.24.0 | 钉钉 Stream SDK |
| OneBot | websockets | >= 15.0.1 | OneBot WebSocket 支持 |
| QQ 机器人 | qq-botpy | >= 1.1.5 | QQ 开放平台官方 SDK |
| QQ 机器人 | pilk | >= 0.2.1 | SILK 语音编解码 |
| 桌面自动化 | mss | >= 9.0.0 | 高性能截图 |
| 桌面自动化 | pyautogui | >= 0.9.54 | 鼠标键盘控制 |
| 桌面自动化 | pywinauto | >= 0.6.8 | Windows UIAutomation |

## 6. 模块间调用关系

OpenAkita 的模块之间存在复杂的调用关系，以下是主要模块之间的依赖关系：

### 6.1 核心调用流程

1. **用户输入处理**：
   - 用户通过 CLI、HTTP API 或 IM 通道输入消息
   - 消息被传递给 Agent 实例
   - Agent 处理消息，构建上下文

2. **LLM 交互**：
   - Agent 通过 Brain 模块与 LLM 交互
   - Brain 处理消息格式转换，调用 LLM API
   - LLM 返回响应，可能包含工具调用

3. **工具执行**：
   - Agent 解析 LLM 响应中的工具调用
   - 通过 ToolExecutor 执行工具
   - 将工具执行结果返回给 LLM

4. **记忆管理**：
   - Agent 通过 MemoryManager 存储和检索记忆
   - MemoryManager 使用 VectorStore 进行向量检索
   - 记忆被整合到对话上下文中

5. **技能管理**：
   - Agent 通过 SkillManager 管理技能
   - SkillManager 加载和执行技能脚本
   - 技能执行结果被整合到对话中

### 6.2 主要模块依赖图

```
+----------------+     +----------------+     +----------------+     +----------------+
|   用户输入     | --> |    Agent       | --> |    Brain       | --> |    LLM API     |
+----------------+     +----------------+     +----------------+     +----------------+
     ^                       |                       |
     |                       |                       |
     |                       v                       |
+----------------+     +----------------+     +----------------+
|   IM 通道      | <-- |  ToolExecutor   | <-- |  MemoryManager |
+----------------+     +----------------+     +----------------+
     ^                       |                       |
     |                       v                       |
+----------------+     +----------------+     +----------------+
|  HTTP API      | <-- |  SkillManager  | <-- |  VectorStore   |
+----------------+     +----------------+     +----------------+
```

## 7. 功能实现分析

### 7.1 对话管理

OpenAkita 的对话管理功能通过 SessionManager 和 ContextManager 实现，支持多会话并行处理，保持对话上下文的连续性。

**实现细节**：
- 使用 contextvars 实现协程隔离的会话状态
- 支持会话持久化和恢复
- 实现了消息历史管理和上下文压缩

### 7.2 工具执行

OpenAkita 的工具执行系统支持并行执行多个工具，提高执行效率。

**实现细节**：
- 使用 asyncio.Semaphore 控制并发度
- 对状态型工具（如浏览器、桌面、MCP）使用互斥锁
- 支持工具执行的取消和跳过

### 7.3 记忆系统

OpenAkita 的记忆系统使用向量存储实现高效的记忆检索。

**实现细节**：
- 使用 ChromaDB 作为向量存储
- 支持记忆的自动 consolidation
- 实现了实体解析和关系提取

### 7.4 技能系统

OpenAkita 的技能系统支持动态加载和执行技能，实现了自我进化能力。

**实现细节**：
- 遵循 Agent Skills 规范 (agentskills.io)
- 支持技能的自动发现和安装
- 实现了技能生成功能

### 7.5 IM 通道

OpenAkita 支持多种 IM 通道，实现了统一的消息处理接口。

**实现细节**：
- 使用适配器模式处理不同通道的差异
- 支持消息的格式转换和媒体处理
- 实现了通道的热重载

## 8. 部署和配置

### 8.1 部署方式

OpenAkita 支持多种部署方式：

1. **本地部署**：
   - 使用 `pip install openakita` 安装
   - 运行 `openakita` 启动

2. **Docker 部署**：
   - 使用项目提供的 Dockerfile
   - 运行 `docker-compose up` 启动

3. **开发环境**：
   - 克隆仓库
   - 安装依赖：`pip install -e .[all]`
   - 运行 `openakita` 启动

### 8.2 配置管理

OpenAkita 使用 pydantic-settings 管理配置，支持从环境变量和配置文件加载配置。

**主要配置文件**：
- `llm_endpoints.json`：LLM 端点配置
- `runtime_state.json`：运行时状态
- `config.yaml`：系统配置

**环境变量**：
- `OPENAKITA_PROJECT_ROOT`：项目根目录
- `OPENAI_API_KEY`：OpenAI API Key
- `ANTHROPIC_API_KEY`：Anthropic API Key
- `CORS_ORIGINS`：CORS 允许的源

## 9. 总结和亮点

OpenAkita 是一个功能强大、架构清晰的 AI 助手系统，具有以下亮点：

1. **模块化设计**：采用清晰的模块化架构，各模块职责明确，易于扩展和维护。

2. **多通道支持**：支持多种 IM 通道，包括 Telegram、飞书、企业微信、钉钉等，满足不同用户的需求。

3. **自我进化能力**：能够自动搜索、安装和生成技能，不断提升自身能力。

4. **强大的记忆系统**：使用向量存储实现高效的记忆检索和管理，支持长期记忆。

5. **并行工具执行**：支持并行执行多个工具，提高执行效率。

6. **灵活的配置系统**：支持从环境变量和配置文件加载配置，适应不同的部署环境。

7. **完整的 API**：提供丰富的 HTTP API 接口，方便与其他系统集成。

8. **跨平台支持**：支持 Windows、Linux 和 macOS 等多种平台。

9. **安全可靠**：实现了完善的错误处理和故障切换机制，确保系统稳定运行。

10. **易于扩展**：提供了插件系统和 MCP 协议支持，方便扩展系统功能。

OpenAkita 是一个具有广阔应用前景的 AI 助手系统，通过不断的进化和完善，有望成为人们日常生活和工作中的得力助手。

## 10. 未来发展方向

1. **增强多模态能力**：进一步提升对图像、视频、音频等多模态内容的处理能力。

2. **强化自我进化**：通过更高级的技能学习和生成机制，实现更智能的自我进化。

3. **扩展生态系统**：建立更完善的技能市场和插件生态，丰富系统功能。

4. **优化性能**：通过优化算法和架构，提高系统的响应速度和执行效率。

5. **增强安全性**：加强系统的安全性，保护用户数据和隐私。

6. **支持更多语言**：扩展对更多语言的支持，提高系统的国际化水平。

7. **深化行业应用**：针对不同行业的需求，开发专用的技能和插件，拓展系统的应用场景。

8. **提升用户体验**：通过优化界面和交互方式，提高用户体验。

9. **加强社区建设**：建立活跃的社区，鼓励用户和开发者贡献代码和技能。

10. **探索前沿技术**：持续关注 AI 领域的最新发展，将前沿技术集成到系统中。

---

**文档生成时间**：2026-04-01
**项目版本**：1.27.7
**文档作者**：OpenAkita 项目团队
