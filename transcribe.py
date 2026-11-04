"""
transcribe.py — 在本地把英文录音转成文字（NVIDIA Parakeet 模型，Apple Silicon 上用 MLX 运行）。

用法:
    python transcribe.py recording.m4a
    python transcribe.py recording.m4a --save out.txt

第一次运行会自动下载模型（约 1.2 GB），之后完全离线。
除了文字，还会顺带给出语速、长停顿，以及模型“没听太清”的词。
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np

try:
    import mlx.core as mx
    import parakeet_mlx.parakeet as _pk
    from parakeet_mlx import from_pretrained
except ImportError:
    sys.exit("缺少依赖。先运行: pip install -r requirements.txt\n"
             "（需要 Apple Silicon 的 Mac 和 Python 3.10 以上）")

MODEL_ID = "mlx-community/parakeet-tdt-0.6b-v3"


# ---------------------------------------------------------------------------
# 1. 音频读取：没装 ffmpeg 时，改用 macOS 自带的 afconvert
# ---------------------------------------------------------------------------
# parakeet-mlx 默认用 ffmpeg 解码音频。为了不让你额外装 ffmpeg，
# 这里在没有 ffmpeg 的情况下替换成 afconvert（macOS 自带）。

def _load_audio_with_afconvert(filename, sampling_rate, dtype=None):
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "audio.wav"
        cmd = ["afconvert", "-f", "WAVE", "-d", f"LEI16@{sampling_rate}", "-c", "1",
               str(filename), str(wav_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"音频转换失败（afconvert）:\n{result.stderr.strip()}")
        with wave.open(str(wav_path), "rb") as w:
            frames = w.readframes(w.getnframes())
    samples = np.frombuffer(frames, np.int16).flatten()
    return mx.array(samples).astype(mx.float32) / 32768.0


def setup_audio_loader() -> None:
    if shutil.which("ffmpeg"):
        return  # 有 ffmpeg 就用库自己的实现
    if shutil.which("afconvert"):
        _pk.load_audio = _load_audio_with_afconvert
        return
    sys.exit("找不到 ffmpeg 或 afconvert，没法读取音频。Mac 上可以运行: brew install ffmpeg")


# ---------------------------------------------------------------------------
# 2. 把模型输出的子词（token）拼回单词
# ---------------------------------------------------------------------------

@dataclass
class Word:
    text: str
    start: float
    end: float
    confidence: float  # 取组成这个词的各 token 中最低的置信度


def tokens_to_words(tokens) -> list[Word]:
    """
    Parakeet 输出的是子词，例如 " Glas" + "gow"。
    以空格开头的 token 表示新词的开始。
    """
    words: list[Word] = []
    for tok in tokens:
        piece = tok.text
        starts_new = not words or piece.startswith(" ")
        clean = piece.strip()
        if not clean:
            continue
        if starts_new:
            words.append(Word(clean, tok.start, tok.end, tok.confidence))
        else:
            w = words[-1]
            w.text += clean
            w.end = tok.end
            w.confidence = min(w.confidence, tok.confidence)
    return words


# ---------------------------------------------------------------------------
# 3. 简单的口语统计
# ---------------------------------------------------------------------------

def speaking_stats(words: list[Word], pause_threshold: float) -> dict:
    if not words:
        return {}
    span = words[-1].end - words[0].start
    pauses = [
        (prev.text, nxt.text, nxt.start - prev.end)
        for prev, nxt in zip(words, words[1:])
        if nxt.start - prev.end >= pause_threshold
    ]
    return {
        "word_count": len(words),
        "duration": span,
        "wpm": len(words) / span * 60 if span > 0 else 0.0,
        "pauses": pauses,
    }


# ---------------------------------------------------------------------------
# 4. 输出
# ---------------------------------------------------------------------------

def print_report(text: str, words: list[Word], stats: dict,
                 conf_threshold: float, pause_threshold: float) -> None:
    line = "=" * 60
    print(f"\n{line}\n转写文本\n{line}")
    print(text)

    if not stats:
        return

    print(f"\n{line}\n口语统计\n{line}")
    print(f"  词数      {stats['word_count']}")
    print(f"  说话时长  {stats['duration']:.1f} 秒")
    wpm = stats["wpm"]
    hint = "偏慢" if wpm < 110 else "偏快" if wpm > 170 else "正常"
    print(f"  语速      {wpm:.0f} 词/分钟（{hint}；日常对话大约 120–160）")

    pauses = stats["pauses"]
    print(f"  长停顿    {len(pauses)} 次（≥ {pause_threshold:g} 秒）")
    for before, after, gap in pauses:
        print(f"            “{before} … {after}”  停了 {gap:.1f} 秒")

    unsure = [w for w in words if w.confidence < conf_threshold]
    print(f"\n{line}\n模型没听太清的词（置信度 < {conf_threshold:.2f}）\n{line}")
    if not unsure:
        print("  没有")
    for w in unsure:
        print(f"  {w.text:<15} {w.confidence:.2f}   @ {w.start:.1f}s")
    print("\n  注：这只是识别模型的把握程度，可能是发音含糊、太小声或背景噪音，"
          "不等于发音评分。")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="本地英文语音转文字（Parakeet + MLX）")
    parser.add_argument("audio", type=Path, help="录音文件（m4a / mp3 / wav ...）")
    parser.add_argument("--model", default=MODEL_ID, help=f"Hugging Face 模型名，默认 {MODEL_ID}")
    parser.add_argument("--save", type=Path, help="把转写文本另存到这个文件")
    parser.add_argument("--confidence", type=float, default=0.6,
                        help="低于这个置信度的词会被列出来，默认 0.6")
    parser.add_argument("--pause", type=float, default=1.0,
                        help="超过这么多秒的停顿算“长停顿”，默认 1.0")
    args = parser.parse_args()

    if not args.audio.exists():
        sys.exit(f"找不到文件: {args.audio}")

    setup_audio_loader()

    print(f"加载模型 {args.model}（第一次会下载，约 1.2 GB）...")
    t0 = time.time()
    model = from_pretrained(args.model)
    print(f"模型就绪（{time.time() - t0:.1f} 秒），开始识别 ...")

    t1 = time.time()
    # chunk_duration：长录音按 2 分钟一段处理，避免占用太多内存；短录音不受影响
    result = model.transcribe(str(args.audio), chunk_duration=120)
    print(f"识别完成（{time.time() - t1:.1f} 秒）")

    words = tokens_to_words(result.tokens)
    stats = speaking_stats(words, args.pause)
    print_report(result.text, words, stats, args.confidence, args.pause)

    if args.save:
        args.save.write_text(result.text + "\n", encoding="utf-8")
        print(f"\n文本已保存到 {args.save}")


if __name__ == "__main__":
    main()
