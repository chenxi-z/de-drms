# 全文缺件与代下载清单（2026-10-27 重新盘点）

> **可直接转交下载人员。** 旧 199 条请求及“65/66 篇未到”的计数已被实际库存覆盖。本表只列当前正式 bib 中无可用目标全文的条目，已到货不再重复请求；完整状态总账是 `unfetched-papers.csv`（249 条题录，包括已到货）。
> PDF 放 Obsidian：`/home/anning/Documents/Obsidian Vault/20-硬件工程/10-项目设计/p1-文献谱系/fulltext/<H轴>/`，按下表 key 命名 `key.pdf`。**不要放本 Git 仓库**。取得后需核对题名/作者/页数；HTML、摘要页和错误同名论文不算到货。
> “直取受限”可能是付费访问，也可能是开放资料的反爬/网络问题；403/418/超时不用于认定付费属性。未逐条尝试的资料单独标明。只需先处理 P0，P1/P2 按研究需要逐批处理。

本次正式 bib **249 条**；需获取/核对入口 **80 条**（P0 10 / P1 17 / P2 53）。本轮累计成功补全文 **8 份**；其中 Xin、Tadeusiewicz、Kundert 指定段落已核，不宣称整篇已精读。

## 先下载 P0：直接影响核心条件与先行工作判断

