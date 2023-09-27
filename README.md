# WaZao
WaZaoは、テキストを音声に変換し、その音声を背景画像やBGMと合成して動画を生成するツールです。Open JTalk と FFmpeg を活用しています。

## 背景
WaZaoは、chatbotのコメントやレスポンス、eラーニングなどのテキストを音声に変換するニーズに応えるために開始されました。このツールは、ユーザーが効果的に映像素材を生成できるよう、複数の技術を統合して開発されました。

## 準備
環境 debian12.1, OpenJ Talk1.10, Python3.11, ffmpeg5.1.3  
### 依存関係
* fire: コマンドラインインターフェースを簡単に作成するためのライブラリ
* subprocess: Python からシェルコマンドを実行するためのモジュール
* open_jtalk: テキストを音声に変換するツール
* ffmpeg: 音声、画像、動画の変換・編集を行うツール
```shell
sudo apt install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001 ffmpeg
pip install -r requirements.txt
```

### リンク
* 英単語カナ変換辞書: [beg-eng.dic](https://fastapi.metacpan.org/source/MASH/Lingua-JA-Yomi-0.01/lib/Lingua/JA)

## 使い方
### 引数
* text: 変換するテキスト。テキストファイルのパスも指定可能。
* htsvoice: 使用する音声の種類 (デフォルト: /usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice)
* dictionary_dir: 辞書のディレクトリ (デフォルト: /var/lib/mecab/dic/open-jtalk/naist-jdic)
* output_filename: 動画の出力ファイル名 (デフォルト: output.mp4)
* mp3_output: 音声の出力ファイル名 (デフォルト: output.mp3)
* background: 背景の画像または動画 (オプション)
* music_file: BGMとして使用する音楽ファイル (オプション)
* en2kana_dic: カナ変換用の英単語ファイル (デフォルト: bep-eng.dic)

### 注意事項
このツールは、テキストの各行を個別のセグメントとして処理します。そのため、大量のテキストを処理する際は、適切な区切りでテキストを分割することをおすすめします。
```shell
python ttv.py convert --output_filename=output.mp4 --text=speach_text.txt --background=bg.jpg --music_file=yume.mp3
```  
* [背景画像サンプル](https://github.com/yoshida-kazuo/WaZao/raw/main/output.mp4)  
```shell
python ttv.py convert --output_filename=output.mp4 --text=speach_text.txt --background=bg.mp4 --music_file=yume.mp3
```  
* [背景動画サンプル](https://github.com/yoshida-kazuo/wazao/raw/main/output_movie.mp4)  
* [テキスト読み上げサンプル](https://github.com/yoshida-kazuo/wazao/raw/main/output.mp3)  

### 英単語をカナに変換する `bep-eng.dic` の利用方法
`bep-eng.dic` ファイルを実行ディレクトリと同じ階層に配置してください。
```shell
wget https://fastapi.metacpan.org/source/MASH/Lingua-JA-Yomi-0.01/lib/Lingua/JA/bep-eng.dic
python ttv.py convert --output_filename=output.mp4 --text=speach_text.txt --background=bg.mp4 --music_file=yume.mp3 --en2kana_dic=bep-eng.dic
```

## 使用リソースの著作権情報
### BGM
サンプル動画のバックグラウンドミュージックには、甘茶さまの「夢」を使用させていただきました。  
* サイト名: 甘茶の音楽工房（英語表記＝Music Atelier Amacha）  
* 作曲者: 甘茶（英語表記＝Amacha）  
* URL: https://amachamusic.chagasi.com/

### 背景動画
サンプル動画の背景動画には、Sakuraさまの「風景・海・船・航跡」を使用させていただきました。  
* サイト名: HYBRID CREATIVE MOVIE サクラ
* URL: https://www.home-movie.biz

## リンク
* Open JTalk : https://open-jtalk.sourceforge.net
