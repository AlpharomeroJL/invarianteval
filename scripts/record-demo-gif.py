#!/usr/bin/env python3
"""Record docs/demo.gif from real InvariantEval gate runs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo.gif"

WIDTH = 920
HEIGHT = 520
BG = (15, 20, 25)
FG = (231, 236, 243)
MUTED = (157, 180, 208)
GREEN = (81, 207, 102)
RED = (255, 107, 107)
CYAN = (77, 171, 247)
YELLOW = (255, 212, 59)
PROMPT = (61, 90, 128)
FONT_CANDIDATES = [
    Path(r"C:\Windows\Fonts\consola.ttf"),
    Path(r"C:\Windows\Fonts\CascadiaMono.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_CANDIDATES:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def run_cmd(args: list[str]) -> tuple[str, int]:
    proc = subprocess.run(
        args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return out.strip(), proc.returncode


def blank_frame(title: str = "InvariantEval") -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)
    font = load_font(22)
    small = load_font(14)
    draw.text((24, 18), title, fill=FG, font=font)
    draw.text((24, 48), "safety-invariant eval gate", fill=MUTED, font=small)
    draw.line((24, 72, WIDTH - 24, 72), fill=PROMPT, width=1)
    return img


def draw_terminal(
    img: Image.Image,
    lines: list[tuple[str, tuple[int, int, int]]],
    y_start: int = 88,
) -> None:
    draw = ImageDraw.Draw(img)
    font = load_font(15)
    y = y_start
    for text, color in lines:
        draw.text((24, y), text, fill=color, font=font)
        y += 22


def frames_typing(command: str, prefix: str = "$ ") -> list[Image.Image]:
    frames: list[Image.Image] = []
    for i in range(1, len(command) + 1):
        img = blank_frame()
        draw_terminal(img, [(prefix + command[:i] + "▌", CYAN)])
        frames.append(img)
    frames.append(blank_frame())
    draw_terminal(frames[-1], [(prefix + command, CYAN)])
    return frames


def frames_hold(base: Image.Image, repeats: int = 12) -> list[Image.Image]:
    return [base.copy() for _ in range(repeats)]


def wrap_output(text: str, max_chars: int = 96) -> list[str]:
    rows: list[str] = []
    for line in text.splitlines():
        while len(line) > max_chars:
            rows.append(line[:max_chars])
            line = line[max_chars:]
        rows.append(line)
    return rows


def frame_with_output(header: str, command: str, output: str, exit_code: int | None) -> Image.Image:
    img = blank_frame()
    lines: list[tuple[str, tuple[int, int, int]]] = [(f"$ {command}", CYAN)]
    for row in wrap_output(output):
        if "Invariant failures: 0" in row or "Cases: 5/5 passed" in row:
            lines.append((row, GREEN))
        elif "Invariant Failures" in row or "never_auto_filled" in row:
            lines.append((row, RED))
        elif row.startswith("##") or row.startswith("|") or row.startswith("- **"):
            lines.append((row, YELLOW if "FAIL" in row or "Failures" in row else FG))
        elif "invariant failures: 1" in row.lower() or "Cases passed | 4/5" in row:
            lines.append((row, RED))
        else:
            lines.append((row, FG))
    if exit_code is not None:
        color = GREEN if exit_code == 0 else RED
        lines.append((f"exit code: {exit_code}", color))
    draw_terminal(img, lines[:16])
    return img


def save_gif(frames: list[Image.Image], path: Path, duration_ms: int = 90) -> None:
    if not frames:
        raise RuntimeError("No frames to save")
    first, *rest = frames
    first.save(
        path,
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=0,
        optimize=True,
    )


def main() -> int:
    good_cmd = (
        "invarianteval run examples/fire-inspection-extraction/suite.yaml "
        "--provider fixture --fixtures fixtures/good --fail-on-invariant"
    )
    bad_cmd = (
        "invarianteval run examples/fire-inspection-extraction/suite.yaml "
        "--provider fixture --fixtures fixtures/regressed --fail-on-invariant --format summary"
    )

    good_out, good_rc = run_cmd(
        [
            sys.executable,
            "-m",
            "invarianteval.cli",
            "run",
            "examples/fire-inspection-extraction/suite.yaml",
            "--provider",
            "fixture",
            "--fixtures",
            "examples/fire-inspection-extraction/fixtures/good",
            "--fail-on-invariant",
        ]
    )
    bad_out, bad_rc = run_cmd(
        [
            sys.executable,
            "-m",
            "invarianteval.cli",
            "run",
            "examples/fire-inspection-extraction/suite.yaml",
            "--provider",
            "fixture",
            "--fixtures",
            "examples/fire-inspection-extraction/fixtures/regressed",
            "--fail-on-invariant",
            "--format",
            "summary",
        ]
    )
    if good_rc != 0:
        print("Good run failed unexpectedly", file=sys.stderr)
        return 1
    if bad_rc == 0:
        print("Regressed run should have failed", file=sys.stderr)
        return 1

    frames: list[Image.Image] = []
    frames.extend(frames_hold(blank_frame("InvariantEval — demo"), 18))
    frames.extend(frames_typing(good_cmd))
    frames.extend(frames_hold(frame_with_output("Good run", good_cmd, good_out, good_rc), 28))
    frames.extend(frames_typing(bad_cmd))
    frames.extend(frames_hold(frame_with_output("Regressed run", bad_cmd, bad_out, bad_rc), 45))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    save_gif(frames, OUT)
    print(f"Wrote {OUT} ({len(frames)} frames, {OUT.stat().st_size // 1024} KiB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
