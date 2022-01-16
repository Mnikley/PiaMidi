import os
import sys
import subprocess
import platform
from tkinter import Tk, Toplevel, StringVar
from tkinter.filedialog import askopenfilename
from tkinter.simpledialog import askstring
from tkinter.ttk import Label, Button, Frame, Separator, Progressbar, LabelFrame
import time
from concurrent.futures import ThreadPoolExecutor
import youtube_dl
from piano_transcription_inference import PianoTranscription, sample_rate, load_audio
from spotdl.search import SpotifyClient
from spotdl.parsers import parse_query
from spotdl.download import DownloadManager
import torch


class PrintLogger(object):
    """Class to create file like object to redirect stdout to label-text"""
    def __init__(self, status_var):
        # pass reference to text_variable widget
        self.status_var = status_var
        self.line_buffer = ''

    def write(self, buffer):
        # use stdout as text for text_variable, skip newline
        tmp_buffer = self.line_buffer + buffer
        self.line_buffer = ''
        for line in tmp_buffer.splitlines(True):
            if line[-1] == '\n':
                self.status_var.set(f"Status: {line.rstrip()}")
            else:
                self.line_buffer += line

    def flush(self):
        if self.line_buffer != '':
            self.status_var.set(f"Status: {self.line_buffer.rstrip()}")
        self.line_buffer = ''


class ToolTip(object):
    """Tooltip class; call with create_tooltip(widget, text)"""

    def __init__(self, widget):
        self.widget = widget
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.text = None

    def showtip(self, text):
        """Display text in tooltip window"""
        self.text = text
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 57
        y = y + cy + self.widget.winfo_rooty() + 27
        self.tip_window = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))

        label = Label(tw, text=self.text, justify="left", relief="solid", borderwidth=0.5)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


def create_tooltip(widget, text):
    """Call-function for Tooltip class; Example: create_tooltip(some_widget, text="Test Message")"""
    tool_tip = ToolTip(widget)

    def enter(event):
        try:
            # add 1 space to beginning of each line and at the end, show tooltip
            tool_tip.showtip(" {}".format(" \n ".join(text.split("\n"))) if text.find("\n") != -1 else f" {text} ")
        except Exception as e:
            print(e)

    def leave(event):
        tool_tip.hidetip()

    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class YTDLLogger(object):
    """Logger for youtube-dl"""
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


