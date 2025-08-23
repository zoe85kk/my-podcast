import os
import requests
import subprocess
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom.minidom import parseString

# ----------------- 配置 -----------------
PLAYLIST_ID = "PLmKbqjSZR8TbPlILkdUvuBr7NPsblAK9W"  # Last Week Tonight播放列表ID
DOWNLOAD_DIR = "."
FEED_FILE = "feed.xml"
MAX_ITEMS = 1  # RSS 保留最近几集
LAST_POSITION_FILE = "last_index.txt"  # 存储上次处理的播放列表位置（position）
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # 必须设置环境变量

# GitHub 配置
GITHUB_REPO = "zoe85kk/my-podcast"
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
RSS_URL_BASE = f"https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --------------- 获取最新视频 ---------------
def get_last_position():
    """获取上次处理的播放列表位置（position）"""
    last_position_path = os.path.join(DOWNLOAD_DIR, LAST_POSITION_FILE)
    if os.path.exists(last_position_path):
        try:
            with open(last_position_path, 'r') as f:
                return int(f.read().strip())
        except (ValueError, FileNotFoundError):
            pass
    return -1  # 如果没有记录，从-1开始（这样position=0的视频也会被处理）

def save_last_position(position):
    """保存最新处理的播放列表位置（position）"""
    last_position_path = os.path.join(DOWNLOAD_DIR, LAST_POSITION_FILE)
    with open(last_position_path, 'w') as f:
        f.write(str(position))

def get_latest_videos():
    """
    使用YouTube API获取最新视频
    """
    if not YOUTUBE_API_KEY:
        print("错误: 未设置 YOUTUBE_API_KEY 环境变量")
        print("请设置环境变量: export YOUTUBE_API_KEY='your_api_key_here'")
        return []
    
    last_position = get_last_position()
    print(f"上次处理的播放列表位置: {last_position}")
    
    # 使用YouTube API获取播放列表最新视频
    url = f"https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        'key': YOUTUBE_API_KEY,
        'playlistId': PLAYLIST_ID,
        'part': 'snippet',
        'maxResults': 50
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for item in data.get('items', []):
            video_id = item['snippet']['resourceId']['videoId']
            title = item['snippet']['title']
            published_at = item['snippet']['publishedAt']
            position = item['snippet']['position']  # 播放列表中的位置
                
            videos.append({
                'id': video_id,
                'title': title,
                'published_at': published_at,
                'position': position
            })
        
        print(f"播放列表中总共有 {len(videos)} 个视频")
        print(f"最大索引: {max([v['position'] for v in videos]) if videos else 'None'}")
        print(f"最小索引: {min([v['position'] for v in videos]) if videos else 'None'}")
        
        # 查找大于上次位置的视频（新视频）
        new_videos = [v for v in videos if v['position'] > last_position]
        
        if not new_videos:
            print(f"没有找到新的视频（position > {last_position}）")
            return []
        
        # 按播放列表位置倒序排序（position大的在前面，代表最新的视频）
        new_videos.sort(key=lambda v: v['position'], reverse=True)
        
        # 只保留最新 MAX_ITEMS 条
        latest_videos = new_videos[:MAX_ITEMS]
        
        print(f"找到 {len(latest_videos)} 个新视频")
        for v in latest_videos:
            print(f"Title: {v['title']}, Position: {v['position']}, ID: {v['id']}")
        
        return latest_videos
        
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return []
    except KeyError as e:
        print(f"API响应格式错误: {e}")
        return []

# ----------------- 下载音频 -----------------
def download_audio(video_id, filename):
    """使用yt-dlp下载音频（不需要cookies）"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = [
        "yt-dlp",  # 使用系统安装的yt-dlp
        "-x", "--audio-format", "mp3", "-o", filepath, url
    ]
    
    try:
        subprocess.run(ydl_opts, check=True)
        return filepath
    except subprocess.CalledProcessError as e:
        print(f"下载失败: {e}")
        # 如果下载失败，尝试使用备用方法
        return download_audio_backup(video_id, filename)

def download_audio_backup(video_id, filename):
    """备用下载方法：使用pytube"""
    try:
        from pytube import YouTube
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url)
        
        # 获取音频流
        audio_stream = yt.streams.filter(only_audio=True).first()
        if audio_stream:
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            audio_stream.download(output_path=DOWNLOAD_DIR, filename=filename)
            return filepath
    except ImportError:
        print("pytube未安装，无法使用备用下载方法")
    except Exception as e:
        print(f"备用下载方法失败: {e}")
    
    return None

# ----------------- 更新 RSS -----------------
def update_rss(videos):
    """更新RSS feed"""
    namespaces = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    }
    
    rss = Element("rss", version="2.0")
    rss.set('xmlns:itunes', namespaces['itunes'])
    
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Last Week Tonight Podcast"
    SubElement(channel, "link").text = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
    SubElement(channel, "description").text = "Zoe Podcast"
    SubElement(channel, "language").text = "en-us"
    SubElement(channel, "itunes:image", href="https://github.com/zoe85kk/my-podcast/cover.jpg")

    for v in videos:
        filename = f"{v['id']}.mp3"
        item = SubElement(channel, "item")
        SubElement(item, "title").text = v["title"]
        SubElement(item, "link").text = f"https://www.youtube.com/watch?v={v['id']}"
        SubElement(item, "guid").text = v["id"]

        # 使用API返回的发布时间
        pub_date = datetime.fromisoformat(v["published_at"].replace('Z', '+00:00')).strftime("%a, %d %b %Y %H:%M:%S +0000")
        SubElement(item, "pubDate").text = pub_date

        SubElement(item, "enclosure", url=f"{RSS_URL_BASE}/{filename}", type="audio/mpeg")

    xml_str = parseString(tostring(rss)).toprettyxml(indent="  ")
    feed_path = os.path.join(DOWNLOAD_DIR, FEED_FILE)
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    return feed_path

# ----------------- Git 操作 -----------------
def git_push():
    """推送到GitHub"""
    os.chdir(DOWNLOAD_DIR)
    
    if not os.path.exists(os.path.join(DOWNLOAD_DIR, ".git")):
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "remote", "add", "origin", f"https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git"], check=True)
    
    subprocess.run(["git", "checkout", "-B", GITHUB_BRANCH], check=True)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", "Update podcast feed"], check=True)
    subprocess.run(["git", "push", "-u", "origin", GITHUB_BRANCH, "--force"], check=True)

# ----------------- 主流程 -----------------
def main():
    videos = get_latest_videos()
    if not videos:
        print("没有找到新视频")
        return

    for v in videos:
        filename = f"{v['id']}.mp3"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            print(f"音频文件已存在，跳过下载: {v['title']}")
        else:
            print(f"下载音频: {v['title']}")
            if download_audio(v['id'], filename):
                print(f"下载成功: {filename}")
            else:
                print(f"下载失败，跳过: {v['title']}")
                continue

    print("更新 RSS feed.xml")
    update_rss(videos)

    # 保存最新处理的播放列表位置
    latest_position = videos[0]['position']
    save_last_position(latest_position)
    print(f"保存最新播放列表位置: {latest_position}")

    print("推送到 GitHub")
    git_push()
    print("完成 ✅ 你的 RSS 已更新并可在 Apple Podcast 订阅。")

if __name__ == "__main__":
    main()
