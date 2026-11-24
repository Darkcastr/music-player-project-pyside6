from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class AudioPlayer(QObject):
    position_changed = Signal(int)
    duration_changed = Signal(int)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        self.player.positionChanged.connect(self.position_changed.emit)
        self.player.durationChanged.connect(self.duration_changed.emit)

    def load(self, file_path):
        self.player.setSource(QUrl.fromLocalFile(file_path))

    def play(self):
        self.player.play()

    def pause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()

    def seek(self, position_ms):
        self.player.setPosition(position_ms)

    def set_volume(self, percent):
        self.audio_output.setVolume(percent / 100)

    def set_muted(self, muted):
        self.audio_output.setMuted(muted)