import customtkinter as ctk
import os
import threading
from typing import Literal, Dict
from widgets import (
    AddedVideo, DownloadingVideo, DownloadedVideo,
)
from widgets import (
    AddedPlayList, DownloadingPlayList, DownloadedPlayList,
)
from widgets import (
    SettingPanel
)
from Services import (
    LoadingIndicatorController,
    LoadManager,
    DownloadManager,
    ThemeManager
)
from functions import (
    save_settings,
    clear_temp_files
)


class App(ctk.CTk):
    def __init__(
            self,
            theme_settings: Dict = None,
            general_settings: Dict = None):

        super().__init__()
        # root width height
        self.root_width = self.winfo_width()
        self.root_height = self.winfo_height()

        # widgets size resetting check
        self.widget_size_reset_needed = True
        self.geometry_tracker_running = False

        # theme & general settings
        self.theme_settings = theme_settings
        self.general_settings = general_settings

        # download method
        self.selected_download_mode = "video"

        # check if any video added or downloading or downloaded
        self.is_content_downloading = False
        self.is_content_downloaded = False
        self.is_content_added = False

        # widgets
        self.url_entry = None
        self.add_url_btn = None

        self.video_radio_btn = None
        self.playlist_radio_btn = None

        self.navigate_added_frame_btn = None
        self.navigate_downloading_frame_btn = None
        self.navigate_downloaded_frame_btn = None

        self.added_content_scroll_frame = None
        self.downloading_content_scroll_frame = None
        self.downloaded_content_scroll_frame = None

        self.added_frame_info_label = None
        self.downloading_frame_info_label = None
        self.downloaded_frame_info_label = None

        self.added_frame_info_label_placed = False
        self.downloading_frame_info_label_placed = False
        self.downloaded_frame_info_label_placed = False

        self.settings_panel = None
        self.settings_btn = None

    def create_widgets(self):
        self.url_entry = ctk.CTkEntry(
            master=self,
            height=40,
            placeholder_text="Enter Youtube URL"
        )

        self.video_radio_btn = ctk.CTkRadioButton(
            master=self, text="Video",
            radiobutton_width=16,
            radiobutton_height=16,
            width=60,
            height=18,
            command=lambda: self.select_download_mode("video")
        )
        self.video_radio_btn.select()

        self.playlist_radio_btn = ctk.CTkRadioButton(
            master=self,
            text="Playlist",
            radiobutton_width=16,
            radiobutton_height=16,
            width=60,
            height=18,
            command=lambda: self.select_download_mode("playlist")
        )

        self.add_url_btn = ctk.CTkButton(
            master=self,
            text="Add +",
            height=40,
            width=100,
            border_width=2,
            command=self.add_video_playlist
        )

        self.added_content_scroll_frame = ctk.CTkScrollableFrame(master=self)
        self.downloading_content_scroll_frame = ctk.CTkScrollableFrame(master=self)
        self.downloaded_content_scroll_frame = ctk.CTkScrollableFrame(master=self)
        self.settings_btn = ctk.CTkButton(
            master=self,
            text="Setting"
        )

        self.navigate_added_frame_btn = ctk.CTkButton(
            master=self,
            text="Added",
            height=40,
            command=lambda: self.place_frame(self.added_content_scroll_frame, "added")
        )

        self.navigate_downloading_frame_btn = ctk.CTkButton(
            master=self,
            text="Downloading",
            height=40,
            command=lambda: self.place_frame(self.downloading_content_scroll_frame, "downloading")
        )

        self.navigate_downloaded_frame_btn = ctk.CTkButton(
            master=self,
            text="Downloaded",
            height=40,
            command=lambda: self.place_frame(self.downloaded_content_scroll_frame, "downloaded")
        )

        self.added_frame_info_label = ctk.CTkLabel(
            master=self,
            text="Added videos & playlists will be display here.",
        )

        self.downloading_frame_info_label = ctk.CTkLabel(
            master=self,
            text="Downloading videos & playlists will be display here.",
        )

        self.downloaded_frame_info_label = ctk.CTkLabel(
            master=self,
            text="Downloaded videos & playlists will be display here.",
        )

        self.settings_panel = SettingPanel(
            master=self,
            theme_settings=self.theme_settings,
            general_settings=self.general_settings,
            theme_settings_change_callback=self.update_theme_settings,
            general_settings_change_callback=self.update_general_settings
        )

        self.settings_btn = ctk.CTkButton(
            master=self,
            text="⚡",
            border_spacing=0,
            hover=False,
            width=30,
            height=40,
            command=self.open_settings
        )

    def place_widgets(self):
        self.settings_btn.place(x=-5, y=4)
        self.url_entry.place(x=43, y=4)
        self.add_url_btn.place(y=4)
        self.video_radio_btn.place(y=5)
        self.playlist_radio_btn.place(y=25)
        self.navigate_added_frame_btn.place(y=50, x=10)
        self.navigate_downloading_frame_btn.place(y=50)
        self.navigate_downloaded_frame_btn.place(y=50)
        self.place_frame(self.added_content_scroll_frame, "added")
        self.bind("<Configure>", self.run_geometry_tracker)

    def place_forget_frames(self):
        self.added_content_scroll_frame.place_forget()
        self.downloading_content_scroll_frame.place_forget()
        self.downloaded_content_scroll_frame.place_forget()

    def place_forget_labels(self):
        self.added_frame_info_label_placed = False
        self.downloading_frame_info_label_placed = False
        self.downloaded_frame_info_label_placed = False
        self.added_frame_info_label.place_forget()
        self.downloading_frame_info_label.place_forget()
        self.downloaded_frame_info_label.place_forget()

    def place_label(self, frame_name: str):
        self.place_forget_labels()
        if frame_name == "added" and self.is_content_added is not True:
            self.added_frame_info_label_placed = True
            self.added_frame_info_label.place(y=self.winfo_height() / 2 + 45, x=self.winfo_width() / 2, anchor="center")
        elif frame_name == "downloading" and self.is_content_downloading is not True:
            self.downloading_frame_info_label_placed = True
            self.downloading_frame_info_label.place(y=self.winfo_height() / 2 + 45, x=self.winfo_width() / 2,
                                                    anchor="center")
        elif frame_name == "downloaded" and self.is_content_downloaded is not True:
            self.downloaded_frame_info_label_placed = True
            self.downloaded_frame_info_label.place(y=self.winfo_height() / 2 + 45, x=self.winfo_width() / 2,
                                                   anchor="center")

    def place_frame(self, frame: ctk.CTkScrollableFrame, frame_name: str):
        self.place_forget_frames()
        frame.place(y=90, x=10)
        self.place_label(frame_name)

    def configure_widgets_size(self):
        root_width = self.winfo_width()
        root_height = self.winfo_height()
        self.url_entry.configure(width=root_width - 250)

        btn_width = (root_width - 26) / 3
        self.navigate_added_frame_btn.configure(width=btn_width)
        self.navigate_downloading_frame_btn.configure(width=btn_width)
        self.navigate_downloaded_frame_btn.configure(width=btn_width)

        self.navigate_downloading_frame_btn.place(x=btn_width + 10 + 3)
        self.navigate_downloaded_frame_btn.place(x=btn_width * 2 + 10 + 6)

        self.video_radio_btn.place(x=self.winfo_width() - 190)
        self.playlist_radio_btn.place(x=self.winfo_width() - 190)
        self.add_url_btn.place(x=self.winfo_width() - 110)

        if self.added_frame_info_label_placed:
            self.place_label("added")
        elif self.downloading_frame_info_label_placed:
            self.place_label("downloading")
        elif self.downloaded_frame_info_label_placed:
            self.place_label("downloaded")

        frame_height = root_height - 105
        frame_width = root_width - 40
        self.added_content_scroll_frame.configure(
            height=frame_height,
            width=frame_width
        )
        self.downloading_content_scroll_frame.configure(
            height=frame_height,
            width=frame_width
        )
        self.downloaded_content_scroll_frame.configure(
            height=frame_height,
            width=frame_width
        )

    def geometry_tracker(self):
        self.geometry_tracker_running = True
        geometry_changed = False

        if self.root_width != self.winfo_width() or self.root_height != self.winfo_height():
            geometry_changed = True
            self.widget_size_reset_needed = True
            self.root_width = self.winfo_width()
            self.root_height = self.winfo_height()

        if self.widget_size_reset_needed and geometry_changed is False:
            self.geometry_tracker_running = False
            self.widget_size_reset_needed = False
            self.configure_widgets_size()
        elif self.widget_size_reset_needed is False and geometry_changed is False:
            self.geometry_tracker_running = False
            pass
        else:
            self.after(200, self.geometry_tracker)

    def run_geometry_tracker(self, _event):
        if not self.geometry_tracker_running:
            self.geometry_tracker()

    def set_accent_color(self):
        self.settings_btn.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"]
        )
        self.video_radio_btn.configure(
            fg_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.playlist_radio_btn.configure(
            fg_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.add_url_btn.configure(
            border_color=self.theme_settings["root"]["accent_color"]["normal"],
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.navigate_added_frame_btn.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.navigate_downloading_frame_btn.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.navigate_downloaded_frame_btn.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.added_frame_info_label.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.downloading_frame_info_label.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.downloaded_frame_info_label.configure(
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )

    def set_widgets_colors(self):
        self.configure(fg_color=self.theme_settings["root"]["fg_color"]["normal"])

        self.settings_btn.configure(
            fg_color=self.theme_settings["root"]["fg_color"]["normal"],
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            hover=False,
        )

        self.url_entry.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["url_entry"]["fg_color"]["normal"],
            border_color=self.theme_settings["url_entry"]["border_color"]["normal"],
            text_color=self.theme_settings["url_entry"]["text_color"]["normal"]
        )

        self.video_radio_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            text_color=self.theme_settings["url_entry"]["text_color"]["normal"],
        )
        self.playlist_radio_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            text_color=self.theme_settings["url_entry"]["text_color"]["normal"]
        )

        self.add_url_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["url_adding_button"]["fg_color"]["normal"],
            hover=False,
        )

        self.navigate_added_frame_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"],
            hover=False,
        )
        self.navigate_downloading_frame_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"],
            hover=False,
        )
        self.navigate_downloaded_frame_btn.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"],
            hover=False,
        )

        self.added_content_scroll_frame.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_frame"]["fg_color"]["normal"]
        )
        self.downloading_content_scroll_frame.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_frame"]["fg_color"]["normal"]
        )
        self.downloaded_content_scroll_frame.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            fg_color=self.theme_settings["navigation_frame"]["fg_color"]["normal"]
        )
        self.added_frame_info_label.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
        )
        self.downloading_frame_info_label.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )
        self.downloaded_frame_info_label.configure(
            bg_color=self.theme_settings["root"]["fg_color"]["normal"],
            text_color=self.theme_settings["root"]["accent_color"]["normal"],
        )

        self.bind_widget_events()

    def bind_widget_events(self):
        def on_mouse_enter_url_entry(_event):
            self.url_entry.configure(
                fg_color=self.theme_settings["url_entry"]["fg_color"]["hover"],
                border_color=self.theme_settings["url_entry"]["border_color"]["hover"],
                text_color=self.theme_settings["url_entry"]["text_color"]["hover"],
            )

        def on_mouse_leave_url_entry(_event):
            self.url_entry.configure(
                fg_color=self.theme_settings["url_entry"]["fg_color"]["normal"],
                border_color=self.theme_settings["url_entry"]["border_color"]["normal"],
                text_color=self.theme_settings["url_entry"]["text_color"]["normal"],
            )

        self.url_entry.bind("<Enter>", on_mouse_enter_url_entry)
        self.url_entry.bind("<Leave>", on_mouse_leave_url_entry)

        ######################################################################################

        def on_mouse_enter_settings_btn(_event):
            self.settings_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
            )

        def on_mouse_leave_settings_btn(_event):
            self.settings_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
            )

        self.settings_btn.bind("<Enter>", on_mouse_enter_settings_btn)
        self.settings_btn.bind("<Leave>", on_mouse_leave_settings_btn)

        ######################################################################################

        def on_mouse_enter_video_radio_btn(_event):
            self.video_radio_btn.configure(
                text_color=self.theme_settings["url_entry"]["text_color"]["hover"],
                fg_color=self.theme_settings["root"]["accent_color"]["hover"]
            )

        def on_mouse_leave_video_radio_btn(_event):
            self.video_radio_btn.configure(
                text_color=self.theme_settings["url_entry"]["text_color"]["normal"],
                fg_color=self.theme_settings["root"]["accent_color"]["normal"]
            )

        self.video_radio_btn.bind("<Enter>", on_mouse_enter_video_radio_btn)
        self.video_radio_btn.bind("<Leave>", on_mouse_leave_video_radio_btn)

        ######################################################################################

        def on_mouse_enter_playlist_radio_btn(_event):
            self.playlist_radio_btn.configure(
                text_color=self.theme_settings["url_entry"]["text_color"]["hover"],
                fg_color=self.theme_settings["root"]["accent_color"]["hover"]
            )

        def on_mouse_leave_playlist_radio_btn(_event):
            self.playlist_radio_btn.configure(
                text_color=self.theme_settings["url_entry"]["text_color"]["normal"],
                fg_color=self.theme_settings["root"]["accent_color"]["normal"]
            )

        self.playlist_radio_btn.bind("<Enter>", on_mouse_enter_playlist_radio_btn)
        self.playlist_radio_btn.bind("<Leave>", on_mouse_leave_playlist_radio_btn)

        ######################################################################################

        def on_mouse_enter_add_video_playlist_btn(_event):
            self.add_url_btn.configure(
                border_color=self.theme_settings["root"]["accent_color"]["hover"],
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
                fg_color=self.theme_settings["url_adding_button"]["fg_color"]["hover"],
            )

        def on_mouse_leave_add_video_playlist_btn(_event):
            self.add_url_btn.configure(
                border_color=self.theme_settings["root"]["accent_color"]["normal"],
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
                fg_color=self.theme_settings["url_adding_button"]["fg_color"]["normal"],
            )

        self.add_url_btn.bind("<Enter>", on_mouse_enter_add_video_playlist_btn)
        self.add_url_btn.bind("<Leave>", on_mouse_leave_add_video_playlist_btn)

        ######################################################################################

        def on_mouse_enter_navigate_added_frame_btn(_event):
            self.navigate_added_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["hover"]
            )

        def on_mouse_leave_navigate_added_frame_btn(_event):
            self.navigate_added_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"]
            )

        self.navigate_added_frame_btn.bind("<Enter>", on_mouse_enter_navigate_added_frame_btn)
        self.navigate_added_frame_btn.bind("<Leave>", on_mouse_leave_navigate_added_frame_btn)

        ######################################################################################

        def on_mouse_enter_navigate_downloading_frame_btn(_event):
            self.navigate_downloading_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["hover"]
            )

        def on_mouse_leave_navigate_downloading_frame_btn(_event):
            self.navigate_downloading_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"]
            )

        self.navigate_downloading_frame_btn.bind("<Enter>", on_mouse_enter_navigate_downloading_frame_btn)
        self.navigate_downloading_frame_btn.bind("<Leave>", on_mouse_leave_navigate_downloading_frame_btn)

        ######################################################################################

        def on_mouse_enter_navigate_downloaded_frame_btn(_event):
            self.navigate_downloaded_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["hover"]
            )

        def on_mouse_leave_navigate_downloaded_frame_btn(_event):
            self.navigate_downloaded_frame_btn.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
                fg_color=self.theme_settings["navigation_button"]["fg_color"]["normal"]
            )

        self.navigate_downloaded_frame_btn.bind("<Enter>", on_mouse_enter_navigate_downloaded_frame_btn)
        self.navigate_downloaded_frame_btn.bind("<Leave>", on_mouse_leave_navigate_downloaded_frame_btn)

        #######################################################################################

        def on_mouse_enter_added_frame_info_label(_event):
            self.added_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
            )

        def on_mouse_leave_added_frame_info_label(_event):
            self.added_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
            )

        self.added_frame_info_label.bind("<Enter>", on_mouse_enter_added_frame_info_label)
        self.added_frame_info_label.bind("<Leave>", on_mouse_leave_added_frame_info_label)

        #######################################################################################

        def on_mouse_enter_downloading_frame_info_label(_event):
            self.downloading_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
            )

        def on_mouse_leave_downloading_frame_info_label(_event):
            self.downloading_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
            )

        self.downloading_frame_info_label.bind("<Enter>", on_mouse_enter_downloading_frame_info_label)
        self.downloading_frame_info_label.bind("<Leave>", on_mouse_leave_downloading_frame_info_label)

        #######################################################################################

        def on_mouse_enter_downloaded_frame_info_label(_event):
            self.downloaded_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["hover"],
            )

        def mouse_ot_downloaded_frame_info_label(_event):
            self.downloaded_frame_info_label.configure(
                text_color=self.theme_settings["root"]["accent_color"]["normal"],
            )

        self.downloaded_frame_info_label.bind("<Enter>", on_mouse_enter_downloaded_frame_info_label)
        self.downloaded_frame_info_label.bind("<Leave>", mouse_ot_downloaded_frame_info_label)

    def set_widgets_fonts(self):
        self.url_entry.configure(
            font=ctk.CTkFont(
                family="arial",
                size=16,
                weight="normal",
                slant="italic",
                underline=True
            )
        )

        self.video_radio_btn.configure(font=("Monospace", 12, "bold"))
        self.playlist_radio_btn.configure(font=("Monospace", 12, "bold"))
        self.add_url_btn.configure(font=("arial", 15, "bold"))
        self.navigate_added_frame_btn.configure(font=("arial", 15, "bold"))

        font_style = ctk.CTkFont(
            family="arial",
            size=16,
            weight="bold",
            slant="italic"
        )
        self.added_frame_info_label.configure(font=font_style)
        self.downloading_frame_info_label.configure(font=font_style)
        self.downloaded_frame_info_label.configure(font=font_style)
        self.navigate_downloading_frame_btn.configure(font=("arial", 15, "bold"))
        self.navigate_downloaded_frame_btn.configure(font=("arial", 15, "bold"))
        self.settings_btn.configure(font=("arial", 25, "normal"))

    def select_download_mode(self, download_mode):
        self.selected_download_mode = download_mode
        if download_mode == "playlist":
            self.video_radio_btn.deselect()
        else:
            self.playlist_radio_btn.deselect()

    def add_video_playlist(self):
        self.is_content_added = True
        self.added_frame_info_label.place_forget()
        yt_url = self.url_entry.get()
        if self.selected_download_mode == "video":
            AddedVideo(
                master=self.added_content_scroll_frame,
                height=70,
                width=self.added_content_scroll_frame.winfo_width(),
                # video url
                video_url=yt_url,
                # download btn callback
                video_download_button_click_callback=self.download_video,
                # color info
                accent_color=self.theme_settings["root"]["accent_color"],
                theme_settings=self.theme_settings["video_object"]
            ).pack(fill="x", pady=2)

        else:
            AddedPlayList(
                master=self.added_content_scroll_frame,
                height=85,
                width=self.added_content_scroll_frame.winfo_width(),

                playlist_download_button_click_callback=self.download_playlist,
                video_download_button_click_callback=self.download_video,
                playlist_url=yt_url,

                accent_color=self.theme_settings["root"]["accent_color"],
                theme_settings=self.theme_settings["video_object"]
            ).pack(fill="x", pady=2)

    def download_video(self, video: AddedVideo):
        self.is_content_downloading = True
        self.downloading_frame_info_label.place_forget()
        DownloadingVideo(
            master=self.downloading_content_scroll_frame,
            height=70,
            width=self.downloading_content_scroll_frame.winfo_width(),
            # video info
            channel_url=video.channel_url,
            video_url=video.video_url,
            channel=video.channel,
            video_title=video.video_title,
            video_stream_data=video.video_stream_data,
            length=video.length,
            thumbnails=video.thumbnails,
            # download info
            download_quality=video.download_quality,
            download_type=video.download_type,
            download_directory=self.general_settings['download_directory'],
            video_download_complete_callback=self.downloaded_video,

            accent_color=self.theme_settings["root"]["accent_color"],
            theme_settings=self.theme_settings["video_object"]
        ).pack(fill="x", pady=2)

    def download_playlist(self, playlist: AddedPlayList):
        self.is_content_downloading = True
        self.downloading_frame_info_label.place_forget()
        DownloadingPlayList(
            master=self.downloading_content_scroll_frame,
            height=85,
            width=self.downloading_content_scroll_frame.winfo_width(),
            # video info
            channel_url=playlist.channel_url,
            channel=playlist.channel,
            playlist_title=playlist.playlist_title,
            playlist_video_count=playlist.playlist_video_count,
            playlist_url=playlist.playlist_url,
            # play list videos
            videos=playlist.videos,
            # download directory
            download_directory=self.general_settings['download_directory'],
            # playlist download completed callback functions
            playlist_download_complete_callback=self.downloaded_playlist,
            # color info
            accent_color=self.theme_settings["root"]["accent_color"],
            theme_settings=self.theme_settings["video_object"]
        ).pack(fill="x", pady=2)

    def downloaded_video(self, video: DownloadingVideo):
        self.is_content_downloaded = True
        self.downloaded_frame_info_label.place_forget()
        DownloadedVideo(
            master=self.downloaded_content_scroll_frame,
            height=70,
            width=self.downloaded_content_scroll_frame.winfo_width(),

            thumbnails=video.thumbnails,
            video_title=video.video_title,
            channel=video.channel,
            channel_url=video.channel_url,
            video_url=video.video_url,
            file_size=video.file_size,
            length=video.length,

            download_path=video.download_file_name,
            download_quality=video.download_quality,
            download_type=video.download_type,

            theme_settings=self.theme_settings["video_object"],
            accent_color=self.theme_settings["root"]["accent_color"],
        ).pack(fill="x", pady=2)

    def downloaded_playlist(self, playlist: DownloadingPlayList):
        self.is_content_downloaded = True
        self.downloaded_frame_info_label.place_forget()
        DownloadedPlayList(
            master=self.downloaded_content_scroll_frame,
            height=85,
            width=self.downloaded_content_scroll_frame.winfo_width(),
            # playlist url
            channel_url=playlist.channel_url,
            channel=playlist.channel,
            playlist_title=playlist.playlist_title,
            playlist_video_count=playlist.playlist_video_count,
            playlist_url=playlist.playlist_url,
            videos=playlist.videos,
            # color info
            accent_color=self.theme_settings["root"]["accent_color"],
            theme_settings=self.theme_settings["video_object"],
        ).pack(fill="x", pady=2)

    def update_theme_settings(self, theme_settings: Dict, updated: Literal["accent_color", "theme_mode"] = None):
        self.theme_settings = theme_settings
        if updated == "theme_mode":
            ctk.set_appearance_mode(theme_settings["root"]["theme_mode"])
        if updated == "accent_color":
            self.set_accent_color()
            ThemeManager.update_accent_color(theme_settings["root"]["accent_color"])
        save_settings("settings/theme.json", self.theme_settings)

    def update_general_settings(self, general_settings):
        self.general_settings = general_settings
        self.configure_services_values()
        save_settings("settings/general.json", self.general_settings)

    def open_settings(self):
        self.settings_panel.place(relwidth=1, relheight=1)
        self.settings_btn.configure(command=self.close_settings)

    def close_settings(self):
        self.settings_panel.place_forget()
        self.settings_btn.configure(command=self.open_settings)

    def on_app_closing(self):
        self.general_settings['geometry'] = self.geometry()
        clear_temp_files("temp")
        save_settings("settings/general.json", self.general_settings)
        self.destroy()
        os._exit(0)

    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_app_closing)
        self.mainloop()

    def configure_services_values(self):
        DownloadManager.set_max_concurrent_downloads(self.general_settings["simultaneous_downloads"])
        LoadManager.set_max_concurrent_loads(self.general_settings["simultaneous_loads"])

    @staticmethod
    def initiate_services():
        threading.Thread(target=ThemeManager.theme_tracker).start()
        threading.Thread(target=LoadingIndicatorController.start).start()
        # loading and downloading handle
        threading.Thread(target=LoadManager.manage_load_queue).start()
        threading.Thread(target=DownloadManager.manage_download_queue).start()
