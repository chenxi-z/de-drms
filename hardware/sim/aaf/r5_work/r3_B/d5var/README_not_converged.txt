A_trap_1e5.net  (trap, reltol=1e-5, 150us, maxstep 10n): LTspice 240 s 未收敛（rc=124），
                  已删除 324 MB 不完整 .raw，仅保留 .log/.net 作证据。
C_trap_1e6.net  (trap, reltol=1e-6, 150us, maxstep 5n): LTspice 240 s 未收敛（rc=124），
                  已删除 395 MB 不完整 .raw，仅保留 .log/.net 作证据。
结论：TI OPAx388 宏模型在 trap 积分器 + 收紧容差下会反复拒绝步长（log 中大量
"Simulation tolerance relaxed to achieve convergence"）。改用 gear 后 2 s 收敛。
