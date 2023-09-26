# WaZao
WaZaoは、テキストを音声に変換し、その音声を背景画像やBGMと合成して動画を生成するツールです。Open JTalk と FFmpeg を活用しています。

## 準備
環境 debian 12.1  
依存関係
* fire: コマンドラインインターフェースを簡単に作成するためのライブラリ
* subprocess: Python からシェルコマンドを実行するためのモジュール
* open_jtalk: テキストを音声に変換するツール
* ffmpeg: 音声、画像、動画の変換・編集を行うツール
```
sudo apt install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001 ffmpeg
pip install -r requirements.txt
```

## 使い方
### 引数
* text: 変換するテキスト。テキストファイルのパスも指定可能。
* htsvoice: 使用する音声の種類 (デフォルト: /usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice)
* dictionary_dir: 辞書のディレクトリ (デフォルト: /var/lib/mecab/dic/open-jtalk/naist-jdic)
* output_filename: 動画の出力ファイル名 (デフォルト: output.mp4)
* background_image: 背景画像 (オプション)
* music_file: BGMとして使用する音楽ファイル (オプション)

### 注意事項
このツールは、テキストの各行を個別のセグメントとして処理します。そのため、大量のテキストを処理する際は、適切な区切りでテキストを分割することをおすすめします。
```
python ttv.py convert --output_filename=output.mp4 --text=speach_text.txt --background_image=bg.jpg --music_file=yume.mp3
```  
  
[サンプル動画を見る](https://github.com/yoshida-kazuo/WaZao/raw/main/output.mp4)  
サンプル動画のバックグラウンドミュージックには、甘茶さまの「夢」を使用させていただきました。  
* サイト名: 甘茶の音楽工房（英語表記＝Music Atelier Amacha）  
* 作曲者: 甘茶（英語表記＝Amacha）  
* URL: https://amachamusic.chagasi.com/  
