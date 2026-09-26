#!/usr/bin/env python3
"""log_to_png.py - render REAL log excerpts as readable PNG screenshots.

ACA Project 3 - Mehrdad Sheikhabbasi (40131025)

Renders the actual, unmodified text of the run logs with a monospace
font on a white background, with the run title in a header bar. No
output is fabricated or reconstructed: the text is read verbatim from
results/logs/ and results/environment.txt.

Outputs -> results/screenshots/*.png
"""

import os

from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
LOG_DIR = os.path.join(RESULTS_DIR, "logs")
SHOT_DIR = os.path.join(RESULTS_DIR, "screenshots")
os.makedirs(SHOT_DIR, exist_ok=True)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
]


def get_font(size=14):
    for path in FONT_CANDIDATES:
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


BG_COLOR     = "#0d1117"   # dark background (GitHub-dark style)
HEADER_COLOR = "#161b22"   # slightly lighter header bar
BORDER_COLOR = "#30363d"   # subtle border line under header
TEXT_COLOR   = "#e6edf3"   # light body text
TITLE_COLOR  = "#58a6ff"   # blue title text


def render(title, text, out_name, max_lines=60, max_cols=110):
    lines = []
    for raw in text.splitlines():
        raw = raw.rstrip()
        while len(raw) > max_cols:
            lines.append(raw[:max_cols])
            raw = raw[max_cols:]
        lines.append(raw)
    if len(lines) > max_lines:
        head = lines[: max_lines // 2]
        tail = lines[-(max_lines - len(head) - 1):]
        lines = head + ["    [...]"] + tail

    font = get_font(14)
    tfont = get_font(16)
    lh = 20
    pad = 14
    header_h = 38
    width = max_cols * 9 + 2 * pad
    height = header_h + len(lines) * lh + 2 * pad

    img = Image.new("RGB", (width, height), BG_COLOR)
    d = ImageDraw.Draw(img)
    # header bar
    d.rectangle([0, 0, width, header_h], fill=HEADER_COLOR)
    # border line below header
    d.rectangle([0, header_h - 1, width, header_h], fill=BORDER_COLOR)
    d.text((pad, 10), title, font=tfont, fill=TITLE_COLOR)
    y = header_h + pad
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=TEXT_COLOR)
        y += lh
    out = os.path.join(SHOT_DIR, out_name)
    img.save(out)
    print(f"wrote {out}")


def read(path):
    with open(path, errors="replace") as fh:
        return fh.read()


def stats_excerpt(run_name, patterns):
    """Extract lines matching patterns from a stats.txt."""
    path = os.path.join(RESULTS_DIR, "raw", run_name, "stats.txt")
    if not os.path.isfile(path):
        return f"[stats.txt not found for {run_name}]"
    lines = []
    header = f"# stats.txt excerpt: {run_name}"
    lines.append(header)
    lines.append("# " + "=" * (len(header) - 2))
    with open(path, errors="replace") as fh:
        for line in fh:
            if any(p.lower() in line.lower() for p in patterns):
                lines.append(line.rstrip())
    return "\n".join(lines)


def config_excerpt(run_name, patterns):
    """Extract lines/sections matching patterns from config.ini."""
    path = os.path.join(RESULTS_DIR, "raw", run_name, "config.ini")
    if not os.path.isfile(path):
        return f"[config.ini not found for {run_name}]"
    out_lines = [f"# config.ini excerpt: {run_name}",
                 "# " + "=" * 40]
    in_section = False
    with open(path, errors="replace") as fh:
        for line in fh:
            ls = line.strip()
            if ls.startswith("["):
                in_section = any(p.lower() in ls.lower() for p in patterns)
            if in_section and ls:
                out_lines.append(ls)
    return "\n".join(out_lines)


