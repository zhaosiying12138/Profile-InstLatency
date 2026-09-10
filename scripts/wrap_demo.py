#!/usr/bin/env python3
"""Wrap an llc-produced function .s into a runnable _start program with
__yx_marker_*region_{start,end} labels around the first vsetvli..body, and
also emit region_<v>.s (the bare instruction sequence for llvm-mca)."""
import re, sys

src, dst = sys.argv[1], sys.argv[2]
lines = open(src).read().splitlines()
vec = [l for l in lines if re.match(r"\s*v(setvli|setivli|setvl|divu|mul|add|slideup|redsum)(\.|\s)", l)]
assert vec, "no vector instructions found"

tag = "region"
body = []
body.append("    # ---- setup ----")
body.append("    li x5, 8")
body.append("    vmv.v.i v8, 3")
body.append("    vmv.v.i v9, 5")
body.append("    la x10, __yx_out")
body += [f"    li x{r}, {r}" for r in range(6, 10)]
body.append("    .balign 64")
body.append("    j 1f")
body += ["    li a7, 93", "    li a0, 0", "    ecall", "1:"]
body.append(f"    .globl __yx_marker_ab_{tag}_start")
body.append(f"__yx_marker_ab_{tag}_start:")
body += ["    " + l.strip() for l in vec]
body.append(f"    .globl __yx_marker_ab_{tag}_end")
body.append(f"__yx_marker_ab_{tag}_end:")
body += ["    # ---- exit ----", "    li a7, 93", "    li a0, 0", "    ecall"]

open(dst, "w").write(
    "# wrapped demo: " + src + "\n.text\n.global _start\n_start:\n" +
    "\n".join(body) + "\n.section .data\n.balign 64\n__yx_out:\n    .space 256\n")

# bare region for llvm-mca (vsetvli + instructions)
v = "yx" if "_yx." in src else "generic"
region = dst.rsplit("/", 1)[0] + f"/region_{v}.s"
open(region, "w").write("\n".join("    " + l.strip() for l in vec) + "\n")
print(f"wrapped {len(vec)} vector instructions -> {dst}, region -> {region}")
