# 版本发布 v1.27.8 - 实施计划

## [ ] 任务 1：更新版本号
- **Priority**: P0
- **Depends On**: None
- **Description**: 
  - 更新 VERSION 文件从 1.27.7 到 1.27.8
  - 更新 pyproject.toml 文件中的版本号
  - 更新 src/openakita/_bundled_version.txt 文件
- **Success Criteria**:
  - 所有版本号文件都更新为 1.27.8
- **Test Requirements**:
  - `programmatic` TR-1.1: 检查 VERSION 文件内容是否为 1.27.8
  - `programmatic` TR-1.2: 检查 pyproject.toml 文件中的 version 字段是否为 1.27.8
- **Notes**: 确保所有版本文件都同步更新

## [ ] 任务 2：更新 CHANGELOG.md
- **Priority**: P0
- **Depends On**: 任务 1
- **Description**: 
  - 在 CHANGELOG.md 中添加 v1.27.8 的更新记录
  - 记录多端对话实时同步功能的改进
  - 记录修复的问题
- **Success Criteria**:
  - CHANGELOG.md 中包含 v1.27.8 的完整更新记录
- **Test Requirements**:
  - `human-judgement` TR-2.1: CHANGELOG.md 格式正确，更新记录清晰
- **Notes**: 参考 Keep a Changelog 格式

## [ ] 任务 3：提交更改到 GitHub
- **Priority**: P0
- **Depends On**: 任务 2
- **Description**: 
  - 检查 git 状态
  - 添加所有更改的文件
  - 创建提交信息
  - 创建 v1.27.8 标签
  - 推送到 GitHub 仓库
- **Success Criteria**:
  - 所有更改都已提交
  - v1.27.8 标签已创建并推送
- **Test Requirements**:
  - `programmatic` TR-3.1: git status 显示没有未提交的更改
  - `programmatic` TR-3.2: git tag 显示 v1.27.8 标签存在
- **Notes**: 确保 git 仓库配置正确

## [ ] 任务 4：检查前端构建状态
- **Priority**: P1
- **Depends On**: 任务 3
- **Description**: 
  - 检查 apps/setup-center 目录
  - 确认前端是否已构建
  - 如果需要，构建前端
- **Success Criteria**:
  - 前端构建文件存在且是最新的
- **Test Requirements**:
  - `programmatic` TR-4.1: 检查 apps/setup-center/dist-web 目录是否存在
- **Notes**: 前端需要先构建才能打包到应用中

## [ ] 任务 5：打包各平台安装程序
- **Priority**: P1
- **Depends On**: 任务 4
- **Description**: 
  - 根据操作系统选择适当的构建脚本
  - 运行构建脚本打包应用
  - 验证生成的安装程序
- **Success Criteria**:
  - 各平台安装程序成功生成
  - 安装程序位于正确的目录
- **Test Requirements**:
  - `programmatic` TR-5.1: 检查 apps/setup-center/src-tauri/target/release/bundle/ 目录
  - `human-judgement` TR-5.2: 安装程序文件存在且大小合理
- **Notes**: 在 Linux 环境下使用 build_core.sh 或 build_full.sh
