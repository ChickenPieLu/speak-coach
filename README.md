# speaking-coach

英语口语练习工具。目前这一步：在 Mac 本地把英文录音转成文字，不联网、不需要任何账号。

用的模型是 NVIDIA 的 **Parakeet TDT 0.6B v3**，通过 [parakeet-mlx](https://github.com/senstella/parakeet-mlx) 在 Apple Silicon 上运行。

## 环境要求

- Apple Silicon 的 Mac（M1 及以后）
- **Python 3.10 或以上**。先运行 `python3 --version` 看一下；如果是 3.9，用 `brew install python` 或去 python.org 装个新的。

## 安装

```bash
cd ~/Projects/github_projects/speaking-coach
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使用

用“语音备忘录”录一段英文，然后：

```bash
python transcribe.py ~/Desktop/test.m4a
python transcribe.py ~/Desktop/test.m4a --save out.txt
```

- 第一次运行会从 Hugging Face 下载模型（约 1.2 GB），存在 `~/.cache/huggingface/`，之后完全离线。
- 不需要装 ffmpeg：没有 ffmpeg 时，脚本会改用 macOS 自带的 `afconvert` 读取音频。

## 输出

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
