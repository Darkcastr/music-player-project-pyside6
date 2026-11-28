import os

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QSlider, QListWidget, QListWidgetItem, QStyle,
    QInputDialog, QMessageBox
)

from core.player import AudioPlayer
from core.library import read_track, scan_folder
from core.queue_manager import PlayQueue, REPEAT_OFF, REPEAT_ALL, REPEAT_ONE
from database import (
    get_user_id, get_favorites, add_favorite, remove_favorite,
    create_playlist, rename_playlist, delete_playlist, get_playlists,
    add_track_to_playlist, remove_track_from_playlist, get_playlist_paths,
)

def format_time(ms):
    total_seconds = ms // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"

class ClickableSlider(QSlider):
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            value = QStyle.sliderValueFromPosition(
                self.minimum(), self.maximum(),
                int(event.position().x()), self.width(),
            )
            self.setValue(value)
            self.sliderMoved.emit(value)
        super().mousePressEvent(event)

class PlayerWindow(QWidget):
    logout_requested = Signal()

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.audio = AudioPlayer()
        self.tracks = []
        self.queue = PlayQueue()
        self.position = 0
        self.user_id = get_user_id(username)
        self.favorites = get_favorites(self.user_id)
        self.current_playlist_id = None
        self.playlist_paths = set()
        self.setWindowTitle("Music Player")
        self.resize(800, 500)

        welcome_label = QLabel(f"Welcome, {username}")
        logout_button = QPushButton("Log out")

        top_bar = QHBoxLayout()
        top_bar.addWidget(welcome_label)
        top_bar.addStretch()
        top_bar.addWidget(logout_button)

        self.track_list = QListWidget()
        self.playlist_list = QListWidget()
        new_playlist_button = QPushButton("New")
        rename_playlist_button = QPushButton("Rename")
        delete_playlist_button = QPushButton("Delete")

        playlist_buttons = QHBoxLayout()
        playlist_buttons.addWidget(new_playlist_button)
        playlist_buttons.addWidget(rename_playlist_button)
        playlist_buttons.addWidget(delete_playlist_button)

        sidebar = QVBoxLayout()
        sidebar.addWidget(QLabel("Playlists"))
        sidebar.addWidget(self.playlist_list, stretch=1)
        sidebar.addLayout(playlist_buttons)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(200)

        body = QHBoxLayout()
        body.addWidget(sidebar_widget)
        body.addWidget(self.track_list, stretch=1)

        self.now_playing_label = QLabel("No track loaded")
        self.now_playing_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.elapsed_label = QLabel("0:00")
        self.total_label = QLabel("0:00")
        self.seek_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)

        seek_row = QHBoxLayout()
        seek_row.addWidget(self.elapsed_label)
        seek_row.addWidget(self.seek_slider, stretch=1)
        seek_row.addWidget(self.total_label)

        add_files_button = QPushButton("Add files")
        add_folder_button = QPushButton("Add folder")
        play_button = QPushButton("Play")
        pause_button = QPushButton("Pause")
        stop_button = QPushButton("Stop")

        prev_button = QPushButton("Previous")
        next_button = QPushButton("Next")
        self.shuffle_button = QPushButton("Shuffle")
        self.shuffle_button.setCheckable(True)
        self.repeat_button = QPushButton("Repeat: Off")

        self.favorite_button = QPushButton("★ Favorite")
        self.favorites_only_button = QPushButton("Favorites only")
        self.favorites_only_button.setCheckable(True)

        add_to_playlist_button = QPushButton("Add to playlist")
        remove_from_playlist_button = QPushButton("Remove from playlist")

        controls = QHBoxLayout()
        controls.addWidget(add_files_button)
        controls.addWidget(add_folder_button)
        controls.addStretch()
        controls.addWidget(prev_button)
        controls.addWidget(play_button)
        controls.addWidget(pause_button)
        controls.addWidget(stop_button)
        controls.addWidget(next_button)

        self.mute_button = QPushButton("Mute")
        self.mute_button.setCheckable(True)
        self.volume_slider = ClickableSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(150)

        volume_row = QHBoxLayout()
        volume_row.addWidget(self.shuffle_button)
        volume_row.addWidget(self.repeat_button)
        volume_row.addWidget(self.favorite_button)
        volume_row.addWidget(self.favorites_only_button)
        volume_row.addWidget(add_to_playlist_button)
        volume_row.addWidget(remove_from_playlist_button)
        volume_row.addStretch()
        volume_row.addWidget(self.mute_button)
        volume_row.addWidget(self.volume_slider)

        layout = QVBoxLayout()
        layout.addLayout(top_bar)
        layout.addLayout(body, stretch=1)
        layout.addWidget(self.now_playing_label)
        layout.addLayout(seek_row)
        layout.addLayout(controls)
        layout.addLayout(volume_row)
        self.setLayout(layout)

        logout_button.clicked.connect(self.logout_requested.emit)
        add_files_button.clicked.connect(self.add_files)
        add_folder_button.clicked.connect(self.add_folder)
        play_button.clicked.connect(self.audio.play)
        pause_button.clicked.connect(self.audio.pause)
        stop_button.clicked.connect(self.audio.stop)

        self.track_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.audio.position_changed.connect(self.on_position_changed)
        self.audio.duration_changed.connect(self.on_duration_changed)
        self.seek_slider.sliderMoved.connect(self.audio.seek)
        self.volume_slider.valueChanged.connect(self.audio.set_volume)
        self.mute_button.toggled.connect(self.audio.set_muted)

        prev_button.clicked.connect(self.play_previous)
        next_button.clicked.connect(self.play_next)
        self.shuffle_button.toggled.connect(self.on_shuffle_toggled)
        self.repeat_button.clicked.connect(self.cycle_repeat)
        self.audio.track_finished.connect(self.on_track_finished)
        self.favorite_button.clicked.connect(self.toggle_favorite)
        self.favorites_only_button.toggled.connect(self.apply_filter)

        new_playlist_button.clicked.connect(self.new_playlist)
        rename_playlist_button.clicked.connect(self.rename_selected_playlist)
        delete_playlist_button.clicked.connect(self.delete_selected_playlist)
        add_to_playlist_button.clicked.connect(self.add_selected_to_playlist)
        remove_from_playlist_button.clicked.connect(self.remove_selected_from_playlist)
        self.playlist_list.currentItemChanged.connect(self.on_playlist_selected)

        self.load_playlists()

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add audio files",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac);;All Files (*)",
        )
        self.add_tracks(paths)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Add folder")
        if folder:
            self.add_tracks(scan_folder(folder))

    def add_tracks(self, paths):
        known = {track["path"] for track in self.tracks}
        for path in paths:
            if path in known:
                continue
            track = read_track(path)
            self.tracks.append(track)
            self.track_list.addItem(self.track_text(track))
        self.apply_filter()

    def track_text(self, track):
        star = "★ " if track["path"] in self.favorites else ""
        duration_text = format_time(track["duration"] * 1000)
        return f"{star}{track['title']} - {track['artist']}   [{duration_text}]"

    def refresh_item(self, row):
        self.track_list.item(row).setText(self.track_text(self.tracks[row]))

    def toggle_favorite(self):
        row = self.track_list.currentRow()
        if row < 0:
            return
        path = self.tracks[row]["path"]
        if path in self.favorites:
            remove_favorite(self.user_id, path)
            self.favorites.discard(path)
        else:
            add_favorite(self.user_id, path)
            self.favorites.add(path)
        self.refresh_item(row)
        self.apply_filter()

    def apply_filter(self, _checked=None):
        only_favorites = self.favorites_only_button.isChecked()
        for row, track in enumerate(self.tracks):
            path = track["path"]
            hidden = only_favorites and path not in self.favorites
            if self.current_playlist_id is not None and path not in self.playlist_paths:
                hidden = True
            self.track_list.item(row).setHidden(hidden)

    def load_playlists(self, select_id=None):
        self.playlist_list.blockSignals(True)
        self.playlist_list.clear()

        all_item = QListWidgetItem("All songs")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        self.playlist_list.addItem(all_item)

        selected_row = 0
        for playlist_id, name in get_playlists(self.user_id):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, playlist_id)
            self.playlist_list.addItem(item)
            if playlist_id == select_id:
                selected_row = self.playlist_list.count() - 1

        self.playlist_list.setCurrentRow(selected_row)
        self.playlist_list.blockSignals(False)
        self.on_playlist_selected()

    def on_playlist_selected(self, *_):
        item = self.playlist_list.currentItem()
        playlist_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.current_playlist_id = playlist_id

        if playlist_id is None:
            self.playlist_paths = set()
        else:
            paths = get_playlist_paths(self.user_id, playlist_id)
            self.playlist_paths = set(paths)
            self.add_tracks([p for p in paths if os.path.exists(p)])
        self.apply_filter()

    def new_playlist(self):
        name, ok = QInputDialog.getText(self, "New playlist", "Name:")
        if not ok:
            return
        success, result = create_playlist(self.user_id, name)
        if success:
            self.load_playlists(select_id=result)
        else:
            QMessageBox.warning(self, "New playlist", result)

    def rename_selected_playlist(self):
        if self.current_playlist_id is None:
            return
        old_name = self.playlist_list.currentItem().text()
        name, ok = QInputDialog.getText(
            self, "Rename playlist", "New name:", text=old_name
        )
        if not ok:
            return
        success, message = rename_playlist(self.user_id, self.current_playlist_id, name)
        if success:
            self.load_playlists(select_id=self.current_playlist_id)
        else:
            QMessageBox.warning(self, "Rename playlist", message)

    def delete_selected_playlist(self):
        if self.current_playlist_id is None:
            return
        name = self.playlist_list.currentItem().text()
        answer = QMessageBox.question(
            self, "Delete playlist",
            f"Delete \"{name}\"? Your songs will not be deleted.",
        )
        if answer == QMessageBox.StandardButton.Yes:
            delete_playlist(self.user_id, self.current_playlist_id)
            self.load_playlists()

    def add_selected_to_playlist(self):
        row = self.track_list.currentRow()
        if row < 0:
            return
        playlists = get_playlists(self.user_id)
        if not playlists:
            QMessageBox.information(self, "Add to playlist", "Create a playlist first.")
            return
        names = [name for _, name in playlists]
        choice, ok = QInputDialog.getItem(
            self, "Add to playlist", "Playlist:", names, 0, False
        )
        if not ok:
            return
        playlist_id = playlists[names.index(choice)][0]
        path = self.tracks[row]["path"]
        add_track_to_playlist(self.user_id, playlist_id, path)
        if playlist_id == self.current_playlist_id:
            self.playlist_paths.add(path)
            self.apply_filter()

    def remove_selected_from_playlist(self):
        row = self.track_list.currentRow()
        if row < 0 or self.current_playlist_id is None:
            return
        path = self.tracks[row]["path"]
        remove_track_from_playlist(self.user_id, self.current_playlist_id, path)
        self.playlist_paths.discard(path)
        self.apply_filter()

    def on_item_double_clicked(self, item):
        self.play_track(self.track_list.row(item))

    def play_track(self, index):
        track = self.tracks[index]
        self.queue.current = index
        self.track_list.setCurrentRow(index)
        self.now_playing_label.setText(f"{track['title']} - {track['artist']}")
        self.audio.load(track["path"])
        self.audio.play()

    def play_next(self):
        index = self.queue.next_index(len(self.tracks))
        if index is not None:
            self.play_track(index)

    def play_previous(self):
        if self.position > 3000 and self.queue.current != -1:
            self.audio.seek(0)
            return
        index = self.queue.previous_index(len(self.tracks))
        if index is not None:
            self.play_track(index)

    def on_track_finished(self):
        index = self.queue.next_index(len(self.tracks), auto=True)
        if index is None:
            self.audio.stop()
        elif index == self.queue.current:
            self.audio.seek(0)
            self.audio.play()
        else:
            self.play_track(index)

    def on_shuffle_toggled(self, checked):
        self.queue.shuffle = checked
        self.queue.history.clear()

    def cycle_repeat(self):
        order = [REPEAT_OFF, REPEAT_ALL, REPEAT_ONE]
        labels = {
            REPEAT_OFF: "Repeat: Off",
            REPEAT_ALL: "Repeat: All",
            REPEAT_ONE: "Repeat: One",
        }
        next_mode = order[(order.index(self.queue.repeat) + 1) % len(order)]
        self.queue.repeat = next_mode
        self.repeat_button.setText(labels[next_mode])

    def on_position_changed(self, position):
        self.position = position
        if not self.seek_slider.isSliderDown():
            self.seek_slider.setValue(position)
        self.elapsed_label.setText(format_time(position))

    def on_duration_changed(self, duration):
        self.seek_slider.setRange(0, duration)
        self.total_label.setText(format_time(duration))

    def closeEvent(self, event):
        self.audio.stop()
        super().closeEvent(event)