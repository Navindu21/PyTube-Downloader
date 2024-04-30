from app import App
import customtkinter as ctk
from widgets import AlertWindow
from functions import (
    get_theme_settings,
    get_general_settings,
    accessible
)


# get the theme settings
# get the general settings
app_theme_settings = get_theme_settings()
app_general_settings = get_general_settings()

# Initialize app.
app = App(
    # settings
    general_settings=app_general_settings,
    theme_settings=app_theme_settings,
)
# initiate services
app.initiate_services()
# run services
app.run_services()
# Check directory access during startup.
# If accessible, nothing happens if not, show an error message.
DIRECTORIES = ["temp", app_general_settings["download_directory"]]
for directory in DIRECTORIES:
    if not accessible(directory):
        AlertWindow(
            master=app,
            alert_msg="Please run this application as an administrator...!",
            ok_button_text="ok",
            ok_button_callback=app.on_app_closing,
            callback=app.on_app_closing
        )
# set the theme mode, dark or light or system, by getting from settings
ctk.set_appearance_mode(app_theme_settings["root"]["theme_mode"])
# deactivate the automatic scale
ctk.deactivate_automatic_dpi_awareness()
# place the app at the last placed geometry
app.geometry(app_general_settings["geometry"])
# set minimum window size to 900x500
app.minsize(900, 500)
# configure alpha
app.attributes("-alpha", app_theme_settings["opacity"])
# set the title icon
app.iconbitmap("src\\icon.ico")
# set the app title
app.title("PyTube Downloader")
# Create the main widgets of the application
app.create_widgets()
# place main widgets
app.place_widgets()
# configure colors for main widgets
app.set_widgets_colors()
# configure theme color
app.set_accent_color()
# configure fonts for main widgets
app.set_widgets_fonts()
# app event bind
app.bind_events()
# just rut the app
app.run()
