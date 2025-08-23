import os
import re
import subprocess
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom.minidom import parseString

# ----------------- 配置 -----------------
CHANNEL_URL = "https://www.youtube.com/playlist?list=PLmKbqjSZR8TbPlILkdUvuBr7NPsblAK9W"
DOWNLOAD_DIR = "."
FEED_FILE = "feed.xml"
MAX_ITEMS = 1  # RSS 保留最近几集

# GitHub 配置
GITHUB_REPO = "zoe85kk/my-podcast"  # e.g. jessie/youtube-podcast
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 必须设置环境变量
RSS_URL_BASE = f"https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --------------- 获取最新视频 ---------------
import json
import subprocess

def get_latest_videos():
    """
    返回最新 N 条视频，确保第一条就是最新上传的视频
    """
    # 用 flat-playlist 获取播放列表信息
    result = subprocess.run(
        ["/Users/zoekk/Library/Python/3.9/bin/yt-dlp",
         "--cookies-from-browser", "chrome",  # 或者使用 "--cookies", "cookies.txt"
         "--flat-playlist",
         "--get-id",
         "--get-title",
         "--playlist-end", str(MAX_ITEMS*2),
         CHANNEL_URL],
        capture_output=True, text=True
    )

    print(f"yt-dlp 输出行数: {len(result.stdout.strip().split(chr(10)))}")
    print(f"yt-dlp 错误输出: {result.stderr}")

    # 解析 flat-playlist 输出（交替的标题和ID）
    lines = result.stdout.strip().split("\n")
    videos = []
    
    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            title = lines[i].strip()
            vid = lines[i + 1].strip()
            if title and vid:
                # 使用播放列表索引作为排序依据
                videos.append({
                    "title": title,
                    "id": vid,
                    "playlist_index": len(videos) + 1
                })
                print(f"处理视频: title={title}, vid={vid}, index={len(videos)}")

    print(f"找到 {len(videos)} 个有效视频")

    # 按播放列表索引倒序排序（索引大的在前面，代表最新的视频）
    videos.sort(key=lambda v: v["playlist_index"], reverse=True)

    # 只保留最新 MAX_ITEMS 条
    latest_videos = videos[:MAX_ITEMS]

    # 打印调试信息，确认顺序
    for v in latest_videos:
        print(f"Title: {v['title']}, Playlist Index: {v['playlist_index']}")

    return latest_videos



# ----------------- 下载音频 -----------------
def download_audio(video_id, filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = [
        "/Users/zoekk/Library/Python/3.9/bin/yt-dlp", 
        "--cookies-from-browser", "chrome",  # 或者使用 "--cookies", "cookies.txt"
        "-x", "--audio-format", "mp3", "-o", filepath, url
    ]
    subprocess.run(ydl_opts, check=True)
    return filepath

# ----------------- 更新 RSS -----------------
def update_rss(videos):
    # Define namespaces
    namespaces = {
        'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'
    }
    
    rss = Element("rss", version="2.0")
    # Add itunes namespace to root element
    rss.set('xmlns:itunes', namespaces['itunes'])
    
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Last Week Tonight Podcast"
    SubElement(channel, "link").text = CHANNEL_URL
    SubElement(channel, "description").text = "Zoe Podcast"
    SubElement(channel, "language").text = "en-us"
    SubElement(channel, "itunes:image", href="https://github.com/zoe85kk/my-podcast/cover.jpg")

    for v in videos:
        filename = f"{v['id']}.mp3"
        item = SubElement(channel, "item")
        SubElement(item, "title").text = v["title"]
        SubElement(item, "link").text = f"https://www.youtube.com/watch?v={v['id']}"
        SubElement(item, "guid").text = v["id"]

        # pubDate 用当前时间，因为我们已经按播放列表索引排序了
        pub_date = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
        SubElement(item, "pubDate").text = pub_date

        SubElement(item, "enclosure", url=f"{RSS_URL_BASE}/{filename}", type="audio/mpeg")

    xml_str = parseString(tostring(rss)).toprettyxml(indent="  ")
    feed_path = os.path.join(DOWNLOAD_DIR, FEED_FILE)
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    return feed_path


# ----------------- Git 操作 -----------------
def git_push():
    os.chdir(DOWNLOAD_DIR)
    # 初始化 git 仓库（如果第一次运行）
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
        print("未找到完整视频")
        return

    for v in videos:
        filename = f"{v['id']}.mp3"
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        if os.path.exists(filepath):
            print(f"音频文件已存在，跳过下载: {v['title']}")
        else:
            print(f"下载音频: {v['title']}")
            try:
                download_audio(v['id'], filename)
            except subprocess.CalledProcessError:
                print(f"下载失败，跳过: {v['title']}")
                continue

    print("更新 RSS feed.xml")
    update_rss(videos)

    print("推送到 GitHub")
    git_push()
    print("完成 ✅ 你的 RSS 已更新并可在 Apple Podcast 订阅。")

if __name__ == "__main__":
    main()