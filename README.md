# AudioToMidi
Piano-learning app to download piano-audio from various sources and convert them to .midi

# Sources
## piano_transcription_interference repo
https://github.com/bytedance/piano_transcription

## trained piano model .pth:
[1] Qiuqiang Kong, Bochen Li, Xuchen Song, Yuan Wan, Yuxuan Wang., High-resolution Piano Transcription with Pedals by Regressing Onsets and Offsets Times_v0.1, 2020
DL from: https://zenodo.org/record/4034264#.X7vAB2gzZPY

## youtube-dl
https://github.com/ytdl-org/youtube-dl#embedding-youtube-dl

## spotdl
https://github.com/spotDL/spotify-downloader

## ffmpeg
https://ffmpeg.org/

## Midi player
http://midisheetmusic.com/download.html

# pyinstaller command
pyinstaller --noconfirm --onedir --console --name "AudioToMidi" --add-data "C:/Users/Glory/Desktop/testing/audio_to_midi/lib;lib/" --add-data "C:/Users/Glory/Desktop/testing/audio_to_midi/ffmpeg.exe;." --collect-submodules "sklearn" --collect-all "librosa" --collect-all "ytmusicapi"  "C:/Users/Glory/Desktop/testing/audio_to_midi/transcribe_v2.py"

# TODO:
- download ffmpeg.exe if not exists
- download MidiSheetMusic-2.6.2.exe if not exists
- download note_F1=0.9677_pedal_F1=0.9186.pth if not exists
- install requirements on first run instead of creating that huge package
- Disclaimer info at start (built on top of a couple of libraries.. sources erwähnen); Will only work properly on songs with pure piano sounds