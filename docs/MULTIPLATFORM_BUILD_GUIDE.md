# OpenAkita v1.27.8 多平台构建指南

本指南说明如何在不同平台上构建 OpenAkita v1.27.8 的安装程序。

## 📋 已完成的平台

- ✅ **Linux (Debian/Ubuntu)**: deb 包已成功生成
  - 位置: `apps/setup-center/src-tauri/target/release/bundle/deb/OpenAkita Desktop_1.27.8_amd64.deb`
  - 大小: 274 MB

---

## 🖥️ Windows 平台构建

### 前置要求

1. **Windows 10/11** (64位)
2. **Rust**: https://www.rust-lang.org/tools/install
3. **Node.js**: https://nodejs.org/ (推荐 LTS 版本)
4. **Visual Studio Build Tools**: 
   - 下载: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - 安装时选择 "Desktop development with C++" 工作负载
5. **Git**: https://git-scm.com/download/win

### 构建步骤

```powershell
# 1. 克隆仓库
git clone https://github.com/skyshe/openakita.git
cd openakita

# 2. 切换到 v1.27.8 标签
git checkout v1.27.8

# 3. 安装前端依赖
cd apps/setup-center
npm install

# 4. 返回项目根目录
cd ../..

# 5. 运行构建脚本（Windows 版本）
# 注意：Windows 下需要使用对应的 .bat 脚本或直接运行 Tauri 命令

# 或者直接使用 Tauri 构建
cd apps/setup-center
npm run tauri build -- --bundles nsis
```

### 预期输出

构建成功后，会在以下位置生成 Windows 安装程序：

```
apps/setup-center/src-tauri/target/release/bundle/nsis/OpenAkita Desktop_1.27.8_x64-setup.exe
```

### 安装说明

```powershell
# 双击运行安装程序
OpenAkita Desktop_1.27.8_x64-setup.exe
```

---

## 🍎 macOS 平台构建

### 前置要求

1. **macOS 10.15 (Catalina) 或更高版本**
2. **Xcode Command Line Tools**:
   ```bash
   xcode-select --install
   ```
3. **Rust**: https://www.rust-lang.org/tools/install
4. **Node.js**: https://nodejs.org/ (推荐 LTS 版本)
5. **Git**: 通常预装在 macOS 上，或通过 Homebrew 安装

### 构建步骤

```bash
# 1. 克隆仓库
git clone https://github.com/skyshe/openakita.git
cd openakita

# 2. 切换到 v1.27.8 标签
git checkout v1.27.8

# 3. 安装前端依赖
cd apps/setup-center
npm install

# 4. 返回项目根目录
cd ../..

# 5. 运行构建脚本
./build/build_core.sh --fast

# 或者直接使用 Tauri 构建
cd apps/setup-center
npm run tauri build -- --bundles dmg
```

### 预期输出

构建成功后，会在以下位置生成 macOS 安装程序：

```
apps/setup-center/src-tauri/target/release/bundle/macos/OpenAkita Desktop.app/
apps/setup-center/src-tauri/target/release/bundle/dmg/OpenAkita Desktop_1.27.8_aarch64.dmg
# 或
apps/setup-center/src-tauri/target/release/bundle/dmg/OpenAkita Desktop_1.27.8_x64.dmg
```

### 安装说明

```bash
# 挂载 DMG 文件
hdiutil attach "OpenAkita Desktop_1.27.8_*.dmg"

# 拖拽应用到 Applications 文件夹
```

---

## 🐧 Linux 平台（已完成）

### 安装说明

```bash
# 安装 deb 包
sudo dpkg -i "apps/setup-center/src-tauri/target/release/bundle/deb/OpenAkita Desktop_1.27.8_amd64.deb"

# 如果遇到依赖问题
sudo apt-get install -f
```

### 运行应用

```bash
# 从应用菜单启动，或命令行运行
openakita-setup-center
```

---

## 🔧 通用构建选项

### Tauri 支持的 Bundle 类型

| 平台 | Bundle 类型 | 说明 |
|--------|------------|------|
| Windows | `nsis` | NSIS 安装程序（推荐） |
| Windows | `msi` | Windows Installer |
| macOS | `dmg` | DMG 磁盘映像（推荐） |
| macOS | `app` | .app 应用包 |
| Linux | `deb` | Debian/Ubuntu 包（推荐） |
| Linux | `appimage` | AppImage 自包含包 |
| Linux | `rpm` | Red Hat/CentOS 包 |

### 同时构建多个 Bundle 类型

```bash
# 在任意平台上，可以同时构建多个类型
npm run tauri build -- --bundles nsis,msi  # Windows
npm run tauri build -- --bundles dmg,app   # macOS
npm run tauri build -- --bundles deb,appimage  # Linux
```

### 快速构建模式

使用 `--fast` 参数可以跳过一些耗时的优化步骤：

```bash
# Linux/macOS
./build/build_core.sh --fast

# Windows
# 在对应的构建命令中添加 --fast 参数（如果支持）
```

---

## 📦 构建产物说明

### 核心包 vs 完整版

- **核心包 (Core)**: 约 180-300 MB，包含基本功能
- **完整版 (Full)**: 约 600MB-1GB，包含所有依赖和模型

### 使用 build_core.sh vs build_full.sh

```bash
# 核心包（推荐用于日常使用）
./build/build_core.sh --fast

# 完整版（包含所有功能）
./build/build_full.sh --fast
```

---

## 🚀 版本控制说明

### 当前版本

- **版本号**: v1.27.8
- **Git 标签**: v1.27.8
- **分支**: trae/solo-agent-TfNiky
- **仓库**: https://github.com/skyshe/openakita

### 在此版本上进行开发

```bash
# 克隆并切换到 v1.27.8
git clone https://github.com/skyshe/openakita.git
cd openakita
git checkout v1.27.8

# 创建新的功能分支
git checkout -b feature/your-feature-name

# 开发完成后提交更改
git add .
git commit -m "feat: 描述你的功能"
git push origin feature/your-feature-name
```

---

## 🐛 常见问题

### Windows 构建问题

**Q: 提示找不到 Visual Studio Build Tools**
- A: 确保已安装 Visual Studio Build Tools 并选择了 "Desktop development with C++"

**Q: Rust 编译错误**
- A: 确保安装了最新版本的 Rust，运行 `rustup update`

### macOS 构建问题

**Q: 提示 Xcode Command Line Tools 未安装**
- A: 运行 `xcode-select --install`

**Q: 代码签名错误**
- A: 在 tauri.conf.json 中将 signingIdentity 设置为 "-" 以跳过签名（开发用）

### Linux 构建问题

**Q: 缺少系统依赖**
- A: 运行以下命令安装依赖：
  ```bash
  sudo apt-get install -y libwebkit2gtk-4.1-dev build-essential curl wget file libssl-dev libayatana-appindicator3-dev librsvg2-dev libglib2.0-dev dpkg fakeroot
  ```

---

## 📞 获取帮助

如果在构建过程中遇到问题：

1. 检查 Tauri 官方文档: https://tauri.app/
2. 查看项目的 GitHub Issues
3. 检查构建日志中的错误信息

---

## ✅ 版本 v1.27.8 特性

此版本包含以下主要功能：

- ✨ 多端对话实时同步
- 🔄 对话任务后台持续执行
- 📊 实时对话进度显示
- 🛡️ 窗口失焦不影响对话执行
- 🎯 基于 v1.27.8 标签进行功能迭代

---

**文档版本**: 1.0  
**最后更新**: 2026-04-01  
**适用版本**: OpenAkita v1.27.8
