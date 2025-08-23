# GitHub Actions 自动播客更新

## 🚀 优势

### **相比本地Cron的优势：**
- ✅ **24/7运行**：不受本地电脑开关机影响
- ✅ **云端执行**：使用GitHub的服务器资源
- ✅ **自动触发**：每天自动执行，无需手动干预
- ✅ **完整日志**：GitHub Actions提供详细的执行日志
- ✅ **手动触发**：可以随时手动触发更新

## ⚙️ 设置步骤

### **1. 设置GitHub Secrets**

在GitHub仓库页面：
1. 点击 **Settings** → **Secrets and variables** → **Actions**
2. 添加以下两个密钥：

#### **YOUTUBE_API_KEY**
- **名称**: `YOUTUBE_API_KEY`
- **值**: 你的YouTube Data API密钥
- **获取方式**: [YouTube Data API v3](https://console.developers.google.com/apis/api/youtube.googleapis.com/overview)

#### **GITHUB_TOKEN**
- **名称**: `GITHUB_TOKEN`
- **值**: 你的GitHub个人访问令牌
- **获取方式**: GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)

### **2. 工作流配置**

工作流文件：`.github/workflows/update_podcast.yml`

#### **执行时间**
- **UTC时间**: 每天17:00
- **北京时间**: 每天01:00
- **手动触发**: 随时可以手动执行

#### **执行步骤**
1. **检出代码**：获取最新代码
2. **设置Python环境**：Python 3.11
3. **安装依赖**：requests, pytube
4. **安装yt-dlp**：YouTube下载工具
5. **设置环境变量**：API密钥等
6. **执行播客更新**：运行更新脚本
7. **提交更改**：自动提交并推送

## 📊 监控执行

### **查看执行状态**
1. 在GitHub仓库页面点击 **Actions** 标签
2. 查看 `Update Podcast` 工作流
3. 点击具体执行记录查看详细日志

### **执行日志示例**
```
✓ Checkout code
✓ Set up Python
✓ Install dependencies
✓ Install yt-dlp
✓ Set environment variables
✓ Run podcast update
✓ Commit and push changes
```

## 🔧 故障排除

### **常见问题**

#### **1. Secrets未设置**
- 错误：`YOUTUBE_API_KEY not found`
- 解决：检查GitHub Secrets设置

#### **2. API配额超限**
- 错误：YouTube API配额用完
- 解决：等待配额重置或升级API计划

#### **3. 网络问题**
- 错误：下载失败
- 解决：GitHub Actions会自动重试

### **手动触发**
如果自动执行失败，可以手动触发：
1. 进入 **Actions** 页面
2. 选择 **Update Podcast** 工作流
3. 点击 **Run workflow** 按钮

## 📅 执行时间表

| 时区 | 执行时间 | 说明 |
|------|----------|------|
| UTC | 17:00 | GitHub Actions执行时间 |
| 北京时间 | 01:00 | 对应本地时间 |
| 美东时间 | 13:00 | 对应美东时间 |

## 🎯 工作流程

```
每天01:00 (北京时间)
    ↓
GitHub Actions自动触发
    ↓
检查Last Week Tonight播放列表
    ↓
下载新视频并转换为MP3
    ↓
重命名为S08E30格式
    ↓
更新RSS订阅源
    ↓
自动提交到GitHub
    ↓
播客内容更新完成
```

## 🚀 优势总结

- **🌍 云端运行**：不受本地设备影响
- **⏰ 定时执行**：每天自动检查更新
- **📱 随时触发**：可以手动执行
- **📊 完整监控**：详细的执行日志
- **🔄 自动同步**：自动提交到GitHub
- **💡 智能更新**：只处理新内容

---

**现在你的播客系统真正实现了24/7自动化！** 🎉