class UI(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.title("PiaMidi Transcriber")
        self.widgets = {}  # dict holding relevant UI elements
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.build_interface()
        self.audio_file = None  # stores path of local .mp3 file (either by chosing or after DL/conversion from YT)
        self.audio_url = None  # stores entered YT-url
        self.current_file_dl = None  # stores temporary filename during download
        if torch.cuda.is_available():
            self.transcribe_engine = "cuda"
        else:
            self.transcribe_engine = "cpu"
        self.change_status(f"Set {self.transcribe_engine.upper()} as engine")


    """ ################################### Interface widgets ######################################### """

    def build_interface(self):
        """Builds the graphical elements of the app"""
        # frame holding sub-frames + buttons
        master_box = Frame(self)
        master_box.pack(side="top", padx=2)

        # sub frame for launch midi player button
        play_box = LabelFrame(master_box, text="Play")
        play_box.pack(side="left", ipadx=2, ipady=2)

        # launch midi player button
        self.widgets["launch_midi_player"] = Button(play_box, text="Lauch Midi Player", command=self.launch_midi_player)
        self.widgets["launch_midi_player"].pack()
        if not os.path.exists("lib" + os.sep + "MidiSheetMusic-2.6.2.exe"):
            self.widgets["launch_midi_player"]["state"] = "disabled"
            create_tooltip(self.widgets["launch_midi_player"], "External midi player not found!")
        else:
            create_tooltip(self.widgets["launch_midi_player"], "Launch external midi player")

        # sub frame for load & convert buttons
        load_box = LabelFrame(master_box, text="(Down-)load & convert")
        load_box.pack(side="left", ipadx=2, ipady=2)

        # load file button
        self.widgets["load_file"] = Button(load_box, text="Load File", command=self.load_file)
        self.widgets["load_file"].pack(side="left")
        create_tooltip(self.widgets["load_file"], "Load a local .mp3 file to convert to .midi")

        # load YT url button
        self.widgets["load_yt_url"] = Button(load_box, text="Load URL", command=self.load_url)
        self.widgets["load_yt_url"].pack(side="left")
        create_tooltip(self.widgets["load_yt_url"], "Enter URL to download & convert to .mp3 and .midi afterwards\n"
                                                    "Supported tested platforms: Youtube, Soundcloud, Spotify")

        # separator
        sep_bottom = Separator(self, orient="horizontal")
        sep_bottom.pack(side="top", fill="x", pady=3)

        # subframe for status bar & progress indicator
        status_box = Frame(self)
        status_box.pack(side="bottom", fill="x")

        # status label
        self.widgets["status_var"] = StringVar()
        self.widgets["status"] = Label(status_box, textvariable=self.widgets["status_var"])
        self.widgets["status"].pack(side="left", anchor="w", padx=5)

        # progress bar
        self.widgets["progress"] = Progressbar(status_box, length=100, mode="determinate", orient="horizontal")
        self.widgets["progress"].pack(side="right", anchor="e", padx=2, pady=2)

    """ ################################### Core functions ########################################## """

    def launch_midi_player(self):
        """Launch the midi player .exe (Windows only)"""
        folder = os.getcwd() + os.sep + "lib"
        if platform.system() == "Windows":
            subprocess.Popen(os.path.join(folder, "MidiSheetMusic-2.6.2.exe"))
            self.change_status("Launched Midi Player")
        else:
            self.change_status("Midi Player is a Windows-only feature!")

    def load_file(self):
        """Load local .mp3 file"""
        self.audio_file = askopenfilename(title="Chose audio file to convert to midi",
                                          filetypes=[("Audio file", "*.mp3"), ("All files", "*.*")])
        if not self.audio_file:
            self.change_status("Load file aborted")
            return

        self.change_status(f"Loaded file: {os.path.split(self.audio_file)[-1]}")
        self.process()

    def process(self):
        """Convert audio data to .midi file"""
        def callback():
            # self.change_status("Trying to download from spotify URL ..")

            # stdout to status-bar
            self.stdout_to_label()

            # # create results folder if doesnt exist
            # if not os.path.exists("results"):
            #     os.mkdir("results")
            #     print("Created folder results")

            # midi_file_name = os.getcwd() + os.sep + "results" + os.sep + \
            #                  os.path.splitext(os.path.split(self.audio_file)[-1])[0] + ".midi"
            midi_file_name = os.path.splitext(self.audio_file)[0] + ".midi"

            # Load audio
            (audio, _) = load_audio(self.audio_file, sr=sample_rate, mono=True)

            # Transcriptor
            transcriptor = PianoTranscription(device=self.transcribe_engine,
                                              checkpoint_path="lib" + os.sep + "note_F1=0.9677_pedal_F1=0.9186.pth")

            # Transcribe and write out to MIDI file
            transcribed_dict = transcriptor.transcribe(audio, midi_file_name)

            # self.change_status(f"Conversion OK: {os.path.split(midi_file_name)[-1]}")
            self.change_status(f"Conversion OK")

            if platform.system() == "Windows":
                os.startfile("results")

            # stdout back to console
            self.stdout_to_console()

        # start threads, initiate loading
        main_thread = self.executor.submit(callback)
        self.executor.submit(self.loading, main_thread)

    def load_url(self):
        """Load URL, decide if dl'ed via youtube-dl or spotdl"""
        self.audio_url = askstring(title="Convert URL to mp3", prompt="Enter URL (Youtube, Spotify, Soundcloud, ..):")

        if not self.audio_url:
            self.change_status("Load Youtube URL cancelled")
            return

        if not os.path.exists("results"):
            os.mkdir("results")

        if "spotify.com" in self.audio_url:
            self.load_spotify_url()
        else:
            self.load_youtube_url()

    def load_spotify_url(self):
        """DL spotify URL via spotdl
        TODO: fix bug when file exists but doesnt start process
        TODO: fix bug when file exists and process isnt initiated
        """
        def callback():
            self.change_status("Trying to download spotify song ..")

            # Initialize spotify client
            try:
                SpotifyClient.init(
                    client_id="5f573c9620494bae87890c0f08a60293",
                    client_secret="212476d9b0f3472eaa762d90b19b0ba8",
                    # user_auth=True,
                    user_auth=False
                )
            except Exception as e:
                self.change_status(e)

            # specify URLs to download
            # url_list = [self.audio_url]

            # configuration for DownloadManager
            args_dict = {
                "query": self.audio_url,
                "debug_termination": False,
                "output": None,
                # "output_format": "mp3",
                "user_auth": False,
                "use_youtube": False,
                "lyrics_provider": "musixmatch",
                # "path_template": None,
                # "ffmpeg": "ffmpeg",
                "ignore_ffmpeg_version": False,
                # "download_threads": 4,
                "search_threads": 4,
                "generate_m3u": False
            }

            # query youtube urls & start downloads
            exc = None
            # stdout to label
            self.stdout_to_label()
            with DownloadManager(args_dict) as downloader:
                try:
                    song = parse_query([self.audio_url], "mp3", False, False, "musixmatch", 4, None)
                    downloader.download_single_song(song[0])
                    self.audio_file = song[-1].file_name + "." + downloader.arguments["output_format"]
                    self.change_status(f"DL OK: {self.audio_file}")
                except Exception as e:
                    exc = e
            # stdout to console
            self.stdout_to_console()
            if exc:
                self.change_status(exc)
            else:
                self.move_and_process()

        # start threads, initiate loading
        main_thread = self.executor.submit(callback)
        self.executor.submit(self.loading, main_thread)

    def load_youtube_url(self):
        """Load and convert youtube video to mp3 via youtube-dl"""
        def ytdl_hook(d):
            self.audio_file = d["filename"]
            if d["status"] == "downloading":
                self.change_status(f"Downloading.. {d['_percent_str']} (ETA {d['_eta_str']})")
            if d['status'] == 'finished':
                self.move_and_process()

        def callback():
            self.change_status("Downloading & converting youtube URL ..")

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'logger': YTDLLogger(),
                'progress_hooks': [ytdl_hook]
                # 'ffmpeg_location': os.getcwd() + os.sep + "lib",
            }

            try:
                with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.audio_url])

            except Exception as e:
                self.change_status(e)

        # start threads, initiate loading
        main_thread = self.executor.submit(callback)
        self.executor.submit(self.loading, main_thread)

    """ ################################## Supplementary functions ################################ """
    def change_status(self, status_text):
        """Change status text at bottom"""
        self.widgets["status_var"].set(f"Status: {status_text}")

    def move_and_process(self):
        """Moves file defined in print(self.current_file_dl) to results folder and starts conversion process"""
        if not os.path.exists("results"):
            os.mkdir("results")

        # move file
        os.rename(os.path.join(os.getcwd() + os.sep + self.audio_file),
                  os.path.join(os.getcwd() + os.sep + "results" + os.sep + self.audio_file))

        # TODO: following line produces [WinError 2] for some reason which doesnt affect further processes ..
        self.audio_file = os.path.join(os.getcwd() + os.sep + "results" + os.sep + self.audio_file)
        self.process()

    def loading(self, thread):
        """Loading animation while thread is running"""
        # start animation
        self.start_infinite_loading()

        # loop while thread is working
        while thread.running():
            time.sleep(0.5)
            pass

        # stop loading animation when finished
        self.stop_infinite_loading()

    def start_infinite_loading(self):
        """Debug function - starts infinite loading"""
        self.widgets["progress"].config(mode="indeterminate")
        self.widgets["progress"].start(10)

    def stop_infinite_loading(self):
        """Debug function - stops infinite loading"""
        self.widgets["progress"].stop()
        self.widgets["progress"].config(mode="determinate")

    def stdout_to_label(self):
        """Redirect stdout/stderr to label"""
        print_logger = PrintLogger(self.widgets["status_var"])
        sys.stdout = print_logger
        sys.stderr = print_logger

    def stdout_to_console(self):
        """Redirect stdout/stderr to console"""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


if __name__ == "__main__":
    app = UI()
    app.mainloop()
