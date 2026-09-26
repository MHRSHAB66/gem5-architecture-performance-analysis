# no_cache.py - minimal SE-mode gem5 config WITHOUT any cache hierarchy
# ACA Project 3 - Part 1 Step 1 (baseline)
#
# Verified against gem5 v23.0.0.1 (build/X86/gem5.opt).
#
# System: single X86TimingSimpleCPU connected directly to a SystemXBar
# and a SimpleMemory (no L1/L2 caches). Every memory access therefore
# pays the SimpleMemory latency - there is no locality benefit at all.
#
# TimingSimpleCPU is used (not Atomic) so that the baseline is directly
# comparable with the Step-2 cache runs, which the assignment mandates
# to use TimingSimpleCPU.
#
# Usage:
#   gem5.opt -d <outdir> configs/no_cache.py <binary> [binary args...]
#            [--cpu-clock 2GHz] [--mem-size 512MB]

import argparse

import m5
from m5.objects import (
    AddrRange,
    Process,
    Root,
    SEWorkload,
    SimpleMemory,
    SrcClockDomain,
    System,
    SystemXBar,
    VoltageDomain,
    X86TimingSimpleCPU,
)

parser = argparse.ArgumentParser(
    description="gem5 SE-mode baseline system without caches"
)
parser.add_argument("binary", help="statically linked X86 binary to run")
parser.add_argument(
    "binary_args", nargs="*", default=[], help="arguments passed to the binary"
)
# 2GHz matches the se.py default cpu_clock so baseline and cache runs
# share the same CPU clock.
parser.add_argument("--cpu-clock", default="2GHz", help="CPU clock (default 2GHz)")
parser.add_argument("--mem-size", default="512MB", help="memory size (default 512MB)")
args = parser.parse_args()

system = System()

# Explicit clock domain and voltage domain
system.clk_domain = SrcClockDomain(
    clock=args.cpu_clock, voltage_domain=VoltageDomain()
)

# Timing memory mode (event-driven request/response), SE mode
system.mem_mode = "timing"
system.mem_ranges = [AddrRange(args.mem_size)]

# Single in-order CPU with timing memory accesses
system.cpu = X86TimingSimpleCPU()

# System crossbar: CPU ports connect DIRECTLY to the bus (no caches)
system.membus = SystemXBar()
system.cpu.icache_port = system.membus.cpu_side_ports
system.cpu.dcache_port = system.membus.cpu_side_ports

# x86 interrupt controller plumbing
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# SimpleMemory: fixed-latency memory model (assignment: --mem-type=SimpleMemory)
system.mem_ctrl = SimpleMemory(range=system.mem_ranges[0])
system.mem_ctrl.port = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

# SE-mode workload
binary = args.binary
system.workload = SEWorkload.init_compatible(binary)

process = Process()
process.cmd = [binary] + args.binary_args
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print(f"**** no_cache.py: beginning simulation of {binary}")
exit_event = m5.simulate()
print(
    f"**** no_cache.py: exiting @ tick {m5.curTick()} "
    f"because {exit_event.getCause()}"
)
