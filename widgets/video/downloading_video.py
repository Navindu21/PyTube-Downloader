from widgets.video import Video
import customtkinter as ctk
import threading
import time
import os
from tkinter import PhotoImage
from typing import Literal, List, Union, Any
from pytube import request as pytube_request
from settings import (
    GeneralSettings,
    ThemeSettings,
    ScaleSettings
)
from services import (
    DownloadManager
)
from utils import (
    GuiUtils,
    ValueConvertUtility,
    FileUtility
)


class DownloadingVideo(Video):
    def __init__(
            self,
            master: Any,
            width: int = 0,
            height: int = 0,
            # download quality & type
            download_quality: Literal["128kbps", "360p", "720p"] = "720p",
            download_type: Literal["Video", "Audio"] = "Video",
            # video details
            video_title: str = "-------",
            channel: str = "-------",
            video_url: str = "-------",
            channel_url: str = "-------",
            length: int = 0,
            thumbnails: List[PhotoImage] = (None, None),
            # video stream data
            video_stream_data: property = None,
            # video download callback utils @ only use if mode is video
            video_download_complete_callback: callable = None,
            # state callback utils @ only use if mode is video
            mode: Literal["video", "playlist"] = "video",
            video_download_status_callback: callable = None,
            video_download_progress_callback: callable = None):

        # download status track and callback
        self.download_state: Literal["waiting", "downloading", "failed", "completed", "removed"] = "waiting"
        self.pause_requested: bool = False
        self.pause_resume_btn_command: Literal["pause", "resume"] = "pause"
        # callback
        self.video_download_complete_callback: callable = video_download_complete_callback
        self.video_download_status_callback: callable = video_download_status_callback
        self.video_download_progress_callback: callable = video_download_progress_callback
        # selected download quality and type
        self.download_quality: Literal["128kbps", "360p", "720p"] = download_quality
        self.download_type: Literal["Video", "Audio"] = download_type
        self.video_stream_data: property = video_stream_data
        # playlist or video
        self.mode: Literal["video", "playlist"] = mode
        # widgets
        self.sub_frame: Union[ctk.CTkFrame, None] = None
        self.download_progress_bar: Union[ctk.CTkProgressBar, None] = None
        self.download_progress_label: Union[ctk.CTkLabel, None] = None
        self.download_percentage_label: Union[ctk.CTkLabel, None] = None
        self.download_type_label: Union[ctk.CTkLabel, None] = None
        self.net_speed_label: Union[ctk.CTkLabel, None] = None
        self.status_label: Union[ctk.CTkLabel, None] = None
        self.re_download_btn: Union[ctk.CTkButton, None] = None
        self.pause_resume_btn: Union[ctk.CTkButton, None] = None
        # download file info
        self.bytes_downloaded: int = 0
        self.file_size: int = 0
        self.converted_file_size: str = "0 B"
        self.download_file_name: str = ""

        super().__init__(
            master=master,
            height=height,
            width=width,
            video_url=video_url,
            channel_url=channel_url,
            thumbnails=thumbnails,
            video_title=video_title,
            channel=channel,
            length=length
        )

        self.set_video_data()
        threading.Thread(target=self.start_download_video, daemon=True).start()

    def start_download_video(self):
        scale = GeneralSettings.settings["scale_r"]
        y = ScaleSettings.settings["DownloadingVideo"][str(scale)]

        if GeneralSettings.settings["max_simultaneous_downloads"] > DownloadManager.active_download_count:
            DownloadManager.active_download_count += 1
            DownloadManager.active_downloads.append(self)
            threading.Thread(target=self.download_video, daemon=True).start()
            self.set_pause_btn()
            self.pause_resume_btn.place(y=y[6], relx=1, x=-80 * scale)
            self.net_speed_label.configure(text="0.0 B/s")
            self.download_progress_bar.set(0)
            self.download_percentage_label.configure(text="0.0 %")
            self.download_state = "downloading"
            if self.mode == "playlist":
                self.video_download_status_callback(self, self.download_state)
            self.display_status()

        else:
            self.set_waiting()

    def re_download_video(self):
        self.re_download_btn.place_forget()
        self.start_download_video()

    def display_status(self):
        if self.download_state == "failed":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["error_color"]["normal"],
                text="Failed"
            )
        elif self.download_state == "waiting":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"],
                text="Waiting"
            )
        elif self.download_state == "paused":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"],
                text="Paused"
            )
        elif self.download_state == "downloading":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"],
                text="Downloading"
            )
        elif self.download_state == "pausing":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"],
                text="Pausing"
            )
        elif self.download_state == "completed":
            self.status_label.configure(
                text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"],
                text="Downloaded"
            )

    def download_video(self):
        if not os.path.exists(GeneralSettings.settings["download_directory"]):
            try:
                FileUtility.create_directory(GeneralSettings.settings["download_directory"])
            except Exception as error:
                print("@2 : ", error)
                self.set_download_failed()
                return

        stream = None
        self.bytes_downloaded = 0
        self.download_file_name = (
                f"{GeneralSettings.settings["download_directory"]}\\" +
                f"{FileUtility.sanitize_filename(f"{self.channel} - {self.video_title}")}"
            )
        try:
            self.download_type_label.configure(text=f"{self.download_type} : {self.download_quality}")
            if self.download_type == "Video":
                stream = self.video_stream_data.get_by_resolution(self.download_quality)
                self.download_file_name += ".mp4"
            else:
                stream = self.video_stream_data.get_audio_only()
                self.download_file_name += ".mp3"
            self.file_size = stream.filesize
            self.converted_file_size = ValueConvertUtility.convert_size(self.file_size, 2)
            self.download_file_name = FileUtility.get_available_file_name(self.download_file_name)
            self.set_download_progress()
        except Exception as error:
            print("@1 : ", error)
            self.set_download_failed()

        try:
            with open(self.download_file_name, "wb") as self.video_file:
                stream = pytube_request.stream(stream.url)
                while 1:
                    try:
                        time_s = time.time()
                        if self.pause_requested:
                            if self.pause_resume_btn_command != "resume":
                                self.pause_resume_btn.configure(command=self.resume_downloading)
                                self.download_state = "paused"
                                if self.mode == "playlist":
                                    self.video_download_status_callback(self, self.download_state)
                                self.display_status()
                                self.set_resume_btn()
                                self.pause_resume_btn_command = "resume"
                            time.sleep(0.3)
                            continue
                        self.download_state = "downloading"
                        self.pause_resume_btn_command = "pause"
                        chunk = next(stream, None)
                        time_e = time.time()
                        if chunk:
                            self.video_file.write(chunk)
                            self.net_speed_label.configure(
                                text=ValueConvertUtility.convert_size(
                                    ((self.bytes_downloaded + len(chunk)) - self.bytes_downloaded) / (time_e - time_s),
                                    1
                                ) + "/s"
                            )
                            self.bytes_downloaded += len(chunk)
                            self.set_download_progress()
                        else:
                            if self.bytes_downloaded == self.file_size:
                                self.set_download_completed()
                                break
                            else:
                                self.set_download_failed()
                                break
                    except Exception as error:
                        print("@3 downloading_play_list.py : ", error)
                        self.set_download_failed()
                        break
        except Exception as error:
            print("@4 downloading_play_list.py : ", error)
            self.set_download_failed()

    def set_resume_btn(self):
        self.pause_resume_btn.configure(text="▷")

    def set_pause_btn(self):
        self.pause_resume_btn.configure(text="⏸")

    def pause_downloading(self):
        self.pause_resume_btn.configure(command=GuiUtils.do_nothing)
        self.download_state = "pausing"
        self.display_status()
        self.pause_requested = True

    def resume_downloading(self):
        self.pause_requested = False
        self.set_pause_btn()
        while self.download_state == "paused":
            time.sleep(0.3)
        self.pause_resume_btn.configure(command=self.pause_downloading)
        self.download_state = "downloading"
        if self.mode == "playlist":
            self.video_download_status_callback(self, self.download_state)
        self.display_status()

    def set_download_progress(self):
        completed_percentage = self.bytes_downloaded / self.file_size
        self.download_progress_bar.set(completed_percentage)
        self.download_percentage_label.configure(text=f"{round(completed_percentage * 100, 2)} %")
        self.download_progress_label.configure(
            text=f"{ValueConvertUtility.convert_size(self.bytes_downloaded, 2)} / {self.converted_file_size}"
        )
        if self.mode == "playlist":
            self.video_download_progress_callback()

    def set_download_failed(self):
        scale = GeneralSettings.settings["scale_r"]
        y = ScaleSettings.settings["DownloadingVideo"][str(scale)]

        if self.download_state != "removed":
            self.download_state = "failed"
            self.display_status()
            if self.mode == "playlist":
                self.video_download_status_callback(self, self.download_state)
            if self in DownloadManager.active_downloads:
                DownloadManager.active_downloads.remove(self)
                DownloadManager.active_download_count -= 1
            self.pause_resume_btn.place_forget()
            self.re_download_btn.place(y=y[7], relx=1, x=-80 * scale)

    def set_waiting(self):
        DownloadManager.queued_downloads.append(self)
        self.download_state = "waiting"
        if self.mode == "playlist":
            self.video_download_status_callback(self, self.download_state)
        self.display_status()
        self.pause_resume_btn.place_forget()
        self.download_progress_bar.set(0.5)
        self.download_percentage_label.configure(text="")
        self.net_speed_label.configure(text="")
        self.download_progress_label.configure(text="")
        self.download_type_label.configure(text="")

    def set_download_completed(self):
        if self in DownloadManager.active_downloads:
            DownloadManager.active_downloads.remove(self)
            DownloadManager.active_download_count -= 1
        self.pause_resume_btn.place_forget()
        self.download_state = "completed"
        self.display_status()
        if self.mode == "playlist":
            self.video_download_status_callback(self, self.download_state)
        if self.mode == "video":
            self.video_download_complete_callback(self)
            self.kill()

    def kill(self):
        if self in DownloadManager.queued_downloads:
            DownloadManager.queued_downloads.remove(self)
        if self in DownloadManager.active_downloads:
            DownloadManager.active_downloads.remove(self)
            DownloadManager.active_download_count -= 1
        self.download_state = "removed"
        if self.mode == "playlist":
            self.video_download_status_callback(self, self.download_state)
        super().kill()

    # create widgets
    def create_widgets(self):
        super().create_widgets()
        scale = GeneralSettings.settings["scale_r"]

        self.sub_frame = ctk.CTkFrame(
            self,
            height=self.height - 4,
        )

        self.download_progress_bar = ctk.CTkProgressBar(
            master=self.sub_frame,
            height=8 * scale
        )

        self.download_progress_label = ctk.CTkLabel(
            master=self.sub_frame,
            text="",
            font=("arial", 12 * scale, "bold"),
        )

        self.download_percentage_label = ctk.CTkLabel(
            master=self.sub_frame,
            text="",
            font=("arial", 12 * scale, "bold"),
        )

        self.download_type_label = ctk.CTkLabel(
            master=self.sub_frame,
            text="",
            font=("arial", 12 * scale, "normal"),
        )

        self.net_speed_label = ctk.CTkLabel(
            master=self.sub_frame,
            text="",
            font=("arial", 12 * scale, "normal"),
        )

        self.status_label = ctk.CTkLabel(
            master=self.sub_frame,
            text="",
            font=("arial", 12 * scale, "bold"),
        )

        self.re_download_btn = ctk.CTkButton(
            master=self,
            text="⟳",
            width=15 * scale,
            height=15 * scale,
            font=("arial", 20 * scale, "normal"),
            command=self.re_download_video,
            hover=False
        )

        self.pause_resume_btn = ctk.CTkButton(
            master=self,
            text="⏸",
            width=15 * scale,
            height=15 * scale,
            font=("arial", 20 * scale, "normal"),
            command=self.pause_downloading,
            hover=False
        )

    # configure widgets colors
    def on_mouse_enter_self(self, event):
        super().on_mouse_enter_self(event)
        self.sub_frame.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["hover"])
        self.re_download_btn.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["hover"])
        self.pause_resume_btn.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["hover"])

    def on_mouse_leave_self(self, event):
        super().on_mouse_leave_self(event)
        self.sub_frame.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"])
        self.re_download_btn.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"])
        self.pause_resume_btn.configure(fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"])

    def set_accent_color(self):
        super().set_accent_color()
        self.download_progress_bar.configure(
            progress_color=ThemeSettings.settings["root"]["accent_color"]["normal"]
        )
        self.re_download_btn.configure(
            text_color=ThemeSettings.settings["root"]["accent_color"]["normal"]
        )
        self.pause_resume_btn.configure(
            text_color=ThemeSettings.settings["root"]["accent_color"]["normal"]
        )

    def set_widgets_colors(self) -> None:
        super().set_widgets_colors()
        self.sub_frame.configure(
            fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"],
        )
        self.download_progress_label.configure(
            text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"]
        )
        self.download_percentage_label.configure(
            text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"]
        )
        self.download_type_label.configure(
            text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"]
        )
        self.net_speed_label.configure(
            text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"]
        )
        self.status_label.configure(
            text_color=ThemeSettings.settings["video_object"]["text_color"]["normal"]
        )
        self.re_download_btn.configure(
            fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"]
        )
        self.pause_resume_btn.configure(
            fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"]
        )

    def bind_widget_events(self):
        super().bind_widget_events()

        def on_mouse_enter_re_download_btn(event):
            self.re_download_btn.configure(
                fg_color=ThemeSettings.settings["video_object"]["fg_color"]["hover"],
                text_color=ThemeSettings.settings["root"]["accent_color"]["hover"]
            )
            self.on_mouse_enter_self(event)

        def on_mouse_leave_download_btn(_event):
            self.re_download_btn.configure(
                fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"],
                text_color=ThemeSettings.settings["root"]["accent_color"]["normal"]
            )

        self.re_download_btn.bind("<Enter>", on_mouse_enter_re_download_btn)
        self.re_download_btn.bind("<Leave>", on_mouse_leave_download_btn)

        def on_mouse_enter_pause_resume_btn(event):
            self.pause_resume_btn.configure(
                fg_color=ThemeSettings.settings["video_object"]["fg_color"]["hover"],
                text_color=ThemeSettings.settings["root"]["accent_color"]["hover"]
            )
            self.on_mouse_enter_self(event)

        def on_mouse_leave_pause_resume_btn(_event):
            self.pause_resume_btn.configure(
                fg_color=ThemeSettings.settings["video_object"]["fg_color"]["normal"],
                text_color=ThemeSettings.settings["root"]["accent_color"]["normal"]
            )

        self.pause_resume_btn.bind("<Enter>", on_mouse_enter_pause_resume_btn)
        self.pause_resume_btn.bind("<Leave>", on_mouse_leave_pause_resume_btn)

    # place widgets
    def place_widgets(self):
        super().place_widgets()
        scale = GeneralSettings.settings["scale_r"]
        y = ScaleSettings.settings["DownloadingVideo"][str(scale)]

        self.video_title_label.place(relwidth=0.5, width=-150 * scale)
        self.channel_btn.place(relwidth=0.5, width=-150 * scale)
        self.url_label.place(relwidth=0.5, width=-150 * scale)

        self.sub_frame.place(relx=0.5, y=2)

        self.download_progress_label.place(relx=0.25, anchor="n", y=y[0])
        self.download_progress_label.configure(height=20 * scale)
        self.download_type_label.place(relx=0.75, anchor="n", y=y[1])
        self.download_type_label.configure(height=20 * scale)
        self.download_progress_bar.place(relwidth=1, y=y[2] * scale)
        self.download_percentage_label.place(relx=0.115, anchor="n", y=y[3])
        self.download_percentage_label.configure(height=20 * scale)
        self.net_speed_label.place(relx=0.445, anchor="n", y=y[4])
        self.net_speed_label.configure(height=20 * scale)

        self.status_label.place(relx=0.775, anchor="n", y=y[5])
        self.status_label.configure(height=20 * scale)

    # configure widgets sizes and place location depend on root width
    def configure_widget_sizes(self, e):
        scale = GeneralSettings.settings["scale_r"]
        self.sub_frame.configure(width=self.master.winfo_width() / 2 - 100 * scale)