import fire
import subprocess
import sys
import os
import textwrap
import shutil

class TextToVideo:
    def __init__(self):
        pass

    def convert(self,
                text,
                output_wav="output.wav",
                htsvoice="/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice",
                dictionary_dir="/var/lib/mecab/dic/open-jtalk/naist-jdic",
                output_filename="output.mp4",
                background_image=None,
                music_file=None):
        """_summary_

        Args:
            text (_type_): _description_
            output_wav (str, optional): _description_. Defaults to "output.wav".
            htsvoice (str, optional): _description_. Defaults to "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice".
            dictionary_dir (str, optional): _description_. Defaults to "/var/lib/mecab/dic/open-jtalk/naist-jdic".
            output_filename (str, optional): _description_. Defaults to "output.mp4".
            background_image (_type_, optional): _description_. Defaults to None.
        """

        if os.path.isfile(text):
            with open(text, 'r', encoding='utf-8') as file:
                text = file.read()

        segments = text.split("\n")
        video_segments = []
        for index, segment in enumerate(segments):
            temp_output = f"temp_output_{index}.mp4"
            segment = segment.replace('\\', '¥')
            
            if not segment.strip():
                continue

            temp_filename = self.run_open_jtalk_with_text(text=segment,
                                                          output_wav=output_wav,
                                                          htsvoice=htsvoice,
                                                          dictionary_dir=dictionary_dir,
                                                          output_filename=temp_output,
                                                          background_image=background_image)
            video_segments.append(temp_filename)

        self.merge_videos(video_segments, output_filename)

        for vid in video_segments:
            os.remove(vid)

        if os.path.isfile(music_file):
            self.add_background_music(video_file=output_filename,
                                      music_file=music_file,
                                      music_volume=0.15,
                                      output_file=output_filename)

        return os.path.abspath(output_filename)

    def run_open_jtalk_with_text(self,
                                 text: str,
                                 output_wav: str="output.wav",
                                 htsvoice: str=None,
                                 dictionary_dir: str=None,
                                 output_filename: str="output.mp4",
                                 background_image: str=None) -> str:
        cmd = ["open_jtalk"]

        if dictionary_dir:
            cmd.extend(["-x", dictionary_dir])
        if htsvoice:
            cmd.extend(["-m", htsvoice])
        cmd.extend(["-ow", output_wav])

        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
                proc.stdin.write(text.encode('utf-8'))
                proc.stdin.close()
                proc.wait()
        mp3_output = output_wav.replace(".wav", ".mp3")
        self.convert_wav_to_mp3(output_wav, mp3_output)

        duration = self.duration(mp3_output=mp3_output)

        srt_file = "subtitle.srt"
        self.generate_srt(text, srt_file, duration)

        base_video = "base_video.mp4"
        self.generate_video_with_subtitle(input_audio=mp3_output,
                                          background_image=background_image,
                                          base_video=base_video,
                                          duration=duration)

        adelay_filter = "adelay=1s:all=true"
        self.combine_videos(input_audio=mp3_output,
                            base_video=base_video,
                            input_srt=srt_file,
                            adelay_filter=adelay_filter,
                            output_video=output_filename)

        os.remove(output_wav)
        os.remove(mp3_output)
        os.remove(srt_file)
        os.remove(base_video)

        return os.path.abspath(output_filename)

    def convert_wav_to_mp3(self,
                           input_wav,
                           output_mp3):
        cmd = [
            "ffmpeg", 
            "-y",
            "-loglevel", "error",   # この行を追加
            "-i", input_wav, 
            "-codec:a", "libmp3lame", 
            "-qscale:a", "2", 
            output_mp3
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL)

    def wrap_text(self,
                  text,
                  max_width=42):
        wrapper = textwrap.TextWrapper(width=max_width)
        wrapped_text = wrapper.fill(text)
        return wrapped_text

    def generate_srt(self,
                     text: str,
                     output_srt: str="subtitle.srt",
                     duration: float=10.0):
        text = self.wrap_text(text)
        with open(output_srt, 'w', encoding='utf-8') as f:
            f.write("1\n")
            f.write("00:00:01,000 --> " + "{:02d}:{:02d}:{:02d},{:03d}\n".format(
                int(duration // 3600),
                int((duration % 3600) // 60),
                int(duration % 60),
                int((duration % 1) * 1000)
            ))
            f.write(text + "\n")

    def generate_video_with_subtitle(self,
                                     input_audio: str,
                                     background_image: str=None,
                                     base_video: str=None,
                                     duration: float=10.0):
        loop_time = str(int(duration))

        if background_image:
            filter_complex = f"[0:v]scale=w=1920:h=1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[video]"

            cmd_base_video = [
                "ffmpeg",
                "-y",
                "-loglevel", "error",
                "-loop", "1",
                "-i", background_image,
                "-filter_complex", filter_complex,
                "-map", "[video]",
                "-c:v", "libx264",
                "-t", loop_time,
                "-s", "1920x1080",
                "-pix_fmt", "yuv420p",  # ここを追加
                "-r", "30",
                base_video
            ]
        else:
            cmd_base_video = [
                "ffmpeg",
                "-y",
                "-loglevel", "error",
                "-t", loop_time,  # 10秒間の動画を生成
                "-s", "1920x1080",
                "-f", "rawvideo",
                "-pix_fmt", "yuv420p",
                "-r", "30",  # fps
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
                    output_video: str):
        subtitle_filter = f"subtitles={input_srt}:force_style='FontSize=12,Alignment=2'"  # ここを変更
        cmd = [
            "ffmpeg", 
            "-y",
            "-loglevel", "error",   # この行を追加
            "-i", base_video,
            "-i", input_audio, 
            "-vf", subtitle_filter,
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
                     video_list,
                     output):
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
                             video_file,
                             music_file,
                             music_volume: float,
                             output_file):
        temp_filename = 'tmp.mp4'

        # 動画の長さを取得
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

        # BGMの長さを取得
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

        # BGMを動画の長さに合わせて調整
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

        # BGMと動画を合成
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
