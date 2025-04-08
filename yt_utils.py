import os
from yt_dlp import YoutubeDL

def download_audio(url: str) -> str | None:
    os.makedirs('downloads', exist_ok=True)  # Create a folder for uploading files

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }
        ],
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'cookiefile': 'cookies.txt',  # 🔥 ВАЖНО: добавили cookies
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            return mp3_filename if os.path.exists(mp3_filename) else None
    except Exception as e:
        print(f"❌ Ошибка при скачивании: {e}")
        return None