# 使用YouTube Data API v3（推荐方案）

## 🚀 优势

✅ **无需cookies：** 永远不会过期
✅ **更稳定：** 官方API，不会失效
✅ **更准确：** 直接获取视频信息，包括发布时间
✅ **更快速：** 不需要解析网页内容
✅ **免费额度：** 每天10,000次请求，足够使用

## 📋 获取API Key步骤

### 1. 访问Google Cloud Console
- 访问 [Google Cloud Console](https://console.cloud.google.com/)
- 使用你的Google账号登录

### 2. 创建新项目
- 点击页面顶部的项目选择器
- 点击"新建项目"
- 输入项目名称（如：my-podcast）
- 点击"创建"

### 3. 启用YouTube Data API
- 在左侧菜单中选择"API和服务" > "库"
- 搜索"YouTube Data API v3"
- 点击进入，然后点击"启用"

### 4. 创建凭据
- 在左侧菜单中选择"API和服务" > "凭据"
- 点击"创建凭据" > "API密钥"
- 复制生成的API密钥

### 5. 设置环境变量
```bash
export YOUTUBE_API_KEY="your_api_key_here"
```

或者添加到你的shell配置文件（~/.zshrc 或 ~/.bashrc）：
```bash
echo 'export YOUTUBE_API_KEY="your_api_key_here"' >> ~/.zshrc
source ~/.zshrc
```

## 🔧 安装依赖

```bash
pip3 install requests
```

## 📊 API配额说明

- **免费配额：** 每天10,000次请求
- **每次运行消耗：** 约1-2次请求
- **使用频率：** 每天运行100次都没问题

## 🛡️ 安全注意事项

1. **不要分享API Key：** 这是你的个人凭据
2. **限制使用范围：** 只用于获取视频信息
3. **监控使用量：** 在Google Cloud Console中查看使用情况

## 🧪 测试API

设置好API Key后，可以测试：

```bash
curl "https://www.googleapis.com/youtube/v3/search?key=YOUR_API_KEY&channelId=UC3XTzVzaHQEd30rQbuvCtTQ&part=snippet&order=date&maxResults=1"
```

## 📁 文件说明

- `update_podcast_api.py` - 使用API的新版本脚本
- `update_podcast.py` - 使用cookies的旧版本脚本

## 🚀 使用新脚本

```bash
# 设置API Key
export YOUTUBE_API_KEY="your_key_here"

# 运行脚本
python3 update_podcast_api.py
```

## 🔄 迁移步骤

1. 获取YouTube API Key
2. 设置环境变量
3. 运行新脚本测试
4. 确认工作正常后，可以删除旧脚本

## 💡 其他好处

- **更精确的时间：** 使用视频实际发布时间
- **更好的错误处理：** API错误更明确
- **更快的响应：** 不需要等待网页加载
- **更可靠：** 官方支持，不会因为YouTube界面变化而失效
