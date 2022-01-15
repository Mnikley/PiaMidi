"""
Audio to Midi downloader & converter entry script to create and launch virtual environment

Author: Matthias Ley
Date: 15.01.2022
"""
import sys
import os
from importlib.util import find_spec
import platform
import requests
from zipfile import ZipFile


def download_file(url, to_folder=None, optional=False):
    try:
        file_name = url.split("/")[-1]
        print(f"Downloading {file_name} ..")
        file = requests.get(url)
        if file.status_code != 200:
            if not optional:
                raise FileNotFoundError(f"URL not found ({file.status_code}): {url})")
            else:
                print(f"WARNING - URL not found ({file.status_code}): {url}")
                return
        if to_folder:
            if not os.path.exists(to_folder):
                os.mkdir(to_folder)
            file_name = os.getcwd() + os.sep + to_folder + os.sep + file_name
        else:
            file_name = os.getcwd() + os.sep + file_name
        with open(file_name, "wb") as f:
            f.write(file.content)
        return file_name
    except Exception as e:
        raise e


def dl_ffmpeg():
    file_path = download_file("https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
                              "ffmpeg-master-latest-win64-gpl.zip")
    print("Extracting ffmpeg.exe from zip file ..")
    with ZipFile(file_path, "r") as z:
        z.extract("ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe", ".")
    # remove zip
    os.remove(file_path)
    # move exe to root folder
    os.rename("ffmpeg-master-latest-win64-gpl" + os.sep + "bin" + os.sep + "ffmpeg.exe", "ffmpeg.exe")
    # remove folders from zip
    os.rmdir("ffmpeg-master-latest-win64-gpl" + os.sep + "bin")
    os.rmdir("ffmpeg-master-latest-win64-gpl")


def dl_trained_model():
    file_path = download_file("https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth",
                              to_folder="lib")
    # rename file
    os.rename(file_path, "lib" + os.sep + "note_F1=0.9677_pedal_F1=0.9186.pth")


def dl_midi_sheet_music():
    file_path = download_file("http://midisheetmusic.com/downloads/MidiSheetMusic-2.6.2.exe", to_folder="lib",
                              optional=True)


if __name__ == "__main__":
    # verify python version
    if sys.version_info.major < 3 or (sys.version_info.major == 3 and sys.version_info.minor < 4):
        raise SystemExit("Python 3.4+ is required to run this application")

    # check if pip is installed
    if not find_spec("pip"):
        raise ModuleNotFoundError("pip not installed. Please check: https://pip.pypa.io/en/stable/installation/")

    # get virtual environment interpreter location
    _platform = platform.system()
    if _platform == "Windows":
        _interpreter = os.getcwd() + os.sep + "venv" + os.sep + "Scripts" + os.sep + "python.exe"
    elif _platform in ["Darwin", "Linux"]:
        _interpreter = os.getcwd() + os.sep + "venv" + os.sep + "bin" + os.sep + "python"
        raise SystemExit(f"OS '{_platform}' not supported")
    else:
        raise SystemExit("Unknown operating system")

    # check if venv folder exists, if not create folder, venv and install requirements.txt
    if not os.path.exists("venv"):
        print("Setting up virtual environment ..")
        os.mkdir("venv")
        os.system(sys.executable + " -m venv " + os.getcwd() + os.sep + "venv")
        os.system(_interpreter + " -m pip install -r requirements.txt")

    # download other requirements
    if not os.path.exists("lib"):
        os.mkdir("lib")

    if not os.path.isfile("ffmpeg.exe"):
        dl_ffmpeg()

    if not os.path.isfile("lib" + os.sep + "note_F1=0.9677_pedal_F1=0.9186.pth"):
        dl_trained_model()

    if not os.path.isfile("lib" + os.sep + "MidiSheetMusic-2.6.2.exe"):
        dl_midi_sheet_music()

    # launch app
    os.system(_interpreter + " transcribe_v2.py")
