import os
import re
import subprocess
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom.minidom import parseString

# ----------------- 配置 -----------------
CHANNEL_URL = "https://www.youtube.com/@LastWeekTonight/videos"
DOWNLOAD_DIR = "."
FEED_FILE = "feed.xml"
MAX_ITEMS = 5  # RSS 保留最近几集

# GitHub 配置
GITHUB_REPO = "zoe85kk/my-podcast"  # e.g. jessie/youtube-podcast
GITHUB_BRANCH = "main"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 必须设置环境变量
RSS_URL_BASE = f"https://{GITHUB_REPO.split('/')[0]}.github.io/{GITHUB_REPO.split('/')[1]}"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ----------------- 获取最新完整视频 -----------------
def get_latest_videos():
    ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True, "playlistend": MAX_ITEMS*2}
    result = subprocess.run(
        ["/Users/zoekk/Library/Python/3.9/bin/yt-dlp", "--flat-playlist", "--get-id", "--get-title", CHANNEL_URL],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split("\n")
    episodes = [(lines[i], lines[i+1]) for i in range(0, len(lines), 2)]
    videos = []
    for title, vid in episodes:
        if re.search(r"S\d+\s*E\d+", title):  # 完整集
            videos.append((title, vid))
    return videos[:MAX_ITEMS]

# ----------------- 下载音频 -----------------
def download_audio(video_id, filename):
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = [
        "/Users/zoekk/Library/Python/3.9/bin/yt-dlp", "-x", "--audio-format", "mp3", "-o", filepath, url
    ]
    subprocess.run(ydl_opts, check=True)
    return filepath

# ----------------- 更新 RSS -----------------
def update_rss(videos):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")
    SubElement(channel, "title").text = "Last Week Tonight Podcast"
    SubElement(channel, "link").text = CHANNEL_URL
    SubElement(channel, "description").text = "Auto-generated podcast feed from YouTube full episodes."
    SubElement(channel, "language").text = "en-us"

    for title, vid in videos:
        filename = f"{vid}.mp3"
        SubElement(channel, "item")
        item = SubElement(channel, "item")
        SubElement(item, "title").text = title
        SubElement(item, "link").text = f"https://www.youtube.com/watch?v={vid}"
        SubElement(item, "guid").text = vid
        SubElement(item, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
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

    for title, vid in videos:
        filename = f"{vid}.mp3"
        print(f"下载音频: {title}")
        download_audio(vid, filename)

    print("更新 RSS feed.xml")
    update_rss(videos)

    print("推送到 GitHub")
    git_push()
    print("完成 ✅ 你的 RSS 已更新并可在 Apple Podcast 订阅。")

if __name__ == "__main__":
    main()
