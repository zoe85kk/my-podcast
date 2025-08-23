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
PLAYLIST_FETCH_COUNT = 20  # 从播放列表中获取更多视频来确保找到最新的

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
    返回最新 N 条视频，通过解析标题中的集数来确定最新
    """
    # 用 dump-json 拿到详细信息
    result = subprocess.run(
        ["/Users/zoekk/Library/Python/3.9/bin/yt-dlp",
         "--dump-json",
         "--playlist-end", str(PLAYLIST_FETCH_COUNT),
         CHANNEL_URL],
        capture_output=True, text=True
    )

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        data = json.loads(line)
        title = data.get("title")
        vid = data.get("id")
        
        if title and vid:
            # 解析标题中的集数，格式如 "S8 E5: ..." 或 "S8E5: ..."
            episode_number = extract_episode_number(title)
            if episode_number:
                videos.append({
                    "title": title,
                    "id": vid,
                    "episode_number": episode_number
                })

    # 按集数倒序排序（数字大的集数更新）
    videos.sort(key=lambda v: v["episode_number"], reverse=True)

    # 只保留最新 MAX_ITEMS 条
    latest_videos = videos[:MAX_ITEMS]

    # 打印调试信息，确认顺序
    for v in latest_videos:
        print(f"Title: {v['title']}, Episode: S8 E{v['episode_number']}")

    return latest_videos

def extract_episode_number(title):
    """
    从标题中提取集数，支持多种格式：
    - "S8 E5: ..." -> 5
    - "S8E5: ..." -> 5
    - "Season 8 Episode 5: ..." -> 5
    """
    import re
    
    # 尝试匹配 "S8 E5" 格式
    match = re.search(r'S8\s*E(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # 尝试匹配 "Season 8 Episode 5" 格式
    match = re.search(r'Season\s*8\s*Episode\s*(\d+)', title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # 如果都没匹配到，返回 None
    return None



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

        # pubDate 用当前时间，因为我们已经按集数排序了
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
        print(f"下载音频: {v['title']}")
        download_audio(v['id'], filename)

    print("更新 RSS feed.xml")
    update_rss(videos)

    print("推送到 GitHub")
    git_push()
    print("完成 ✅ 你的 RSS 已更新并可在 Apple Podcast 订阅。")

if __name__ == "__main__":
    main()
