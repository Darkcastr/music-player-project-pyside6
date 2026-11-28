import os

from mutagen import File

AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".flac")


def read_track(path):
    title = os.path.splitext(os.path.basename(path))[0]
    artist = "Unknown artist"
    duration = 0

    try:
        audio = File(path, easy=True)
        if audio is not None:
            title = audio.get("title", [title])[0]
            artist = audio.get("artist", [artist])[0]
            if audio.info:
                duration = int(audio.info.length)
    except Exception:
        pass

    return {"path": path, "title": title, "artist": artist, "duration": duration}


def scan_folder(folder):
    paths = []
    for root, _, files in os.walk(folder):
        for name in sorted(files):
            if name.lower().endswith(AUDIO_EXTENSIONS):
                paths.append(os.path.join(root, name))
    return paths