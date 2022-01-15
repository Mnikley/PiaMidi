# PiaMidi

Piano-learning app to download piano-audio from various sources and convert them to .midi

![Screenshot PiaMidi](https://user-images.githubusercontent.com/75040444/149627235-c8f1ec08-43ee-4174-9467-730f6f419908.png)

---

# Quickstart

- Clone repository: ```git clone https://github.com/Mnikley/PiaMidi```
- Run app: ```python run.py```

---



# Sources
### Piano transcription to MIDI
- https://github.com/bytedance/piano_transcription
- License: Apache 2.0

### Trained model:
- Qiuqiang Kong, Bochen Li, Xuchen Song, Yuan Wan, Yuxuan Wang., High-resolution Piano Transcription with Pedals by Regressing Onsets and Offsets Times_v0.1, 2020
- Downloaded from: https://zenodo.org/record/4034264#.X7vAB2gzZPY

### youtube-dl
- https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl
- License: The Unlicense

### spotify-downloader
- https://github.com/spotDL/spotify-downloader
- License: MIT

### FFmpeg
- https://ffmpeg.org/
- https://github.com/FFmpeg/FFmpeg
- License: Mainly LGPL-licensed; https://github.com/FFmpeg/FFmpeg/blob/master/LICENSE.md

### MidiSheetMusic
- http://midisheetmusic.com/
- Developed by [Madhav Vaidyanathan](midisheetmusic.sf@gmail.com)

---

# pyinstaller command
```pyinstaller --noconfirm --onedir --console --name "PiaMidi" --add-data "lib;lib/" --add-data "ffmpeg.exe;." --collect-submodules "sklearn" --collect-all "librosa" --collect-all "ytmusicapi"  "transcribe_v2.py"```

--- 

# TODO:
- Disclaimer info at start (built on top of a couple of libraries.. sources erwähnen); Will only work properly on songs with pure piano sounds
- Fix bug when moving latest file in transcribe_v2.py move_latest_file_to_results_folder()
