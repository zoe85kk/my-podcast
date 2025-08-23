# 播客自动更新 - 本地版本

## 🚀 本地自动化方案

本播客系统使用本地脚本实现自动化更新，无需依赖云端服务。

## 📋 使用方法

### **手动执行**
```bash
python3 update_podcast_api.py
```

### **设置定时任务（可选）**
如果你想要定时执行，可以使用macOS的launchd或简单的cron：

#### **使用launchd（推荐）**
1. 创建plist文件：`~/Library/LaunchAgents/com.zoe.podcast.plist`
2. 设置每天01:00执行
3. 加载服务：`launchctl load ~/Library/LaunchAgents/com.zoe.podcast.plist`

#### **使用cron（简单）**
```bash
# 编辑crontab
crontab -e

# 添加任务（每天01:00执行）
0 1 * * * cd /Users/zoekk/Desktop/my-podcast && python3 update_podcast_api.py
```

## ⚙️ 环境配置

### **必需的环境变量**
```bash
# 添加到 ~/.zshrc
export YOUTUBE_API_KEY="your_youtube_api_key"
export PD_TOKEN="your_github_token"
```

### **重新加载配置**
```bash
source ~/.zshrc
```

## 🎯 功能特点

- ✅ **智能下载**：多种下载策略，自动重试
- ✅ **文件重命名**：自动重命名为S08E30格式
- ✅ **增量更新**：只处理新内容
- ✅ **RSS生成**：自动更新播客订阅源
- ✅ **Git同步**：自动提交并推送到GitHub
- ✅ **错误处理**：容错设计，即使部分失败也能继续

## 📁 文件说明

- **`update_podcast_api.py`** - 主播客更新脚本
- **`last_index.txt`** - 记录上次处理的播放列表位置
- **`feed.xml`** - RSS订阅源
- **`S08E30.mp3`** - 音频文件（自动重命名）

## 🔧 故障排除

### **常见问题**

#### **1. 下载失败**
- 检查网络连接
- 确认YouTube API密钥有效
- 查看详细错误日志

#### **2. Git推送失败**
- 确认PD_TOKEN环境变量已设置
- 检查GitHub仓库权限
- 验证本地Git配置

#### **3. 环境变量问题**
```bash
# 检查环境变量
echo $YOUTUBE_API_KEY
echo $PD_TOKEN

# 重新设置
source ~/.zshrc
```

## 🚀 优势

- **🌍 本地控制**：完全在你的控制之下
- **⚡ 快速执行**：无需等待云端队列
- **🔒 隐私安全**：所有操作都在本地进行
- **💰 成本为零**：无需支付云服务费用
- **🛠️ 易于调试**：可以直接查看和修改代码

## 📅 执行建议

- **频率**：每天执行1-2次
- **时间**：建议在01:00-06:00之间（网络较空闲）
- **监控**：定期检查执行日志和GitHub同步状态

---

**本地自动化方案简单可靠！** 🎉