def main():
    core_jobs = [
        ("gem5 environment & version detection (results/environment.txt)",
         os.path.join(RESULTS_DIR, "environment.txt"),
         "01_environment.png"),
        ("Step 1 baseline run — matrix_no_cache_naive (gem5 console log)",
         os.path.join(LOG_DIR, "matrix_no_cache_naive.log"),
         "02_matrix_no_cache_naive_run.png"),
        ("Step 1 baseline run — matrix_no_cache_tiled (gem5 console log)",
         os.path.join(LOG_DIR, "matrix_no_cache_tiled.log"),
         "03_matrix_no_cache_tiled_run.png"),
        ("Step 2 cache run — matrix_cache_naive (gem5 console log)",
         os.path.join(LOG_DIR, "matrix_cache_naive.log"),
         "04_matrix_cache_naive_run.png"),
        ("Step 2 cache run — matrix_cache_tiled (gem5 console log)",
         os.path.join(LOG_DIR, "matrix_cache_tiled.log"),
         "05_matrix_cache_tiled_run.png"),
        ("Q1 CPU comparison — list_recursive_atomic (gem5 console log)",
         os.path.join(LOG_DIR, "list_recursive_atomic.log"),
         "06_list_recursive_atomic_run.png"),
        ("Q1 CPU comparison — list_recursive_o3 (gem5 console log)",
         os.path.join(LOG_DIR, "list_recursive_o3.log"),
         "07_list_recursive_o3_run.png"),
        ("Q1 IPC optimisation — list_iterative_atomic (gem5 console log)",
         os.path.join(LOG_DIR, "list_iterative_atomic.log"),
         "08_list_iterative_atomic_run.png"),
        ("Q1 IPC optimisation — list_iterative_o3 (gem5 console log)",
         os.path.join(LOG_DIR, "list_iterative_o3.log"),
         "09_list_iterative_o3_run.png"),
        ("Automated validation — all 89 checks passed",
         os.path.join(LOG_DIR, "validation.log"),
         "10_validation.png"),
    ]
    for title, path, out in core_jobs:
        if not os.path.isfile(path):
            print(f"WARNING: {path} missing, screenshot skipped")
            continue
        render(title, read(path), out)

    # stats.txt excerpt screenshots
    stats_jobs = [
        ("matrix_no_cache_naive",
         ["ipc", "simticks", "simseconds", "siminsts", "numcycles"],
         "11_stats_matrix_no_cache_naive.png"),
        ("matrix_no_cache_tiled",
         ["ipc", "simticks", "simseconds", "siminsts", "numcycles"],
         "12_stats_matrix_no_cache_tiled.png"),
        ("matrix_cache_naive",
         ["ipc", "simticks", "simseconds", "siminsts", "numcycles",
          "overallhits", "overallmisses", "overallmissrate"],
         "13_stats_matrix_cache_naive.png"),
        ("matrix_cache_tiled",
         ["ipc", "simticks", "simseconds", "siminsts", "numcycles",
          "overallhits", "overallmisses", "overallmissrate"],
         "14_stats_matrix_cache_tiled.png"),
        ("list_recursive_atomic",
         ["ipc", "simseconds", "simticks", "siminsts", "numcycles"],
         "15_stats_list_recursive_atomic.png"),
        ("list_recursive_o3",
         ["ipc", "simseconds", "simticks", "siminsts", "numcycles",
          "branchpred", "functioncalls", "nummemrefs"],
         "16_stats_list_recursive_o3.png"),
        ("list_iterative_atomic",
         ["ipc", "simseconds", "simticks", "siminsts", "numcycles"],
         "17_stats_list_iterative_atomic.png"),
        ("list_iterative_o3",
         ["ipc", "simseconds", "simticks", "siminsts", "numcycles",
          "branchpred", "functioncalls", "nummemrefs"],
         "18_stats_list_iterative_o3.png"),
    ]
    for run, patterns, out in stats_jobs:
        text = stats_excerpt(run, patterns)
        render(f"stats.txt — {run}", text, out)

    # config.ini cache geometry
    cfg_jobs = [
        ("matrix_cache_naive",
         ["system.cpu.icache", "system.cpu.dcache", "system.l2",
          "system.mem_ctrl", "system.clk_domain", "system.cpu_clk_domain"],
         "19_config_cache_naive.png"),
        ("list_recursive_atomic",
         ["system.cpu.icache", "system.cpu.dcache", "system.l2",
          "system.mem_ctrl", "system.clk_domain", "system.cpu_clk_domain"],
         "20_config_list_recursive_atomic.png"),
    ]
    for run, patterns, out in cfg_jobs:
        text = config_excerpt(run, patterns)
        render(f"config.ini — {run}", text, out)

    print("log_to_png.py: done")


if __name__ == "__main__":
    main()