| key / 建议文件名 | 完整题录 | DOI / 获取入口 | 当前状态 | 获取用途 |
| --- | --- | --- | --- | --- |
| `fialkow1951rcladder.pdf` | The Transfer Function of an R‐C Ladder Network；Fialkow, Aaron and Gerst, Irving；1951；Journal of Mathematics and Physics | [DOI](https://doi.org/10.1002/sapm195130149) | 直取受限；需机构/浏览器或代下 | N1：RC 梯形传函与元件/可实现性约束的经典基线，防止重复已有综合结果 |
| `fialkow1952rcnetworks.pdf` | The transfer function of general two terminal-pair RC networks；Fialkow, Aaron and Gerst, Irving；1952；Quarterly of Applied Mathematics | [DOI](https://doi.org/10.1090/qam/49081) | 直取受限；需机构/浏览器或代下 | N1：一般 RC 两端口传函与实现条件，界定同传函与端接等效的差别 |
| `guillemin1949rcsynthesis.pdf` | Synthesis of RC‐Networks；Guillemin, E. A.；1949；Journal of Mathematics and Physics | [DOI](https://doi.org/10.1002/sapm194928122) | 直取受限；需机构/浏览器或代下 | N1：RC 网络综合基础；需区分已知综合程序与本项目新增元件条件 |
| `guillemin1957synthesis.pdf` | Synthesis of Passive Networks: Theory and Methods Appropriate to the Realization and Approximation Problems；Guillemin, Ernst A.；1957；John Wiley & Sons | [入口](https://openlibrary.org/books/OL4903945M/Synthesis_of_passive_networks) | 未有全文；本轮未逐条尝试 | N1：RC 网络综合相关章节；不需为本轮盲读整本 |
| `moschytz1999realizability.pdf` | Realizability constraints for third-order impedance-tapered allpole filters；Moschytz, G.S.；1999；IEEE Transactions on Circuits and Systems II: Analog and Digital Signal Processing | [DOI](https://doi.org/10.1109/82.782054) | 直取受限；需机构/浏览器或代下 | N3：三阶可实现性约束；避免把已知界作为新理论 |
| `moschytz1999tapering.pdf` | Low-sensitivity, low-power active-RC allpole filters using impedance tapering；Moschytz, G.S.；1999；IEEE Transactions on Circuits and Systems II: Analog and Digital Signal Processing | [DOI](https://doi.org/10.1109/82.782042) | 直取受限；需机构/浏览器或代下 | N1/N3：阻抗渐变与灵敏度；核对可制造设计族及既有权衡 |
| `smither1982commonmode.pdf` | Common mode interference reduction in seismic recording；Smither, Miles A. and Pater, Arnold；1982；Geophysics | [DOI](https://doi.org/10.1190/1.1441316) | 直取受限；需机构/浏览器或代下 | 共模不平衡建模近缘；目前仅摘要，必须补全文 |
| `wang2017rcladder.pdf` | Realization of a transfer function as a passive two‐port RC ladder network with a specified gain；Wang, Kai and Chen, Michael Z. Q. and Chen, Guanrong；2017；International Journal of Circuit Theory and Applications | [DOI](https://doi.org/10.1002/cta.2328) | 直取受限；需机构/浏览器或代下 | N1：指定增益的 RC 梯形实现；最近直接相关的综合论文，全文逐式划界 |
| `weinberg1962synthesis.pdf` | Network Analysis and Synthesis；Weinberg, Louis；1962；McGraw-Hill | [入口](https://archive.org/details/networkanalysiss0000wein) | 未有全文；本轮未逐条尝试 | N1：网络综合章节/RC 两端口与实现非唯一性背景，优先相关章节 |
| `whitlock1995balanced.pdf` | Balanced Lines in Audio Systems: Fact, Fiction, and Transformers；Whitlock, Bill；1995；Journal of the Audio Engineering Society | [入口](https://aes.org/publications/elibrary-page/?id=7944) | 直取受限；需机构/浏览器或代下 | 源端失衡和 Zcm 基线；2004 笔记指向的上游正文 |

## 第二批 P1：源端误差、经典工具与工业近缘

| key / 建议文件名 | 完整题录 | DOI / 获取入口 | 当前状态 | 获取用途 |
| --- | --- | --- | --- | --- |
| `adi_difffilters.pdf` | Understanding and Designing Differential Filters for Communications Systems；Chen, Mercy；2016；Analog Devices Technical Article | [入口](https://www.analog.com/en/resources/technical-articles/understanding-and-designing-differential-filters-for-communications-systems.html) | 直取受限；需机构/浏览器或代下 | N1/源端误差/理论背景补查 |
| `adi_emifilter.pdf` | ``Gettin' In Tune'' with the EMI Filter；Smith, Marc；2025；Analog Devices Technical Article | [入口](https://www.analog.com/en/resources/technical-articles/gettin-in-tune-emi-filter.html) | 未有全文；本轮未逐条尝试 | N1/源端误差/理论背景补查 |
| `adi_sd_driver.pdf` | Maximize the Performance of Your Sigma-Delta ADC Driver；；；Analog Dialogue, Analog Devices | [入口](https://www.analog.com/en/resources/analog-dialogue/articles/maximize-the-performance-of-your-sigma-delta-adc-driver.html) | 未有全文；本轮未逐条尝试 | N1/源端误差/理论背景补查 |
| `bell1978longitudinal.pdf` | Steady-State Response of a Well-Balanced Wire Pair to Distributed Interference；Bell, W. N.；1978；Bell System Technical Journal | [DOI](https://doi.org/10.1002/j.1538-7305.1978.tb00600.x) | 未有全文；本轮未逐条尝试 | N1/源端误差/理论背景补查 |
| `bode1945network.pdf` | Network Analysis and Feedback Amplifier Design；Bode, H. W.；1945；D. Van Nostrand | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `breems2023ctsd.pdf` | High-Speed and High-Performance Continuous-Time ADCs for Automotive Receivers；Breems, Lucien J. and Bolatkale, Muhammed and Liu, Qilong and Cenci, Pierluigi；2023；IEEE Open Journal of the Solid-State Circuits Society | [DOI](https://doi.org/10.1109/OJSSCS.2023.3317817) | 直取受限；需机构/浏览器或代下 | N1/源端误差/理论背景补查 |
| `breems_book_filternonid.pdf` | Filter Nonidealities in Continuous-Time σΔ Modulators；{(作者待补)}；2004；Springer Series in Advanced Microelectronics | [DOI](https://doi.org/10.1007/3-540-28473-7_5) | 直取受限；需机构/浏览器或代下 | N1/源端误差/理论背景补查 |
| `dimopoulos2009lowsens.pdf` | Synthesis of Low-Sensitivity Analog Filters；Dimopoulos, H. J. and Constantinides, A. G.；2009；Continuous-Time Active Filter Design | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `fujishiro2017bartlett.pdf` | Expansion of Bartlett's Bisection Theorem Based on Group Theory；Fujishiro, I. and Yamamoto, K.；2017； | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `gervasoni2017switchedratio.pdf` | Switched ratiometric lock-in amplifier enabling sub-ppm measurements in a wide frequency range；Gervasoni, G. and Carminati, M. and Ferrari, G.；2017；Review of Scientific Instruments | [DOI](https://doi.org/10.1063/1.4996423) | 直取受限；需机构/浏览器或代下 | I3直接近缘：双ADC交替采集与比率消漂；需补正文逐式划界 |
| `gregorian1986mos.pdf` | Analog MOS Integrated Circuits for Signal Processing；Gregorian, R. and Temes, G. C.；1986；Wiley | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `kincl2013testfrequency.pdf` | Test Frequency Selection Using Particle Swarm Optimization；Kincl, Zdenek and Kolka, Zdenek；2013；Advances in Electrical and Electronic Engineering | [DOI](https://doi.org/10.15598/aeee.v11i6.912) | 直取受限；需机构/浏览器或代下 | I5直接近缘：模拟active-RC多频诊断/选频；需可解析全文 |
| `magerlein1975tra.pdf` | Digitally Programmable Ratio Transformer Bridge；Magerlein, J.；1975； | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `muncy1995noise.pdf` | Noise Susceptibility in Analog and Digital Signal Processing Systems；Muncy, N. A.；1995；Journal of the Audio Engineering Society | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `pallas1993book.pdf` | Sensors and Signal Conditioning；Pallas-Areny, Ramon and G. Webster, John；1993； | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |
| `rogillio2007aliasing.pdf` | Understanding the Aliasing Effects of Delta-Sigma Analog-to-Digital Converters；Rogillio, D.；2007；OSTI | [入口](https://www.osti.gov/servlets/purl/1137235) | 本轮直取失败；需重试或代下 | N1/源端误差/理论背景补查 |
| `wenner1912guard.pdf` | A Principle Governing the Distribution of Current in Networks；Wenner, F.；1912； | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | N1/源端误差/理论背景补查 |

## 可选 P2：原库其他缺件，不阻塞当前 N1

| key / 建议文件名 | 完整题录 | DOI / 获取入口 | 当前状态 | 获取用途 |
| --- | --- | --- | --- | --- |
| `adi_ctsd_part3.pdf` | CTSD Precision ADCs — Part 3: Inherent Alias Rejection；；；Analog Dialogue, Analog Devices | [入口](https://www.analog.com/en/resources/analog-dialogue/articles/ctsd-precision-adcs-part-3.html) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `augustin2018scarfed.pdf` | Health monitoring of scarfed CFRP joints under cyclic loading via electrical resistance measurements using CNT modified adhesive films；Augustin, T. and Karsten, J. and K{"o}tter, B. and Fiedler, B.；2018；Composites Part A: Applied Science and Manufacturing | [DOI](https://doi.org/10.1016/j.compositesa.2017.11.015) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `bartlett1930bisection.pdf` | The Theory of Electrical Artificial Lines and Filters；Bartlett, A. C.；1930；Chapman & Hall | [入口](https://archive.org/details/dli.ernet.206148) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `brown2003scin.pdf` | Common-Mode to Differential-Mode Conversion in Shielded Twisted-Pair Cables (Shield-Current-Induced Noise)；Brown, Jim and Whitlock, Bill；2003；AES 114th Convention Preprint 5747, Amsterdam, March 2003 | [入口](https://aes.org/publications/elibrary-page/?id=12594) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `catania2022.pdf` | A 150 mV, Sub-1 nW, 0.75%-Full-Scale INL Delta-Sigma ADC for Power-Autonomous Sensor Nodes；Catania, A. and Ria, A. and Manfredini, G. and Dei, M. and Piotto, M. and Bruschi, P.；2022；ESSCIRC 2022- IEEE 48th European Solid State Circuits Conference (ESSCIRC) | [DOI](https://doi.org/10.1109/esscirc55480.2022.9911235) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `chen2022n.pdf` | An Energy-Efficient Readout Circuit Based on Incremental Delta-Sigma ADC with Decimation Filter for CMOS Image Sensors；Chen, Junsheng and Meng, Lingxin and Zhao, Menglian and Tan, Zhichao；2022；2022 IEEE Asia Pacific Conference on Circuits and Systems (APCCAS) | [DOI](https://doi.org/10.1109/apccas55924.2022.10090386) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `couriol2021.pdf` | A 12-pA Resolution Sigma Delta ADC Topology for Chemiresistive Sensor-Based Applications；Couriol, Matthieu and Giacomin, Edouard and Gaillardon, Pierre-Emmanuel；2021；2021 IFIP/IEEE 29th International Conference on Very Large Scale Integration (VLSI-SoC) | [DOI](https://doi.org/10.1109/vlsi-soc53125.2021.9606996) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `denisenko2022notch.pdf` | Notch filter on differential difference operational amplifier；Denisenko, D. Yu. and Prokopenko, N. N. and Ivanov, Yu. I. and Butyrlagin, N. V.；2022；Journal of Physics: Conference Series | [DOI](https://doi.org/10.1088/1742-6596/2373/7/072034) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `denisenko2024scfilter.pdf` | Discrete-Analog Filters on Switchable Capacitors with a Summator of Input and Output Signals on a Differential Difference Operational Amplifier；Denisenko, Darya and Titov, Alexey and Prokopenko, Nikolay and Butyrlagin, Nikolay；2024；2024 IEEE Ural-Siberian Conference on Biomedical Engineering, Radioelectronics and Information Technology (USBEREIT) | [DOI](https://doi.org/10.1109/USBEREIT61901.2024.10584055) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `dong2024.pdf` | High performing piezoresistive MoS2/epoxy strain sensors for structural health monitoring；Dong, Ming and Bilotti, Emiliano and Zhang, Han and Boland, Conor S. and Papageorgiou, Dimitrios G.；2024；Polymer | [DOI](https://doi.org/10.1016/j.polymer.2024.127449) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `fano1950matching.pdf` | Theoretical Limitations on the Broadband Matching of Arbitrary Impedances；Fano, R. M.；1950；Journal of the Franklin Institute | [DOI](https://doi.org/10.1016/0016-0032(50)90006-8) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `fayed2010commonmode.pdf` | System and Method for Common Mode Translation；Fayed, Ayman A. and Byrd, Russell and Haroun, Baher；2010；US Patent 7,796,066 B2, Texas Instruments Inc. | [入口](https://patents.google.com/patent/US7796066B2/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `fu2022.pdf` | Insight into dynamic compressive response of carbon nanotube/carbon fiber-reinforced concrete；Fu, Qiang and Zhou, Zhiming and Wang, Zhenhua and Huang, Jie and Niu, Ditao；2022；Cement and Concrete Composites | [DOI](https://doi.org/10.1016/j.cemconcomp.2022.104471) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `gamry_potentiostat_specs.pdf` | Understanding the Specifications of your Potentiostat；{Gamry Instruments}；2015；Gamry Instruments Application Note --- Instrumentation | [入口](https://www.gamry.com/application-notes/instrumentation/understanding-specs-of-potentiostat) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `hagerup2002ltcc.pdf` | High Speed Differential Attenuator Using a Low Temperature Co-Fired Ceramic Substrate；Hagerup, William A.；2002；US Patent 6,373,348 B1, Tektronix Inc. | [入口](https://patents.google.com/patent/US6373348B1/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `hague1971bridges.pdf` | Alternating Current Bridge Methods: For the Measurement of Inductance, Capacitance, and Effective Resistance at Low and Telephonic Frequencies；Hague, Bernard and Foord, T. R.；1971；Sir Isaac Pitman & Sons | [入口](https://archive.org/details/alternatingcurre0000hagu) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `hioki_lcr_principles.pdf` | LCR Meter Measurement Principles；{Hioki E.E. Corporation}；；Hioki Learning Center（在线技术讲座） | [入口](https://www.hioki.com/us-en/learning/usage/lcr-meters_1.html) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `ieee820.pdf` | IEEE Standard Telephone Loop Performance Characteristics (IEEE Std 820)；；；IEEE Standard | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `inose1963a.pdf` | A unity bit coding method by negative feedback；Inose, H. and Yasuda, Y.；1963；Proceedings of the IEEE | [DOI](https://doi.org/10.1109/proc.1963.2622) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `kellogg1980wideband.pdf` | Wideband Instrumentation Amplifier with High Common Mode Rejection；Kellogg, James R.；1980；US Patent 4,206,416, Tektronix Inc. | [入口](https://patents.google.com/patent/US4206416A/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `kim2024.pdf` | A Precision Low-Noise Sensor Readout System With BJT-Input-Based Amplifier and High-Input-Impedance Delta–Sigma ADC；Kim, Hyungseup and Son, Hyeoktae and Shin, Hyun-Jin and Kim, Choul-Young and Lee, Hi-Deok and Ko, Hyoungho；2024；IEEE Sensors Letters | [DOI](https://doi.org/10.1109/lsens.2024.3433584) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `konno2023.pdf` | 1-b Delta-Sigma ADC-Based Power Side-Channel Attack Detection Sensor；Konno, Shota and Golder, Anupam and Raychowdhury, Arijit；2023；IEEE Sensors Letters | [DOI](https://doi.org/10.1109/lsens.2023.3259301) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `link1998differential.pdf` | Differential Attenuator Common Mode Rejection Correction Circuit；Link, Garry N. and Andrews, Roland E.；1998；US Patent 5,796,308, Tektronix Inc. | [入口](https://patents.google.com/patent/US5796308A/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `lozada2025.pdf` | Continuous-Time Delta-Sigma Modulator with SAR-Assisted Digital Noise Coupling；Lozada, Kent Edrian and Jang, II-Hoon and Kim, Ye-Dam and Ryu, Seung-Tak；2025；2025 IEEE Custom Integrated Circuits Conference (CICC) | [DOI](https://doi.org/10.1109/cicc63670.2025.10983245) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `maehata2022ideband.pdf` | Wideband 1-Bit Bandpass Delta Sigma Modulator Using Elliptic Filter in Noise Transfer Function；Maehata, Takashi and Suematsu, Noriharu；2022；IEEE Access | [DOI](https://doi.org/10.1109/access.2022.3196380) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `martmin2006.pdf` | A Method of Synchronous Sampling in Multifrequency Bioimpedance Measurements；Mart Min；2006；2006 IEEE Instrumentation and Measurement Technology Conference Proceedings | [DOI](https://doi.org/10.1109/imtc.2006.235038) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `mctigue2005probe.pdf` | Differential Voltage Probe；McTigue, Michael T. and Rush, Kenneth and Kimura, Bob and Lujan, Michael J.；2005；US Patent 6,856,126 B2, Agilent Technologies Inc. | [入口](https://patents.google.com/patent/US6856126B2/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `mounika2023.pdf` | A 1.4mW Sigma Delta ADC with Configurable Filter for Sensor Applications；Mounika, Phanidarapu and Pu, Young Gun and Lee, Kang-Yoon；2023；2023 Fourteenth International Conference on Ubiquitous and Future Networks (ICUFN) | [DOI](https://doi.org/10.1109/icufn57995.2023.10200609) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `naderi2014sampling.pdf` | Systems and Methods for Sampling in an Input Network of a Delta-Sigma Modulator；Naderi, Ali；2014；US Patent 8,907,829 B1, Cirrus Logic Inc. | [入口](https://patents.google.com/patent/US8907829B1/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `nbs_precision_handbook.pdf` | Precision Measurement and Calibration: Electricity and Electronics；{National Bureau of Standards}；1962；NBS Handbooks | [入口](https://archive.org/details/precisionmeasure771boot) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `nie2016matching.pdf` | Matching Networks for Broadband Multiport Radio-Frequency Systems: Theory, Analysis, and Design；Nie, D.；2016；University of Notre Dame | 题录/入口需先核对 | 题录/入口待核；暂勿盲目代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `norsworthy1996deltasi.pdf` | Delta-Sigma Data Converters；Norsworthy, Steven R. and Schreier, Richard and Temes, Gabor C.；1996； | [DOI](https://doi.org/10.1109/9780470544358) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `patent_ctsd_lpf.pdf` | Continuous-Time Sigma-Delta ADC with Embedded Low-Pass Filter；；；US Patent App. US2012/0139764A1 | [入口](https://patents.google.com/patent/US20120139764A1/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `patent_kickback.pdf` | Reducing the Effect of Non-Linear Kick-Back in Switched Capacitor Networks；；；Patent WO2013/074188A1 | [入口](https://patents.google.com/patent/WO2013074188A1/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `pimsut2024four.pdf` | Four Terminal Pair Impedance Bridge Based on Two Pulse-Driven Josephson Arrays and a Graphene Quantum Hall System；Pimsut, Yaowaret；2024；Technische Universit{\"a}t Braunschweig | [DOI](https://doi.org/10.24355/dbbs.084-202409200928-0) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `pliquett2011ront.pdf` | Front end with offset-free symmetrical current source optimized for time domain impedance spectroscopy；Pliquett, Uwe and Schönfeldt, Markus and Barthel, Andreas and Frense, Dieter and Nacke, Thomas and Beckmann, Dieter；2011；Physiological Measurement | [DOI](https://doi.org/10.1088/0967-3334/32/7/s15) | 内容错配；需补正确目标全文 | P2 仪器旁系；原同名文件为错误论文，需正确原文，切勿据文件存在判已到货 |
| `pollock2007differential.pdf` | Differential Termination and Attenuator Network for a Measurement Probe；Pollock, Ira G. and Van Epps, Richard A.；2007；US Patent 7,164,995 B2, Tektronix Inc. | [入口](https://patents.google.com/patent/US7164995B2/en) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `preto2025.pdf` | Nanocomposite sensors with indium tin oxide nanowires in a polyvinyl butyral matrix for crack detection in structural health monitoring；Preto, Eduardo and Ambrozini, Beatriz and da Silva, Samuel and Orlandi, Marcelo Ornaghi；2025；Structural Health Monitoring | [DOI](https://doi.org/10.1177/14759217251322998) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `qiu2024.pdf` | Monitoring damage of concrete beams via self-sensing cement mortar coating with carbon nanotube-nano carbon black composite fillers；Qiu, Liangsheng and Li, Linwei and Ashour, Ashraf and Ding, Siqi and Han, Baoguo；2024；Journal of Intelligent Material Systems and Structures | [DOI](https://doi.org/10.1177/1045389x231221129) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `rajalekshmi2024.pdf` | Graphene based piezoresistive pressure sensor for structural health monitoring；Rajalekshmi, Tr and Das, Rinku Rani and James, Alex；2024；2024 IEEE Applied Sensing Conference (APSCON) | [DOI](https://doi.org/10.1109/apscon60364.2024.10465920) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `shlivinski2018beyond.pdf` | Beyond the Bode-Fano Bound: Wideband Impedance Matching for Short Pulses Using Temporal Switching of Transmission-Line Parameters；Shlivinski, A. and Hadad, Y.；2018；Physical Review Letters | [DOI](https://doi.org/10.1103/PhysRevLett.121.204301) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `singh2026.pdf` | Piezoresistive strain monitoring sensors for structural health monitoring of fibre-reinforced composites；Singh, Sudhanshu and Kamble, Zunjarrao；2026；Journal of Materials Science | [DOI](https://doi.org/10.1007/s10853-025-12088-7) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `solecka2025etal.pdf` | Metal powder testing with the employment of electrical impedance spectroscopy；Solecka, Barbara and Tytko, Grzegorz and Michczyński, Adam and Feng, Bo and Xie, Yuedong；2025；Measurement | [DOI](https://doi.org/10.1016/j.measurement.2025.118253) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `styles2008filters.pdf` | Selection of Optimal Filters for Multispectral Imaging；Styles, Iain B.；2008；Applied Optics | [DOI](https://doi.org/10.1364/AO.47.005585) | 未有全文；本轮未逐条尝试 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `sussmanfort2004nonfoster.pdf` | Matching Network Design Using Non-Foster Impedances；Sussman-Fort, Stephen E.；2006；International Journal of RF and Microwave Computer-Aided Engineering | [DOI](https://doi.org/10.1002/mmce.20118) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `vairagade2025.pdf` | Artificial intelligence-driven predictive modeling of multi-functional carbon nanotube infused smart cement for structural reinforcement and real-time damage sensing；Vairagade, Vikrant S.；2025；Frontiers of Structural and Civil Engineering | [DOI](https://doi.org/10.1007/s11709-025-1219-y) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `vittoz2003frequency.pdf` | Frequency--Dynamic Range--Power；Vittoz, E. A. and Tsividis, Y. P.；2003；Trade-Offs in Analog Circuit Design | [DOI](https://doi.org/10.1007/0-306-47673-8_10) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `whitlock2025audiotransformers.pdf` | Audio Transformers；Whitlock, Bill；2025；Handbook for Sound Engineers | [DOI](https://doi.org/10.4324/9781003430292-19) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `wolfer2023.pdf` | Performance and Stability Characterization of a 3rd Order Continuous-Time Delta-Sigma Modulator with Active Time-Constant Tuning；Wolfer, Tobias and Hennig, Eckhard；2023；2023 21st IEEE Interregional NEWCAS Conference (NEWCAS) | [DOI](https://doi.org/10.1109/newcas57931.2023.10198152) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `x2018olerance.pdf` | Tolerance Analysis of a Bandpass Filter；\{(作者待补)\}；2018；Tolerance Analysis of Electronic Circuits Using MATHCAD | [DOI](https://doi.org/10.1201/9781315215402-22) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `xiong2022.pdf` | A Continuous-Time Sigma-Delta Modulator With Continuous-Time Delay-Based Integrator；Xiong, Jiu and Liu, Jin and Lee, Hoi；2022；IEEE Transactions on Circuits and Systems II: Express Briefs | [DOI](https://doi.org/10.1109/tcsii.2021.3127024) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `zanganeh2013.pdf` | A new high output impedance wideband AC current source with high current swing authority for electrical impedance tomography applications；Zanganeh, Mehran；2013；International Journal of Computing and Network Technology | [DOI](https://doi.org/10.12785/ijcnt/010305) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |
| `zhang2022.pdf` | A High Resolution Chemical Sensing Front-end with Integrated Sigma Delta Quantisation；Zhang, Xiuli and Ma, Jinge and Hu, Yuanqi；2022；2022 IEEE International Symposium on Circuits and Systems (ISCAS) | [DOI](https://doi.org/10.1109/iscas48785.2022.9937843) | 直取受限；需机构/浏览器或代下 | 次级背景或原库补件；不阻塞当前 N1，按需获取 |

## 已补齐，不用再代下

| key | 本轮核验 | 正文状态 |
| --- | --- | --- |
| `razbin2025` | PDF 可解析；15 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `kerr1993limits` | PDF 可解析；24 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `murmann2012energy` | PDF 可解析；56 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `nbs1968sp300v3` | PDF 可解析；512 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `nbs_sp300v4` | PDF 可解析；464 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `kundert2006scfilters` | PDF 可解析；25 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `xin2022systemratio` | PDF 可解析；13 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |
| `tadeusiewicz2017diagnostictests` | PDF 可解析；10 物理页；前置题名/作者或出版信息匹配 | 未精读，不计阴性证据 |

## 交接注意

- `pliquett2011ront` 虽有同名文件，内容是其他论文，仍列缺件；保留旧文件，不让下载人员重复交付该错误文件。
- NBS SP300 v3（1968，低频电学）与 v4（1970，RF 电学）已从 NIST 补齐；色度卷 `nimeroff1972recision` 不再冒充电学来源。目标篇仍待在新卷定位。
- `lyu2018ultiobje2` 是同文双 DOI 别名，已退出正式 bib，统一用 `lyu2018ultiobje`，不用再下两份。
- `chen2026dsmod` 是 T3 中文条目，已退出正式 bib，已有 PDF/笔记保留，不再列代下载任务。
- 题录/入口待核项先核来源，不要仅凭题名去购买错误文章；特别是原库早期“题名/作者待核”条目。
- 本清单基于实际文件名库存和已知异常；“已有全文”不等于所有内容、所有引文已经复核。下载人员回货后按 key 归档，再做逐篇身份和正文核验。

本次扩展考察新增代下重点：`gervasoni2017switchedratio.pdf`（I3 双 ADC 比率消漂近缘，出版方/作者存档 403）；`kincl2013testfrequency.pdf`（I5 模拟 active-RC 选频近缘，SSL 失败/镜像返回非 PDF）。两项均 P1，不影响原 P0 优先序；失败不等于付费。
