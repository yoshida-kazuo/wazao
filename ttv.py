import fire
import subprocess
import sys
import os
import textwrap
import shutil
import re
from text2voice import Text2Voice

class TextToVideo:

    _background: str=None
    _dic: dict=None
    _video_size: str=None
    _adlay: int=None
    _silence_duration: int=None
    _video_codec: str=None

    def __init__(self):
        self._dic = {}
        self._video_size = '1920x1080'

    def convert(self,
                text: str,
                mp3_output: str="output.mp3",
                htsvoice: str="./htsvoice/takumi_normal.htsvoice",
                dictionary_dir: str="/var/lib/mecab/dic/open-jtalk/naist-jdic",
                output_filename: str="output.mp4",
                background: str=None,
                music_file: str=None,
                en2kana_dic="bep-eng.dic",
                engine: str="open-jtalk",
                speaker_id: int=0,
                video_codec: str="libx264"):
        """_summary_

        Args:
            text (str): _description_
            mp3_output (str, optional): _description_. Defaults to "output.mp3".
            htsvoice (str, optional): _description_. Defaults to "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice".
            dictionary_dir (str, optional): _description_. Defaults to "/var/lib/mecab/dic/open-jtalk/naist-jdic".
            output_filename (str, optional): _description_. Defaults to "output.mp4".
            background (str, optional): _description_. Defaults to None.
            music_file (str, optional): _description_. Defaults to None.
            en2kan_dic (str, optional): _description_. Defaults to "bep-eng.dic".
            engine (str, optional): "open-jtalk"|"voicevox". Defaults to "open-jtalk".
            speaker_id (int, optional): voicevox option 0~50. Defaults to 0.
            video_code (str, optional): _description_. Defaults to "libx264"
        """

        self._video_codec = video_codec

        if os.path.isfile(text):
            with open(text, 'r', encoding='utf-8') as file:
                text = file.read()

        if en2kana_dic and os.path.isfile(en2kana_dic):
            self.load_dic(en2kana_dic)

        segments = text.split("\n")
        video_segments = []
        for index, segment in enumerate(segments):
            temp_output = f"temp_output_{index}.mp4"
            temp_output_mp3 = f"temp_output_{index}.mp3"
            segment = segment.replace('\\', '¥')

            if not segment.strip():
                continue

            segment = self.extract_params(segment)
            if not self._background:
                self._background = background

            temp_filename = self.run(text=segment,
                                     mp3_output=temp_output_mp3,
                                     htsvoice=htsvoice,
                                     dictionary_dir=dictionary_dir,
                                     output_filename=temp_output,
                                     engine=engine,
                                     speaker_id=speaker_id)
            video_segments.append(temp_filename)

        self.merge_videos(video_list=video_segments,
                          output=output_filename)

        for vid in video_segments:
            os.remove(vid)

        if music_file and os.path.isfile(music_file):
            self.add_background_music(video_file=output_filename,
                                      music_file=music_file,
                                      music_volume=0.15,
                                      output_file=output_filename)

        return os.path.abspath(output_filename)

    def extract_params(self,
                       text: str) -> str:
        extract_params = {}
        match = re.match(r'^(\{\{--(?P<params>.*?)--\}\})?(?P<text>[^\{\{\}\}]+)', text)

        if match['params']:
            params = match['params'].split(',')

            for _, param in enumerate(params):
                k, v = param.split(':')
                extract_params[k] = v

        self._adlay = int(extract_params.get('ad', 1))
        self._silence_duration = int(extract_params.get('sd', 0))
        self._background = extract_params.get('bg', None)

        return match['text']

    def run(self,
            text: str,
            mp3_output: str="output.mp3",
            htsvoice: str=None,
            dictionary_dir: str=None,
            output_filename: str="output.mp4",
            engine: str='open-jtalk',
            speaker_id: int=0) -> str:
        output_wav = 'output.wav'
        speach_text = self.en2kana(text)

        text2voice = Text2Voice(text=speach_text,
                                dictionary_dir=dictionary_dir,
                                output_wav=output_wav,
                                htsvoice=htsvoice,
                                engine=engine,
                                speaker_id=speaker_id)
        text2voice.main()

        self.convert_wav_to_mp3(output_wav, mp3_output)
        duration = self.duration(filename=mp3_output)

        srt_file = "subtitle.srt"
        self.generate_srt(text, srt_file, duration)

        base_video = "base_video.mp4"
        self.generate_background(background=self._background,
                                 base_video=base_video,
                                 duration=duration,
                                 input_srt=srt_file)

        self.combine_videos(speach_audio=mp3_output,
                            base_video=base_video,
                            output_video=output_filename)

        for file in [output_wav, srt_file, base_video, mp3_output]:
            os.remove(file)

        return os.path.abspath(output_filename)

    def convert_wav_to_mp3(self,
                           input_wav,
                           output_mp3) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", input_wav,
            "-codec:a", "libmp3lame",
            "-qscale:a", "2",
            output_mp3
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

    def load_dic(self,
                 filepath: str) -> object:
        with open(filepath, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    english_word, katakana = parts
                    self._dic[english_word] = katakana

        return self._dic

    def en2kana(self,
                text: str) -> str:
        converted_words = []
        matches = re.findall(r'[A-Za-z]+', text)
        for match in matches:
            text = text.replace(match, f" {match} ")
        words = text.split()

        for word in words:
            commas = ''.join([char for char in word if char in [',', '.']])
            commas = commas.replace(',', '、').replace('.', '。')
            word = word.replace('.', '').replace(',', '')
            kana = self._dic.get(word.upper(), word)
            converted_words.append(kana + commas)

        return ''.join(converted_words)

    def wrap_text(self,
                  text,
                  max_width=30) -> str:
        wrapper = textwrap.TextWrapper(width=max_width)
        wrapped_text = wrapper.fill(text)

        return wrapped_text

    def generate_srt(self,
                     text: str,
                     output_srt: str="subtitle.srt",
                     duration: float=10.0) -> None:
        text = self.wrap_text(text)

        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write("1\n")
            f.write("00:00:{:02d},000 --> ".format(
                    self._adlay
                ) + "{:02d}:{:02d}:{:02d},{:03d}\n".format(
                int(duration // 3600),
                int((duration % 3600) // 60),
                int(duration % 60) + self._adlay,
                int((duration % 1) * 1000)
            ))
            f.write(text + "\n")

    def is_video(self,
                 filepath: str) -> bool:
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        _, ext = os.path.splitext(filepath)

        return ext.lower() in video_extensions

    def generate_background(self,
                            background: str=None,
                            base_video: str=None,
                            duration: float=10.0,
                            input_srt: str=None) -> None:
        time = str(duration + self._adlay + self._silence_duration)
        width, height = self._video_size.split('x')
        subtitle_filter = f"subtitles={input_srt}:force_style='FontSize=18,Alignment=2'"
        filter_complex = f"[0:v]scale=w={width}:h={height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,{subtitle_filter}[video]"

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
        ]

        if background:
            if self.is_video(background):
                cmd.extend([
                    "-stream_loop", "-1",
                    "-i", background,
                    "-an"
                ])
            else:
                cmd.extend([
                    "-loop", "1",
                    "-i", background,
                    "-pix_fmt", "yuv420p",
                    "-r", "30"
                ])
        else:
            cmd.extend([
                "-f", "rawvideo",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-i", "/dev/zero"
            ])

        cmd.extend([
            "-t", time,
            "-c:v", self._video_codec,
            "-s", self._video_size,
            "-filter_complex", filter_complex,
            "-map", "[video]",
            base_video
        ])
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

    def combine_videos(self,
                       speach_audio: str,
                       base_video: str,
                       output_video: str) -> None:
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", base_video,
            "-i", speach_audio,
            "-filter_complex", f"[0:v]fade=t=in:st=0:d=0.3[vout]",
            "-map", "[vout]",
            "-map", "1:a",
            "-af", f"adelay={self._adlay}s:all=true,apad=pad_dur={self._silence_duration}",
            "-c:a", "aac",
            "-c:v", self._video_codec,
            output_video
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

    def duration(self,
                 filename: str) -> float:
        duration_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            filename
        ]

        return float(subprocess.check_output(duration_cmd).decode('utf-8').strip())

    def merge_videos(self,
                     video_list: object,
                     output: str) -> None:
        with open("filelist.txt", "w") as f:
            for vid in video_list:
                f.write(f"file '{vid}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-f", "concat",
            "-safe", "0",
            "-i", "filelist.txt",
            "-c", "copy",
            output
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

        os.remove("filelist.txt")

    def add_background_music(self,
                             video_file: str,
                             music_file: str,
                             music_volume: float,
                             output_file: str) -> None:
        temp_filename = 'tmp.mp4'
        video_duration = self.duration(filename=video_file)
        music_duration = self.duration(filename=music_file)

        if video_duration > music_duration:
            loop_count = int(video_duration // music_duration) + 1
            adjusted_music = "temp_adjusted_music.mp3"
            with open("music_list.txt", "w") as f:
                for _ in range(loop_count):
                    f.write(f"file '{music_file}'\n")
            cmd_adjust_music = [
                "ffmpeg",
                "-y",
                "-loglevel", "error",
                "-f", "concat",
                "-safe", "0",
                "-i", "music_list.txt",
                "-c", "copy",
                adjusted_music
            ]
            subprocess.run(cmd_adjust_music, stdout=subprocess.DEVNULL)
        else:
            adjusted_music = music_file

        cmd_merge = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", video_file,
            "-i", adjusted_music,
            "-filter_complex", f"[1:a]volume={music_volume},apad[A];[0:a][A]amerge[out]",
            "-map", "0:v",
            "-map", "[out]",
            "-c:v", "copy",
            "-c:a", "aac",
            temp_filename
        ]
        subprocess.run(cmd_merge, stdout=subprocess.DEVNULL)
        shutil.move(temp_filename, output_file)

        if video_duration > music_duration:
            os.remove("music_list.txt")
            os.remove(adjusted_music)



if __name__ == "__main__":
    fire.Fire(TextToVideo)
