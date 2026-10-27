# 精读笔记 · Stein 1986《An Efficient Method of Sampling for Statistical Circuit Design》（IEEE TCAD）

> 格式：出处 → 核心命题（原文引用+页码）→ 关键数值 → 对 P1/P2/P3 对照 → 没读到的。
> 本 PDF 第 2–7 页为扫描件无文本层；引文经 300 dpi 页图目视逐字核对（页码 = PDF 物理页 1–7，印刷页 23–29）。

## 出处
- Stein, Michael L.（时属 IBM Thomas J. Watson Research Center；现 University of Chicago 统计系）. "An Efficient Method of Sampling for Statistical Circuit Design." *IEEE Transactions on Computer-Aided Design*, vol. CAD-5, no. 1, pp. 23–29, Jan. 1986. DOI: 10.1109/tcad.1986.1270174.
- PDF：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/H8-灵敏度与统计电路设计/stein1986n.pdf`（7 页）。

## 核心命题（原文）
1. **问题设定：换均值后重估良率/期望成本，旧样本不能直接搬**（p.1 摘要）：> "In using these methods, we are often faced with the problem of estimating the cost under one distribution given that we have sampled under another distribution. However, if the sam-pling distribution and the distribution under which the expected cost is to be estimated differ too much, then a poor estimator of the expected cost may be obtained."；方法贡献：> "A new method of doing further sampling only in regions where the original sampling distribution under-sampled is in-troduced. By using this procedure, large reductions in variance are possible with only a small amount of additional sampling."
2. **混合密度 + 分层抽样估计器**（p.2）：> "f_m(x) = αf_0(x) + (1 − α) f_2(x)"（式(4)，α = N/(N+N')），> "We have what is known as a stratified sample with pro-portional allocation [2], [8]. In this sampling method, in-stead of choosing an independent sample of size M under some density g, we choose M_i points under a density g_i."（旧 N 个样本与新 N' 个样本合并成比例分配的分层样本——优于丢弃重采。）
3. **f₂ 的选取准则：压低似然比上界 k**（p.2）：> "we seek to find the den-sity f_2 so that f_m, defined in (4), satisfies > f_1(x) ≤ kf_m(x) ∀x (5) where k is as small as possible."（该约束下有方差界 var(Ĉ) ≤ k·E₂(C²)−(E₁C)²（式(7)），k 越小方差上界越低；显式解 f₂ ≡ (f₁−kf₀)⁺[k(1−α)]⁻¹（式(8)）。）
4. **适用边界：两分布的 Mahalanobis 距离必须适中**（p.5）：> "It is important to note that part of the reason the mixed density approach worked well in this case is that the density f_1 was only a moderate distance from f_0: the Mahal-anobis distance between the two densities is 2. If the dis-tance between f_0 and f_1 had been greater, a Mahalanobis distance more than 4, say, than the procedure would not have worked so well."（原文印 "than"，应为 "then"；经验界：距离 ≈2 有效、>4 失效。）
5. **高维警示：边缘"几乎没变"而联合分布剧变**（p.6）：> "The first is that if we change, say, the means of the distributions of a large number of compo-nents only slightly, we may have changed, in a relevant way, the joint distribution of all of the components by a great deal."；> "The second problem, and a related one, is that estimates of expected cost may be highly sensitive to slight misspecifications in the marginals of the distribution of a large number of components. The larger the number of components, the more critical it is that we specify their marginal distributions correctly."（500 维例：边缘各只差 0.1，Mahalanobis 距离已达 5。）
6. **分布污染的良率灾难：低估两个数量级**（p.6）：> "suppose we believe that each of 500 independent components have a N(0, 1) distribution, when in fact they each have a very small amount of contamination; i.e., the true distribution of each component is a mixture of two normal distributions, > 0.99N(0, 1) + 0.01N(0, 9)."（成本 C(x) = I{x₍₁₎² ≥ 6901}；名义失效率 ≈0.0013 vs 真实 ≈0.11：> "Thus on average, we will under-estimate the true failure rate by two orders of magnitude."）
7. **与灵敏度分析衔接的实用建议**（p.6 结论）：> "Statistical design techniques will probably work best if the starting value for the joint distribution of the components is chosen well. ... if we can focus on those components deemed to be most critical (such as by a sensi-tivity analysis), and try to find good means and tolerances for these components, leaving the other component values constant."（灵敏度筛选关键元件 → 只对其做统计精调——H8 轴①×②的工程衔接点。）

## 关键数值（原文）
- 算例电路：current switch emitter follower（[10] Brayton & Spence p.340，Fig.1），仅 5 个电阻 R1–R5 独立正态变化（Table 1，p.4）：R1 均值 1→0.99（σ0.02）、R2 0.4→0.405、R3 0.4555→0.4525、R4 0.815→0.81、R5 0.615→0.62（σ 各 0.01）。
- 成本 1：C(x) = I{U_A−(d₄(x)>3.4 or p(x)>5)}（ defective 判据：任一延迟 >34 ns 或平均功耗 >51 mW，50 ns 时窗，p.4）；缺陷率：f₀ 下 0.30、f₁ 下 0.12。
- 方差对比（p.4）：N=100（f₀）基础方差 0.0036；加 N'=5 个新采样 + k=4：混合密度估计器方差 0.0012，线性组合估计器 0.0031；> "For the linear combination estimator to achieve the same variance as the mixed density estimator based on 5 additional simulations, we would have to take 60 additional simulations under f_1."（5 个新样本 ≈ 60 个重采样本的等效。）
- 成本 2：C(x) = Σ₍m=1..4₎(d_m(x)−3)⁺ + (p(x)−50)⁺；E₀C = 0.71、E₁C = 0.77（p.4）；混合 0.0041 vs 线性组合 0.016（p.5 顶部：> "0.016. Thus with both cost functions, the mixed density estimator has much lower variance than the linear combi-nation estimator with the same number of additional sim-ulations."）。
- Mahalanobis 距离（p.5）：本例 f₀↔f₁ 距离 = 2；>4 失效。
- 500 维例（p.5–6）：f₀ = N(0, 0.9I)、f₁ = N(0, I)：P(|X|² ≥ 540) = 0.006 vs 0.1——> "Thus under f_0, we are vastly un-dersampling those points that are far from the origin"；单分量均值偏 0.1 → Mahalanobis 距离 5。
- 界（p.7）：成本有界 |C| ≤ M 时 > "N var_0(Ê_1C) ≤ M²I(f_0, f_1)"，其中距离测度 I(f₀,f₁) = ∫(f₁/f₀)²f₀dx = var₀(f₁/f₀)+1（式(16)）。

## 对 P1/P2/P3 的对照
- **P1（消去条件/失配→G_DC）**：低。本文是 Monte-Carlo 估计方差缩减（重要性采样/分层采样/混合密度）的统计学论文，处理"元件分布→良率期望"而非"元件偏差→传递函数"的灵敏度传递；算例中元件**独立**正态，无匹配对/相关性结构，也无任何网络函数恒等式。与 P1 无理论接口。
- **P2（Kelvin 结构地板）**：无。
- **P3（平坦度衰减上界）**：无。全文无频域/无源网络内容。
- **方法学（D1–D10）**：中-高。这是 H8 轴②"良率仿真/Monte Carlo"支线的方差效率文献：①若 P1/P3 的验证流程要跑 Monte-Carlo（如失配扫描），其"混合密度+分层"可将补采样本需求降一个量级（5 vs 60）；②高维警示（边缘微小误设 → 良率估计错两个数量级）对任何"用 MC 验证失配裕度"的门槛判据是必须引用的健壮性边界；③"灵敏度筛选关键元件再统计精调"是 D 系列门槛化（先定关键项）的先例表述。
- **killRisk**：无威胁。纯统计算法论文，与 P1 四主张零重叠。

## 没读到的
- Appendix A/B 的完整证明（p.7 已目视，式(17)–(21) 推导细节仅粗读）。
- 参考文献 [3]（Antreich & Koblitz, "Design centering by yield prediction," IEEE Trans. CAS-29, Feb 1982）与 [5]（Soin & Spence, Proc. IEEE 1980）——被本文对比并改进的"线性组合估计器"原文献，未读；如需引用该对比须回溯。
- 算例中 [10] Brayton & Spence《Sensitivity and Optimization》（Elsevier 1980）的电路与原始上下文未读。
- Fig.2 波形图（输人/输出 ms 级波形）与 Fig.1 电路图仅确认存在，未提取数值。
