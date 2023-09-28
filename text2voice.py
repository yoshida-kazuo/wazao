import subprocess
from pathlib import Path
import voicevox_core
from voicevox_core import (
    AccelerationMode,
    AudioQuery,
    VoicevoxCore
)

class Text2Voice:

    _text: str=None
    _dictionary_dir: str=None
    _htsvoice: str=None
    _output_wav: str=None
    _engine: str=None
    _speaker_id: int=None

    def __init__(self,
                 text: str,
                 dictionary_dir: str,
                 output_wav: str,
                 engine: str='open-jtalk',
                 htsvoice: str=None,
                 speaker_id: int=0):
        self._text = text
        self._dictionary_dir = dictionary_dir
        self._htsvoice = htsvoice
        self._output_wav = output_wav
        self._engine = engine
        self._speaker_id = speaker_id

    def open_jtalk(self,
                   text: str=None,
                   dictionary_dir: str=None,
                   htsvoice: str=None,
                   output_wav: str=None):
        if text:
            self._text = text
        if dictionary_dir:
            self._dictionary_dir = dictionary_dir
        if htsvoice:
            self._htsvoice
        if output_wav:
            self._output_wav = output_wav

        cmd = ["open_jtalk"]
        if self._dictionary_dir:
            cmd.extend(["-x", self._dictionary_dir])
        if self._htsvoice:
            cmd.extend(["-m", self._htsvoice])
        cmd.extend(["-ow", self._output_wav])

        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as proc:
                proc.stdin.write(self._text.encode('utf-8'))
                proc.stdin.close()
                proc.wait()

        return self._output_wav

    def voicevox(self,
                 text: str=None,
                 dictionary_dir: str=None,
                 output_wav: str=None,
                 speaker_id: int=None) -> str:
        if text:
            self._text = text
        if dictionary_dir:
            self._dictionary_dir = dictionary_dir
        if output_wav:
            self._output_wav = output_wav
        if speaker_id:
            self._speaker_id = speaker_id

        voicevox_core = VoicevoxCore(
            acceleration_mode=AccelerationMode.AUTO,
            open_jtalk_dict_dir=self._dictionary_dir,
        )
        voicevox_core.load_model(self._speaker_id)
        audio_query = voicevox_core.audio_query(self._text, self._speaker_id)

        Path(self._output_wav).write_bytes(
            voicevox_core.synthesis(audio_query, self._speaker_id)
        )

        return self._output_wav

    def main(self,
             engine: str=None):
        if engine:
            self._engine = engine
        method = self._engine.replace('-', '_')
        func = getattr(self, method)

        return func()
