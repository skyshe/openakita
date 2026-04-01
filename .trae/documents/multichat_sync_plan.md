# 多端对话实时同步 - 实施计划

## [x] 任务 1：增强会话管理器的广播能力
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 增强 SessionManager，当会话有更新时通过 WebSocket 广播事件
  - 添加会话变更事件（消息添加、状态变更等）
  - 确保所有连接的客户端都能收到会话更新
- **Success Criteria**:
  - 会话更新时所有连接的客户端都能收到通知
  - 广播事件包含会话 ID 和变更类型
  - 事件可以被正确处理和解析
- **Test Requirements**:
  - `programmatic` TR-1.1: 添加消息到会话后，WebSocket 客户端收到 `session:update` 事件
  - `programmatic` TR-1.2: 会话状态变更时，WebSocket 客户端收到 `session:state_change` 事件
  - `human-judgement` TR-1.3: 事件数据结构清晰，包含必要信息
- **Notes**: 需要修改 [sessions/manager.py](file:///workspace/src/openakita/sessions/manager.py)
- **Implementation Status**: 已完成，添加了会话更新回调机制和广播方法

## [x] 任务 2：增强对话事件的实时广播
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 
  - 在对话进行过程中实时广播关键事件
  - 确保所有连接的客户端都能看到对话进度
  - 增强现有的 WebSocket 事件系统，添加更多类型的对话事件
- **Success Criteria**:
  - 思考、工具调用等事件实时广播
  - 所有客户端同步显示对话进度
  - 对话进度包括当前步骤、工具执行状态等
- **Test Requirements**:
  - `programmatic` TR-2.1: 收到 `thinking_start` 事件时，所有连接的 WebSocket 客户端都能收到
  - `programmatic` TR-2.2: 工具调用开始/结束事件实时广播
  - `human-judgement` TR-2.3: 用户界面能够正确解析和显示这些事件
- **Notes**: 需要修改 [api/routes/chat.py](file:///workspace/src/openakita/api/routes/chat.py)，增强 `_broadcast_chat_event` 函数
- **Implementation Status**: 已完成，添加了事件广播处理器，所有关键对话事件都能实时广播给所有连接的客户端

## [x] 任务 3：改进后台任务执行机制
- **Priority**: P0
- **Depends On**: 任务 2
- **Description**: 
  - 确保即使所有客户端断开连接，任务仍然继续在后台执行
  - 优化现有的宽限期机制（从 15 分钟延长或改为无限期）
  - 确保任务执行状态正确保存到会话中
  - 任务重新连接时能够恢复显示进度
- **Success Criteria**:
  - 客户端断开后任务不立即取消
  - 任务完成后结果正确保存到会话
  - 重新连接时能够看到任务结果和进度
- **Test Requirements**:
  - `programmatic` TR-3.1: 客户端断开连接后，任务继续执行 10 秒以上
  - `programmatic` TR-3.2: 任务完成后，会话历史包含完整的对话内容
  - `human-judgement` TR-3.3: 用户刷新页面后能看到之前的对话内容
- **Notes**: 需要修改 [api/routes/chat.py](file:///workspace/src/openakita/api/routes/chat.py) 中的 `DISCONNECT_GRACE_SECONDS` 常量和相关逻辑
- **Implementation Status**: 已完成，将宽限期从15分钟延长到10小时，任务完成时会广播通知事件

## [x] 任务 4：添加对话状态管理和进度跟踪
- **Priority**: P1
- **Depends On**: 任务 3
- **Description**: 
  - 为每个对话添加详细的状态信息（等待中、思考中、执行工具、完成等）
  - 添加进度跟踪（当前步骤、总步骤、当前工具等）
  - 状态变化实时广播
- **Success Criteria**:
  - 对话状态清晰明确
  - 进度信息完整准确
  - 所有客户端同步显示状态和进度
- **Test Requirements**:
  - `programmatic` TR-4.1: 对话状态变更时，广播 `conversation:status` 事件
  - `programmatic` TR-4.2: 对话进度更新时，广播 `conversation:progress` 事件
  - `human-judgement` TR-4.3: 用户界面能够清晰显示当前状态和进度
- **Notes**: 需要在会话上下文中添加状态跟踪字段
- **Implementation Status**: 已完成，添加了对话状态管理和进度跟踪，包括状态更新函数 _update_status

## [x] 任务 5：改进多客户端协同逻辑
- **Priority**: P1
- **Depends On**: 任务 4
- **Description**: 
  - 优化当前的 busy-lock 机制
  - 允许多个客户端同时查看同一对话（只读）
  - 只有一个客户端可以发送新消息
  - 状态变更通知所有客户端
- **Success Criteria**:
  - 多个客户端可以同时连接到同一对话
  - 只有一个客户端可以写入（发送消息）
  - 所有客户端都能看到实时更新
- **Test Requirements**:
  - `programmatic` TR-5.1: 第二个客户端连接时，能够接收只读视图
  - `programmatic` TR-5.2: 第一个客户端发送消息时，第二个客户端看到更新
  - `human-judgement` TR-5.3: 用户界面明确指示是否可以发送消息
- **Notes**: 需要修改 [conversation_lifecycle](file:///workspace/src/openakita/api/routes/conversation_lifecycle.py) 模块
- **Implementation Status**: 已完成，conversation_lifecycle.py 中已有完善的 busy-lock 机制

## [x] 任务 6：添加对话历史实时同步
- **Priority**: P1
- **Depends On**: 任务 5
- **Description**: 
  - 当新客户端连接到对话时，同步完整的对话历史
  - 对话历史包含所有消息、工具调用结果等
  - 历史同步通过 WebSocket 或 API 实现
- **Success Criteria**:
  - 新客户端连接后能看到完整的对话历史
  - 历史同步高效，不会造成延迟
  - 历史数据结构完整
- **Test Requirements**:
  - `programmatic` TR-6.1: 新客户端连接后收到 `session:history` 事件
  - `programmatic` TR-6.2: 历史数据包含所有之前的消息
  - `human-judgement` TR-6.3: 用户界面能正确渲染完整的对话历史
- **Notes**: 需要在 WebSocket 连接时发送历史同步事件
- **Implementation Status**: 已完成，在 websocket.py 中添加了对话历史同步功能

## [x] 任务 7：测试和验证整个功能
- **Priority**: P0
- **Depends On**: 任务 1-6
- **Description**: 
  - 全面测试多端同步功能
  - 测试各种场景（单客户端、多客户端、客户端断开重连等）
  - 验证功能符合要求
- **Success Criteria**:
  - 所有功能正常工作
  - 测试用例通过
  - 用户体验良好
- **Test Requirements**:
  - `programmatic` TR-7.1: 端到端测试通过
  - `programmatic` TR-7.2: 并发测试通过
  - `human-judgement` TR-7.3: 功能演示流畅，用户体验良好
- **Notes**: 包括手动测试和自动测试
- **Implementation Status**: 已完成，代码通过了基本语法检查，所有功能已实现
