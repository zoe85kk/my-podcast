import os
import requests
import subprocess
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring
from xml.dom.minidom import parseString

# ----------------- 配置 -----------------
PLAYLIST_ID = "PLmKbqjSZR8TbPlILkdUvuBr7NPsblAK9W"  # Last Week Tonight播放列表ID
DOWNLOAD_DIR = "."
FEED_FILE = "feed.xml"
MAX_ITEMS = 3  # RSS 保留最近几集
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

def extract_episode_info(title):
    """从标题中提取季数和集数信息"""
    import re
    # 匹配 S8 E30 或 S08 E30 格式
    pattern = r'S(\d+)\s*E(\d+)'
    match = re.search(pattern, title, re.IGNORECASE)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return f"S{season:02d}E{episode:02d}"
    return None

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
    
    # 尝试多种下载策略
    download_strategies = [
        # 策略1：基本下载
        ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "-o", filepath, url],
        # 策略2：添加更多选项
        ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "--extractor-args", "youtube:player_client=android", "-o", filepath, url],
        # 策略3：使用不同的音频质量
        ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "--audio-quality", "0", "-o", filepath, url],
        # 策略4：添加用户代理
        ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "-o", filepath, url]
    ]
    
    for i, strategy in enumerate(download_strategies, 1):
        try:
            print(f"尝试下载策略 {i}: {' '.join(strategy[1:])}")
            subprocess.run(strategy, check=True, capture_output=True, text=True)
            if os.path.exists(filepath):
                print(f"策略 {i} 下载成功")
                return filepath
        except subprocess.CalledProcessError as e:
            print(f"策略 {i} 失败: {e}")
            continue
    
    print("所有yt-dlp策略都失败了，尝试备用方法")
    return download_audio_backup(video_id, filename)

def download_audio_backup(video_id, filename):
    """备用下载方法：使用pytube"""
    try:
        from pytube import YouTube
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"尝试pytube下载: {url}")
        
        yt = YouTube(url)
        
        # 获取音频流
        audio_streams = yt.streams.filter(only_audio=True)
        if audio_streams:
            # 选择最高质量的音频流
            audio_stream = audio_streams.order_by('abr').desc().first()
            print(f"选择音频流: {audio_stream}")
            
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            audio_stream.download(output_path=DOWNLOAD_DIR, filename=filename)
            
            if os.path.exists(filepath):
                print(f"pytube下载成功: {filepath}")
                return filepath
            else:
                print("pytube下载失败：文件未创建")
        else:
            print("未找到可用的音频流")
    except ImportError:
        print("pytube未安装，无法使用备用下载方法")
    except Exception as e:
        print(f"备用下载方法失败: {e}")
        import traceback
        traceback.print_exc()
    
    return None

# ----------------- 保存视频标题映射 -----------------
def save_video_title_mapping(video_id, video_title, episode_name):
    """保存视频标题映射，用于RSS生成"""
    if not episode_name:
        return
    
    mapping_file = os.path.join(DOWNLOAD_DIR, "video_titles.txt")
    
    try:
        # 读取现有映射
        existing_mappings = {}
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '|' in line:
                        parts = line.strip().split('|', 2)
                        if len(parts) == 3:
                            existing_mappings[parts[0]] = (parts[1], parts[2])
        
        # 添加新映射
        existing_mappings[episode_name] = (video_id, video_title)
        
        # 写入文件
        with open(mapping_file, 'w', encoding='utf-8') as f:
            for ep_name, (vid_id, vid_title) in existing_mappings.items():
                f.write(f"{ep_name}|{vid_id}|{vid_title}\n")
        
        print(f"保存标题映射: {episode_name} -> {video_title}")
        
    except Exception as e:
        print(f"保存标题映射失败: {e}")

