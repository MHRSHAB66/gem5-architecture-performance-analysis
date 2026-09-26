# configs/

## no_cache.py

Minimal SE-mode gem5 configuration **without any cache hierarchy**, used for
Part 1 Step 1 (baseline). Verified against gem5 **v23.0.0.1**.

- CPU: `X86TimingSimpleCPU` (in-order, timing memory accesses) — chosen so the
  baseline is directly comparable with the Step-2 cache runs, which the
  assignment mandates to use `TimingSimpleCPU`.
- Memory: `SimpleMemory` (fixed-latency model, default 30 ns latency,
  12.8 GB/s bandwidth), size `512MB` (explicit, same as all other runs).
- Clock: explicit `SrcClockDomain`, default `2GHz` — matching the `se.py`
  default `--cpu-clock` used in the Step-2 cache runs.
- No L1/L2 caches: both CPU ports connect directly to the `SystemXBar`.
- Mode: SE (Syscall Emulation), `mem_mode = "timing"`.

Usage:

```bash
$GEM5_ROOT/build/X86/gem5.opt -d <outdir> configs/no_cache.py <binary> [args...]
```

## Cache runs (Step 2) and Question 1

These use the official config shipped with gem5:
`$GEM5_ROOT/configs/deprecated/example/se.py` — see `scripts/run_matrix_cache.sh`
and `scripts/run_linked_list.sh` for the exact flags. All parameters
(`--cpu-clock=2GHz`, `--mem-type=SimpleMemory`, `--mem-size=512MB`, cache
geometry L1I/L1D 32kB 4-way, L2 256kB 8-way, 64B lines) are kept identical
across runs; only the variable under study (algorithm or CPU model) changes.
