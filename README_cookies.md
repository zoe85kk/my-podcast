# 如何获取YouTube Cookies文件

## 方法1: 使用浏览器扩展（推荐）

### Chrome浏览器
1. 安装扩展 "Get cookies.txt LOCALLY"
   - 访问 [Chrome Web Store](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - 点击"添加至Chrome"

2. 获取cookies
   - 访问 [youtube.com](https://youtube.com) 并登录
   - 点击扩展图标
   - 点击"Export"按钮
   - 保存文件为 `cookies.txt`
   - 将文件放在项目目录中

### Firefox浏览器
1. 安装扩展 "cookies.txt"
   - 访问 [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
   - 点击"添加到Firefox"

2. 获取cookies
   - 访问 [youtube.com](https://youtube.com) 并登录
   - 按 F12 打开开发者工具
   - 在控制台中输入：`document.cookie`
   - 复制输出内容到 `cookies.txt` 文件

## 方法2: 手动创建cookies文件

1. 在浏览器中登录YouTube
2. 按F12打开开发者工具
3. 切换到"Application"或"Storage"标签
4. 找到"Cookies" > "https://youtube.com"
5. 复制所有cookie值到文本文件

## cookies.txt 文件格式

文件应该包含以下格式的cookies：
```
.youtube.com	TRUE	/	FALSE	1735689600	VISITOR_INFO1_LIVE	[value]
.youtube.com	TRUE	/	FALSE	1735689600	LOGIN_INFO	[value]
.youtube.com	TRUE	/	FALSE	1735689600	SID	[value]
.youtube.com	TRUE	/	FALSE	1735689600	HSID	[value]
.youtube.com	TRUE	/	FALSE	1735689600	SSID	[value]
.youtube.com	TRUE	/	FALSE	1735689600	APISID	[value]
.youtube.com	TRUE	/	FALSE	1735689600	SAPISID	[value]
```

## 注意事项

1. **隐私安全**: cookies文件包含你的登录信息，不要分享给他人
2. **定期更新**: cookies会过期，需要定期重新获取
3. **文件位置**: 确保 `cookies.txt` 文件在项目根目录中
4. **权限设置**: 确保文件有正确的读取权限

## 测试cookies是否有效

运行脚本后，如果看到以下输出说明cookies有效：
```
[youtube] Extracting URL: https://www.youtube.com/watch?v=...
[youtube] [video_id]: Downloading webpage
[info] [video_id]: Downloading 1 format(s): 251
```

如果看到认证错误，需要重新获取cookies。
