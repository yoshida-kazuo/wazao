import fire
import subprocess
import sys
import os
import textwrap
import shutil
import re
from text2voice import Text2Voice

class TextToVideo:

    _dic = None

    def __init__(self):
        self._dic = {}

    def convert(self,
                text,
                mp3_output="output.mp3",
                htsvoice="./htsvoice/takumi_normal.htsvoice",
                dictionary_dir="/var/lib/mecab/dic/open-jtalk/naist-jdic",
                output_filename="output.mp4",
                background=None,
                music_file=None,
                en2kana_dic="bep-eng.dic",
                engine="open-jtalk",
                speaker_id=0):
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
        """

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

            segment, param_background, param_slidetime = self.extract_params(segment)
            if not param_background:
                param_background = background

            temp_filename = self.run(text=segment,
                                     mp3_output=temp_output_mp3,
                                     htsvoice=htsvoice,
                                     dictionary_dir=dictionary_dir,
                                     output_filename=temp_output,
                                     background=param_background,
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
                       text: str):
        extract_params = {}
        match = re.match(r'^(\{\{--(?P<params>.*?)--\}\})?(?P<text>[^\{\{\}\}]+)', text)

        if match['params']:
            params = match['params'].split(',')

            for _, param in enumerate(params):
                k, v = param.split(':')
                extract_params[k] = v

        return [
            match['text'],
            extract_params.get('bg'),
            extract_params.get('ts'),
        ]

    def run(self,
            text: str,
            mp3_output: str="output.mp3",
            htsvoice: str=None,
            dictionary_dir: str=None,
            output_filename: str="output.mp4",
            background: str=None,
            engine: str='open-jtalk',
            speaker_id: int=1) -> str:
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
        duration = self.duration(mp3_output=mp3_output)

        srt_file = "subtitle.srt"
        self.generate_srt(text, srt_file, duration)

        base_video = "base_video.mp4"
        self.generate_background_video(background=background,
                                       base_video=base_video,
                                       duration=duration)

        adelay_filter = "adelay=1s:all=true"
        self.combine_videos(input_audio=mp3_output,
                            base_video=base_video,
                            input_srt=srt_file,
                            adelay_filter=adelay_filter,
                            output_video=output_filename)

        os.remove(output_wav)
        os.remove(srt_file)
        os.remove(base_video)
        os.remove(mp3_output)

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
            f.write("00:00:00,000 --> " + "{:02d}:{:02d}:{:02d},{:03d}\n".format(
                int(duration // 3600),
                int((duration % 3600) // 60),
                int(duration % 60),
                int((duration % 1) * 1000)
            ))
            f.write(text + "\n")

    def is_video(self,
                 filepath: str) -> bool:
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        _, ext = os.path.splitext(filepath)

        return ext.lower() in video_extensions

    def generate_background_video(self,
                                  background: str=None,
                                  base_video: str=None,
                                  duration: float=10.0) -> None:
        loop_time = str(int(duration))

        if background:
            filter_complex = f"[0:v]scale=w=1920:h=1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[video]"

            if self.is_video(background):
                cmd_base_video = [
                    "ffmpeg",
                    "-y",
                    "-loglevel", "error",
                    "-i", background,
                    "-t", loop_time,
                    "-s", "1920x1080",
                    "-c:v", "libx264",
                    "-an",
                    base_video
                ]
            else:
                cmd_base_video = [
                    "ffmpeg",
                    "-y",
                    "-loglevel", "error",
                    "-loop", "1",
                    "-i", background,
                    "-filter_complex", filter_complex,
                    "-map", "[video]",
                    "-c:v", "libx264",
                    "-t", loop_time,
                    "-s", "1920x1080",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    base_video
                ]
        else:
            cmd_base_video = [
                "ffmpeg",
                "-y",
                "-loglevel", "error",
                "-t", loop_time,
                "-s", "1920x1080",
                "-f", "rawvideo",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                "-i", "/dev/zero",
                "-c:v", "libx264",
                base_video
            ]
        subprocess.run(cmd_base_video, stdout=subprocess.DEVNULL)

    def combine_videos(self,
                    input_audio: str,
                    base_video: str,
                    input_srt: str,
                    adelay_filter: str,
                    output_video: str) -> None:
        subtitle_filter = f"subtitles={input_srt}:force_style='FontSize=18,Alignment=2'"
        cmd = [
            "ffmpeg",
            "-y",
            "-loglevel", "error",
            "-i", base_video,
            "-i", input_audio,
            "-filter_complex", f"[0:v]fade=t=in:st=0:d=0.3,{subtitle_filter}[vout]",
            "-map", "[vout]",
            "-map", "1:a",
            "-af", adelay_filter,
            "-c:a", "aac",
            "-c:v", "libx264",
            output_video
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

    def duration(self,
                 mp3_output: str) -> float:
        duration_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            mp3_output
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

        cmd_duration = [
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            video_file
        ]
        video_duration = float(subprocess.check_output(cmd_duration).decode("utf-8").strip())

        cmd_music_duration = [
            "ffprobe",
            "-v", "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            music_file
        ]
        music_duration = float(subprocess.check_output(cmd_music_duration).decode("utf-8").strip())

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