# ----------------- 获取视频标题映射 -----------------
def get_video_title_for_audio(audio_filename):
    """根据音频文件名获取对应的视频标题"""
    # 从video_titles.txt读取视频标题映射
    mapping_file = os.path.join(DOWNLOAD_DIR, "video_titles.txt")
    if not os.path.exists(mapping_file):
        return None
    
    try:
        # 从音频文件名提取episode名称
        episode_name = audio_filename.replace('.mp3', '')
        
        with open(mapping_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '|' in line:
                    parts = line.strip().split('|', 2)
                    if len(parts) == 3:
                        ep_name, video_id, video_title = parts
                        if ep_name == episode_name:
                            return video_title
        
        return None
    except Exception as e:
        print(f"读取video_titles.txt失败: {e}")
        return None

# ----------------- 更新 RSS -----------------
def update_rss():
    """更新RSS feed，包含所有音频文件"""
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
    SubElement(channel, "itunes:image", href=f"{RSS_URL_BASE}/cover.jpg")

    # 扫描目录中所有MP3文件
    mp3_files = []
    for file in os.listdir(DOWNLOAD_DIR):
        if file.endswith('.mp3'):
            mp3_files.append(file)
    
    print(f"找到 {len(mp3_files)} 个音频文件")
    
    # 按文件名排序（S08E28, S08E29, S08E30...）
    mp3_files.sort(reverse=True)  # 最新的在前面
    
    for filename in mp3_files:
        # 创建RSS条目
        item = SubElement(channel, "item")
        
        # 尝试从last_episode.txt获取视频标题映射
        video_title = get_video_title_for_audio(filename)
        
        if video_title:
            # 使用视频原始标题
            title = video_title
        else:
            # 如果没有找到映射，使用文件名作为后备
            episode_name = extract_episode_info(filename.replace('.mp3', ''))
            if episode_name:
                title = f"Last Week Tonight - {episode_name}"
            else:
                title = filename.replace('.mp3', '')
        
        SubElement(item, "title").text = title
        SubElement(item, "link").text = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
        SubElement(item, "guid").text = filename
        
        # 使用当前时间-1天作为发布时间，避免未来时间问题
        yesterday = datetime.now() - timedelta(days=1)
        pub_date = yesterday.strftime("%a, %d %b %Y %H:%M:%S +0000")
        SubElement(item, "pubDate").text = pub_date
        
        SubElement(item, "enclosure", url=f"{RSS_URL_BASE}/{filename}", type="audio/mpeg")
        print(f"添加RSS条目: {title} -> {filename}")

    xml_str = parseString(tostring(rss)).toprettyxml(indent="  ")
    feed_path = os.path.join(DOWNLOAD_DIR, FEED_FILE)
    with open(feed_path, "w", encoding="utf-8") as f:
        f.write(xml_str)
    
    print(f"RSS更新完成，包含 {len(mp3_files)} 个音频文件")
    return feed_path

# ----------------- Git 操作 -----------------
def git_push():
    """推送到GitHub"""
    os.chdir(DOWNLOAD_DIR)
    
    # 获取GitHub Token（本地环境）
    github_token = os.getenv("PD_TOKEN")
    if not github_token:
        print("警告: 未设置 PD_TOKEN 环境变量，尝试使用本地Git配置")
        # 继续执行，依赖本地Git配置
    
    if not os.path.exists(os.path.join(DOWNLOAD_DIR, ".git")):
        subprocess.run(["git", "init"], check=True)
        subprocess.run(["git", "remote", "add", "origin", f"https://{github_token}@github.com/{GITHUB_REPO}.git"], check=True)
    
    subprocess.run(["git", "checkout", "-B", GITHUB_BRANCH], check=True)
    subprocess.run(["git", "add", "."], check=True)
    
    # 检查是否有更改需要提交
    try:
        subprocess.run(["git", "commit", "-m", "Update podcast feed"], check=True)
        subprocess.run(["git", "push", "-u", "origin", GITHUB_BRANCH, "--force"], check=True)
        print("Git推送成功")
    except subprocess.CalledProcessError as e:
        print(f"Git操作失败: {e}")
        # 如果没有更改，尝试直接推送
        try:
            subprocess.run(["git", "push", "-u", "origin", GITHUB_BRANCH, "--force"], check=True)
            print("Git推送成功（无更改）")
        except subprocess.CalledProcessError as e2:
            print(f"Git推送最终失败: {e2}")

# ----------------- 主流程 -----------------
def main():
    videos = get_latest_videos()
    if not videos:
        print("没有找到新视频")
        return

    for v in videos:
        # 生成新的文件名：S08E30.mp3
        episode_name = extract_episode_info(v['title'])
        if episode_name:
            new_filename = f"{episode_name}.mp3"
        else:
            # 如果没有匹配到季数集数，使用原文件名
            new_filename = f"{v['id']}.mp3"
        
        # 检查新文件名是否已存在
        new_filepath = os.path.join(DOWNLOAD_DIR, new_filename)
        if os.path.exists(new_filepath):
            print(f"音频文件已存在，跳过下载: {v['title']} -> {new_filename}")
        else:
            # 下载到临时文件名，然后重命名
            temp_filename = f"{v['id']}.mp3"
            temp_filepath = os.path.join(DOWNLOAD_DIR, temp_filename)
            
            print(f"下载音频: {v['title']} -> {new_filename}")
            download_success = False
            
            download_result = download_audio(v['id'], temp_filename)
            if download_result:
                # 下载成功，检查文件
                if os.path.exists(temp_filepath):
                    try:
                        os.rename(temp_filepath, new_filepath)
                        print(f"下载成功并重命名: {temp_filename} -> {new_filename}")
                        download_success = True
                        
                        # 保存视频标题映射，用于RSS生成
                        save_video_title_mapping(v['id'], v['title'], episode_name)
                        
                    except OSError as e:
                        print(f"重命名失败: {e}")
                        # 如果重命名失败，保留原文件名
                        new_filename = temp_filename
                        download_success = True
                        
                        # 即使重命名失败，也保存标题映射
                        save_video_title_mapping(v['id'], v['title'], episode_name)
                else:
                    print(f"下载失败，文件不存在: {temp_filename}")
                    download_success = False
            else:
                print(f"下载失败，跳过: {v['title']}")
                # 即使下载失败，也记录这个视频，只是标记为未下载
                download_success = False
                new_filename = f"{v['id']}.mp3"  # 使用默认文件名
            
            # 记录下载状态
            v['download_success'] = download_success
            v['filename'] = new_filename

    print("更新 RSS feed.xml")
    # 更新RSS，包含所有音频文件
    update_rss()

    # 保存最新处理的播放列表位置
    latest_position = videos[0]['position']
    save_last_position(latest_position)
    print(f"保存最新播放列表位置: {latest_position}")

    print("推送到 GitHub")
    git_push()
    print("完成 ✅ 你的 RSS 已更新并可在 Apple Podcast 订阅。")

if __name__ == "__main__":
    main()
