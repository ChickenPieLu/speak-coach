# speaking-coach

**English** | [中文](#中文说明)

A tool for practising spoken English. Current stage: transcribe English recordings locally on a Mac — no internet connection and no account required.

It uses NVIDIA's **Parakeet TDT 0.6B v3** model, running on Apple Silicon via [parakeet-mlx](https://github.com/senstella/parakeet-mlx).

## Requirements

- A Mac with Apple Silicon (M1 or later)
- **Python 3.10 or later**. Check with `python3 --version`; if it shows 3.9, install a newer one with `brew install python` or from python.org.

## Installation

```bash
git clone git@github.com:ChickenPieLu/speak-coach.git
cd speak-coach
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Record straight from the microphone (press Enter to start, Enter again to stop), then transcribe:

```bash
python transcribe.py                     # system default microphone
python transcribe.py --device AirPods    # pick a microphone by number or part of its name
python audio.py --list                   # list available microphones
```

Recordings are saved to `recordings/` (ignored by git). The first time, macOS asks whether your terminal may use the microphone; if you get only silence, enable it under System Settings → Privacy & Security → Microphone and restart the terminal.

Or transcribe an existing file, e.g. from Voice Memos:

```bash
python transcribe.py ~/Desktop/test.m4a
python transcribe.py ~/Desktop/test.m4a --save out.txt
```

- The first run downloads the model from Hugging Face (about 1.2 GB) into `~/.cache/huggingface/`. After that it works fully offline.
- No ffmpeg needed: if ffmpeg is not installed, the script reads audio with macOS's built-in `afconvert` instead.

## Output

The script's messages are in Chinese. It prints:

1. **Transcript**
2. **Speaking stats**: word count, speaking rate (words per minute), and where pauses longer than 1 second occur
3. **Words the model wasn't sure about**: words with low recognition confidence. This may point to unclear pronunciation, but it can also be caused by low volume or background noise. Treat it as a hint, not a pronunciation score.

Options:

| Option | Default | Description |
|---|---|---|
| `--confidence` | 0.6 | List words with confidence below this value |
| `--pause` | 1.0 | Minimum gap in seconds counted as a long pause |
| `--save` | — | Also save the transcript to this file |
| `--model` | `mlx-community/parakeet-tdt-0.6b-v3` | Use a different Parakeet model |
| `--device` | system default | Microphone to record with (number or part of its name) |

---

## 中文说明

英语口语练习工具。目前这一步：在 Mac 本地把英文录音转成文字，不联网、不需要任何账号。

用的模型是 NVIDIA 的 **Parakeet TDT 0.6B v3**，通过 [parakeet-mlx](https://github.com/senstella/parakeet-mlx) 在 Apple Silicon 上运行。

### 环境要求

- Apple Silicon 的 Mac（M1 及以后）
- **Python 3.10 或以上**。先运行 `python3 --version` 看一下；如果是 3.9，用 `brew install python` 或去 python.org 装个新的。

### 安装

```bash
git clone git@github.com:ChickenPieLu/speak-coach.git
cd speak-coach
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 使用

直接用麦克风录（按回车开始，再按回车结束），录完马上识别：

```bash
python transcribe.py                     # 系统默认麦克风
python transcribe.py --device AirPods    # 指定麦克风：编号或名字的一部分
python audio.py --list                   # 列出所有麦克风
```

录音存在 `recordings/` 文件夹里（不会提交到 git）。第一次录音时 macOS 会问终端能不能用麦克风；如果录出来全是静音，去 系统设置 → 隐私与安全性 → 麦克风 打开你的终端，然后重启终端。

也可以识别已有的录音文件，比如“语音备忘录”录的：

```bash
python transcribe.py ~/Desktop/test.m4a
python transcribe.py ~/Desktop/test.m4a --save out.txt
```

- 第一次运行会从 Hugging Face 下载模型（约 1.2 GB），存在 `~/.cache/huggingface/`，之后完全离线。
- 不需要装 ffmpeg：没有 ffmpeg 时，脚本会改用 macOS 自带的 `afconvert` 读取音频。

### 输出

1. **转写文本**
2. **口语统计**：词数、语速（词/分钟）、超过 1 秒的长停顿出现在哪里
3. **模型没听太清的词**：识别置信度低的词。可能是发音含糊，也可能只是太小声或有噪音，仅供参考，不是发音评分。

可调参数：

| 参数 | 默认 | 作用 |
|---|---|---|
| `--confidence` | 0.6 | 低于这个置信度的词会被列出来 |
| `--pause` | 1.0 | 超过多少秒算长停顿 |
| `--save` | — | 把文本另存到文件 |
| `--model` | `mlx-community/parakeet-tdt-0.6b-v3` | 换用其他 Parakeet 模型 |
| `--device` | 系统默认 | 录音用的麦克风（编号或名字的一部分） |
