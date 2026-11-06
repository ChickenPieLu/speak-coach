"""
audio.py — 用麦克风录音：按回车开始，再按回车结束，存成 wav。

单独使用:
    python audio.py --list                 # 列出所有麦克风
    python audio.py                        # 用系统默认麦克风录一段
    python audio.py --device 2             # 用编号 2 的麦克风
    python audio.py --device AirPods       # 名字里包含 AirPods 的麦克风
    python audio.py --out my.wav

也可以在别的脚本里 import record_to_file() 使用。
"""

from __future__ import annotations

import argparse
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sys.exit("缺少 sounddevice。先运行: pip install -r requirements.txt")

RECORDINGS_DIR = Path("recordings")


# ---------------------------------------------------------------------------
# 麦克风选择
# ---------------------------------------------------------------------------

def list_input_devices() -> None:
    default_in = sd.default.device[0]
    print("可用的麦克风（* 是系统默认）：")
    for i, dev in enumerate(sd.query_devices()):
        if dev["max_input_channels"] > 0:
            mark = "*" if i == default_in else " "
            print(f"  {mark} [{i}] {dev['name']}  ({dev['default_samplerate']:.0f} Hz)")


def resolve_device(device: str | None) -> int | None:
    """None = 系统默认；数字 = 设备编号；其他 = 按名字模糊匹配。"""
    if device is None:
        return None
    if device.isdigit():
        return int(device)
    matches = [
        i for i, dev in enumerate(sd.query_devices())
        if dev["max_input_channels"] > 0 and device.lower() in dev["name"].lower()
    ]
    if not matches:
        list_input_devices()
        sys.exit(f"\n没找到名字包含 “{device}” 的麦克风。")
    return matches[0]


# ---------------------------------------------------------------------------
# 录音
# ---------------------------------------------------------------------------

def record_until_enter(device: int | None = None) -> tuple[np.ndarray, int]:
    """按回车开始、再按回车结束。返回 (单声道 float32 采样, 采样率)。"""
    info = sd.query_devices(device, "input")
    # 用麦克风自己的采样率录，避免设备不支持 16kHz；转成 16kHz 的事交给识别那一步
    samplerate = int(info["default_samplerate"])
    chunks: list[np.ndarray] = []

    def callback(indata, frames, time_info, status):
        if status:
            print(f"  （录音警告: {status}）", file=sys.stderr)
        chunks.append(indata[:, 0].copy())

    input(f"麦克风: {info['name']}\n按回车开始录音 ...")
    with sd.InputStream(device=device, channels=1, samplerate=samplerate,
                        dtype="float32", callback=callback):
        t0 = time.time()
        input("● 录音中 ... 说完按回车结束")
    print(f"录音结束，共 {time.time() - t0:.1f} 秒")

    samples = np.concatenate(chunks) if chunks else np.zeros(0, np.float32)
    if samples.size and np.abs(samples).max() < 1e-4:
        print("⚠ 录到的几乎全是静音。如果你确实说话了，可能是终端没有麦克风权限：\n"
              "  系统设置 → 隐私与安全性 → 麦克风，打开你用的终端（Terminal / iTerm / VS Code），"
              "然后重启终端。")
    return samples, samplerate


def save_wav(samples: np.ndarray, samplerate: int, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(samplerate)
        w.writeframes(pcm.tobytes())


def default_path() -> Path:
    return RECORDINGS_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.wav"


def record_to_file(device: str | None = None, out: Path | None = None) -> Path:
    samples, sr = record_until_enter(resolve_device(device))
    path = out or default_path()
    save_wav(samples, sr, path)
    print(f"已保存到 {path}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="麦克风录音（按回车开始/结束）")
    parser.add_argument("--list", action="store_true", help="列出所有麦克风")
    parser.add_argument("--device", help="麦克风编号或名字的一部分，默认用系统默认麦克风")
    parser.add_argument("--out", type=Path, help="保存路径，默认 recordings/时间.wav")
    args = parser.parse_args()

    if args.list:
        list_input_devices()
        return
    record_to_file(args.device, args.out)


if __name__ == "__main__":
    main()
