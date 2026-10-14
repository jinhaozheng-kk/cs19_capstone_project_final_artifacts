# CS19 无障碍与可用性评分项目

本仓库是 CS19 Capstone 项目的最终交付包，围绕 AAMI 保险网站用户测试数据，探索如何结合问卷、自述反馈、LLM 提取的摩擦证据和转录片段，生成可解释的无障碍与可用性评分，并评估测试反馈本身的证据质量。

项目的核心实现是基于 Jupyter Notebook 的 Model C/C3 分析原型，包含 Proposal 1 评分规则优化、Proposal 2 时间信号修正、人工复核验证和独立的 Tester Quality Rating。仓库还提供数据字典、结果文件、展示材料和交接文档，便于复查当前实现与后续迭代。

> **项目定位：**这是供分析、验证和交接使用的研究型 MVP，不是已部署的生产评分服务，也不是可直接接入客户系统的产品。

## 目录

- [项目目标与评分输出](#项目目标与评分输出)
- [研究背景与方案选择](#研究背景与方案选择)
- [评分流程与关键约束](#评分流程与关键约束)
- [仓库结构](#仓库结构)
- [数据来源与覆盖](#数据来源与覆盖)
- [Notebook 工作流](#notebook-工作流)
- [环境与运行方法](#环境与运行方法)
- [主要结果与验证](#主要结果与验证)
- [解释结果时的限制](#解释结果时的限制)
- [数据字典与交接材料](#数据字典与交接材料)

## 项目目标与评分输出

项目的最终工作围绕三个目标展开：以 Model C/C3 为基础处理网站无障碍与可用性评分；用 Proposal 1 和 Proposal 2 改进评分规则；另行估计测试反馈的完整度与证据质量，支持人工复核排序。

| 输出 | 含义 | 主要实现 |
| --- | --- | --- |
| 无障碍评分（Accessibility，ACC） | 依据辅助技术（AT）与理解/认知（COMP）相关摩擦证据，调整问卷分数 | Notebook 01 的 L1/L2 评分流 |
| 可用性评分（Usability，USA） | 依据可用性（USA）摩擦、期望达成情况及时间信号，调整问卷分数 | Notebook 01 的 L1/L3，加上 Notebook 02 的 L3.8 |
| 测试者质量评分（Tester Quality，TQ） | 评估反馈深度、任务覆盖、证据一致性和参与证据是否充分 | Notebook 04；独立于 ACC/USA |

评分以问卷中的任务自评为起点，将 1–5 分转换为 0–100 的分数上限，再按参与者、任务和证据匹配情况应用规则。LLM 洞察文件提供摩擦类别、严重度、置信度和证据文本；转录分段和任务耗时则用于时间信号与人工复核。

## 研究背景与方案选择

毕业设计报告将项目问题概括为：问卷自评代表参与者本人对体验的判断，应当被保留；但单独依赖自评，可能无法呈现任务中的阻断、反复操作、困惑或异常耗时。项目尝试把问卷与测试中可观察到的证据结合起来，让分数调整更可解释、可检查，同时避免自动化判断取代参与者声音或专家判断。

项目讨论了四类评分思路：

| 模型 | 核心做法 | 在项目中的作用与边界 |
| --- | --- | --- |
| Model A：问卷平均 | 直接汇总参与者自评 | 作为基准；简单透明，但可能让正向自评分掩盖已确认的严重障碍 |
| Model B：分析师辅助 | 以问卷为基准，由分析师/专家对严重情况作判断或修正 | 作为人工流程参照；结构化和复现能力有限 |
| Model C/C3：问卷分数上限 | 从自评分出发，根据任务证据向下调整 | 被选为当前 MVP 基础；保留自评锚点，规则较易追踪，但原始硬上限可能对中度问题过重 |
| Model D：证据优先协调 | 根据观察证据生成分数，再与自评协调汇总 | 作为比较和未来设计参考；当前样本和证据覆盖下，参与者级聚合可能稀释关键任务的阻断问题，且更难验证 |

选择 Model C 并不表示它已经被证明在所有数据集上优于其他模型，而是基于本项目当前的数据完整度、可解释性要求、阻断问题处理和交付周期，认为它更适合作为可审计的优化起点。项目报告中的理论背景还包括无障碍与可用性评价、自评量表局限、多模态证据融合，以及可解释和负责任 AI；本仓库的 README 侧重实现与交付，不替代完整学术论证和参考文献。

报告中的基线比较使用 67 条记录、17 名参与者和 4 个任务；后续优化和 Proposal 2 使用 136 条 Model C 记录。两组数字对应不同分析阶段和样本范围，不宜直接当作同一口径的模型性能比较。

## 评分流程与关键约束

### Proposal 1：Model C/C3 规则优化

Notebook 01 生成任务级 ACC 和 USA 分数及解释字段，并汇总任务、群组和项目结果。主要处理层如下：

- **L1 基础上限与辅助技术硬规则：**将问卷 1–5 分乘以 20；严重/阻断级辅助技术问题可将分数置为 0；高严重度问题 1 次上限为 20，2 次及以上上限为 10。触发摩擦规则的置信度阈值为 0.70。
- **L2 无障碍流：**中度辅助技术摩擦使用基础扣分 20、下限 30 的渐进规则。理解/认知摩擦使用群组加权上限和扣分：高/严重问题上限 40；中度问题基础扣分 15、下限 50；3 个及以上中度问题上限 40；低度问题上限 70，3 个及以上低度问题上限 60。超过预期时，理解/认知流另有 45 分下限。
- **L3 可用性流：**严重问题或 3 个及以上高严重度问题上限 50；高加中度问题上限 60；中加低度问题使用基础扣分 12、下限 75 的渐进规则；3 个及以上中度问题使用基础扣分 25、下限 70；3 个及以上低度问题上限 80。未达到预期乘以 0.80，远低于预期乘以 0.60；多个规则同时适用时采用最严格上限。
- **L1.5 正向证据保护：**在 L2/L3 之后，对满足条件的高自评、达到预期且没有高严重度问题的记录应用正向分数下限。
- **汇总和解释：**保留逐行规则结果、分数变化解释、任务/群组/项目级汇总，以及部分规则的审计表。

实现中包含置信度阈值和群组权重。Notebook 中列出的理解/认知群组权重为 ESL/DF/ND 1.0、BL/LV 0.5、OL 0.6、General 0.4。具体分数应以 Notebook 中实际匹配到的证据及生成的审计输出为准。

Proposal 1 对适用的中度摩擦采用置信度比例扣分：置信度低于 0.70 时不触发；达到阈值后，`confidence_weight = (confidence - 0.70) / 0.30`，扣分为四舍五入后的 `base_penalty × confidence_weight`，最终分数不低于该规则下限。也就是说，刚超过阈值的证据只带来较小扣分，置信度越高扣分越接近规则设定的完整基础扣分。严重/阻断、高严重度及若干特定叠加规则仍保留硬上限，不做置信度渐进化。

### Proposal 2：参与者归一化时间调节

Notebook 02 先用参与者总实际耗时与建议耗时的比例估计个人速度因子，并将其限制在 0.7–1.5，再把任务耗时除以该因子，与该任务的归一化中位耗时比较。归一化时间比达到 2×、3×、4×时，L3 上限分别为 50、40、25；低于 2×不加时间上限。该层只调节 USA 的 L3 分数：不会改写 L1/L2、ACC 或 Proposal 1 的规则；也不会提高分数。重试或表达困惑的文字仅作为解释背景，不是直接扣分规则。

### 人工复核与 Tester Quality

Notebook 03 建立并评估人工复核样本，对原始问卷分数、Proposal 2 前的 Model C 分数和 Proposal 2 后的分数进行比较。该样本用于验证和审计，不是正式标签库或官方真实值。

Notebook 04 生成独立的 TQ 分数，考察反馈深度（35%）、任务覆盖（25%）、证据一致性（25%）和参与/投入证据（15%）；缺失维度会记录下来，并对可用维度的权重重新归一化。方法说明强调不因残障、辅助技术使用、ESL 身份或完成较慢而直接降低评分；TQ 用于质量监测和复核排序，不能乘入或替代 ACC/USA。

## 仓库结构

```text
.
├── README.md
├── CS19-1_Final_Demo_Slide.pdf
├── SMP_Model_C_Scoring_Documentation_Handover_Pack.pdf
├── final_data_dictionary_package/
│   ├── Final_Data_Dictionary_and_Master_File_Inventory.md
│   ├── final_data_dictionary.csv
│   ├── mapping_rules.csv
│   ├── master_file_inventory.csv
│   ├── observed_raw_field_profile.csv
│   └── output_schema_documentation.csv
└── cs19_capstone_data&notebooks_package/
    ├── 01_run_model_c_proposal1.ipynb
    ├── 02_proposal2_time_integration.ipynb
    ├── 03_manual_review_validation.ipynb
    ├── 04_tester_quality_rating.ipynb
    ├── 05_presentation_assets.ipynb
    ├── 06_proposal2_rollup_outputs.ipynb
    ├── README_How_To_Run.md
    ├── 原始问卷、调查导出、洞察表和任务/时间数据
    ├── proposal2_segments/       # 21 个参与者转录分段文件
    ├── scripts/                  # 人工复核和 TQ 辅助脚本
    └── outputs/                  # 已生成的评分、验证、汇总和展示材料
```

`cs19_capstone_data&notebooks_package/` 是主要分析目录。这里包含原始输入、已生成的中间结果和最终结果，因此仓库同时是可审阅的结果包，不只是代码仓库。数据文件的字段、映射和用途见数据字典目录。

## 数据来源与覆盖

毕业设计报告说明，原始测试数据由 See Me Please 提供，团队负责整理、映射和分析，没有在本项目中另行招募受试者。研究设计涉及问卷、自述/转录证据、LLM 洞察、任务及群组映射和建议任务时长等数据流。当前仓库保存的是可供 Notebook 使用的 AAMI 数据导出、LLM 洞察工作簿、任务/时间映射、21 份转录分段 CSV，以及经处理的输出；原始视频、音频和报告中提到的原始逐词时间戳 Transcript JSON 不在当前仓库的目录清单中。Notebook 使用预先整理的洞察和分段数据，不会在执行时调用 Anthropic Claude API 重新生成洞察。

报告以 11 个官方任务作为规范化任务标识的设计目标，但实际可用的任务/转录/时间匹配并不完整。Proposal 2 的最终结果为 136 条 Model C 记录中 95 条匹配到时间证据；未匹配记录通过诊断文件保留，不应把未匹配解释为“没有摩擦”。原始文件、清洗后数据和输出之间的键也不完全统一，参与者/任务匹配应结合数据字典和未匹配诊断审阅。

## Notebook 工作流

| 顺序 | Notebook | 职责 | 主要产物/用途 |
| --- | --- | --- | --- |
| 01 | `01_run_model_c_proposal1.ipynb` | 清理和匹配问卷与洞察证据；执行 L1、L2、L3、L1.5；生成解释和汇总 | `proposal1_rows.csv`、`proposal1_df_insights.csv`、任务/群组汇总、项目摘要和 Excel 结果 |
| 02 | `02_proposal2_time_integration.ipynb` | 计算/整合参与者归一化耗时信号，应用 L3.8，并记录匹配与分数变化 | `proposal2_integrated_l3_time_score.csv`、时间审计日志、整合摘要和未匹配诊断 |
| 03 | `03_manual_review_validation.ipynb` | 整理人工复核案例、评分规则和模型对照验证 | `outputs/manual_review_outputs/` 下的案例、验证摘要、误差明细和质量检查 |
| 04 | `04_tester_quality_rating.ipynb` | 计算独立 TQ 分数、维度特征、等级和复核标记 | `outputs/tester_quality_outputs/` 下的分数、特征、摘要和质量检查 |
| 05 | `05_presentation_assets.ipynb` | 汇总验证、审计、评分和群组结果，生成图表/展示图 | `outputs/presentation_assets/` 下的 8 个 PNG 文件 |
| 06 | `06_proposal2_rollup_outputs.ipynb` | 对 Proposal 2 整合结果另行计算任务、参与者和项目汇总 | `proposal2_rollup_task.csv`、`proposal2_rollup_participant.csv`、`proposal2_rollup_project.csv` |

建议先按 01 → 02 → 03 → 04 → 05 执行主分析流程。第 06 本是额外的 Proposal 2 汇总步骤，可在 Notebook 02 后单独运行。仓库已包含最终交付时生成的 outputs，因此只查看结果时不必重新运行。

Notebook 06 会从当前目录及其子目录查找 `proposal2_integrated_l3_time_score.csv`，并将汇总写入当前目录的 `outputs/`。从主分析目录运行时，它可能会找到 `outputs/` 中的整合文件；若从仓库根目录打开，请先确认 Notebook 的当前工作目录和目标输出目录。

## 环境与运行方法

建议使用 Python 3 和独立虚拟环境。主要依赖为 `pandas`、`numpy`、`openpyxl`、`sentence-transformers`、`matplotlib`、`nbconvert`、`jupyter` 和 `ipykernel`。Notebook 01 使用 Sentence Transformers 做洞察语义去重，Notebook 05 使用 Matplotlib 生成图表；首次运行可能需要下载语义模型，并需要可用的网络或预先缓存的模型。

在仓库根目录执行：

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install pandas numpy openpyxl sentence-transformers matplotlib nbconvert jupyter ipykernel
python -m ipykernel install --user --name python3 --display-name "Python 3"
```

然后切换至 Notebook 目录并按顺序执行：

```bash
cd "cs19_capstone_data&notebooks_package"

jupyter nbconvert --to notebook --execute --inplace 01_run_model_c_proposal1.ipynb
jupyter nbconvert --to notebook --execute --inplace 02_proposal2_time_integration.ipynb
jupyter nbconvert --to notebook --execute --inplace 03_manual_review_validation.ipynb
jupyter nbconvert --to notebook --execute --inplace 04_tester_quality_rating.ipynb
jupyter nbconvert --to notebook --execute --inplace 05_presentation_assets.ipynb
```

也可以启动 JupyterLab，逐本打开并使用 **Run All Cells**。运行 Notebook 06 前，确认其能找到上一步生成的 `proposal2_integrated_l3_time_score.csv`：

```bash
jupyter nbconvert --to notebook --execute --inplace 06_proposal2_rollup_outputs.ipynb
```

Notebook 主要使用相对路径，并将结果写入 `outputs/`。请从 `cs19_capstone_data&notebooks_package/` 运行主流程，不要把路径改成原开发环境的绝对路径。逐个 Notebook 的额外注意事项见该目录中的 [英文运行指南](cs19_capstone_data%26notebooks_package/README_How_To_Run.md)。

> 执行 `--inplace` 会把新输出和执行状态写回 `.ipynb` 文件。若要保留仓库内的原始 Notebook 状态，建议先复制一份 Notebook 再运行。

## 主要结果与验证

仓库中记录的最终结果包括：

- Proposal 1 项目级无障碍评分为 **50.72**（标准差 31.47），可用性评分为 **60.10**（标准差 12.66）。
- Proposal 2 处理 **136** 条 Model C 记录，其中 **95** 条匹配到时间证据；**14** 条触发归一化时间上限，**12** 条 L3 可用性分数发生变化，没有分数上升。ACC 保持不变。
- 人工复核包含 **18** 个参与者-任务案例，其中 **14** 个有可用于误差比较的人工估分，4 个证据不足。该样本中原始问卷分数 MAE 为 **13.57**，Model C（时间调节前）为 **13.28**，Proposal 2 后为 **19.49**。
- TQ 输出覆盖 **21** 名测试者；现有质量检查记录为 **13/13 项通过**。这些检查说明输出符合预设格式和约束，不代表评分方法已经完成独立科学验证。
- 当前 TQ 汇总文件记录的平均分为 **90.12**：21 人中 18 人被分为 High Quality、3 人为 Good Quality；该分数衡量的是可用证据质量，不是参与者能力，也不证明 ACC/USA 对每个任务都准确。
- Presentation Assets Notebook 生成 8 张展示图；相关图片和评分结果已随仓库提供。

上述数值来自本仓库附带的最终运行摘要和质量检查文件，不是本次重新执行 Notebook 得到的结果。重新运行后，结果可能因依赖版本、模型下载状态或输入文件变化而不同。

## 解释结果时的限制

1. **Proposal 2 不是更准确的既定结论。**在 14 个有效人工估分案例中，时间修正后的 MAE 高于 Proposal 1 前的 Model C。样本很小，只能说明当前样本下的比较结果，不能推断总体性能。
2. **人工复核分数不是官方真实值。**它是基于有限转录证据的审核者估计；样本规模、片段边界和多路音频内容都会限制解释。
3. **耗时是辅助信号。**任务耗时可能受成功但详细的探索、任务边界切分或多路径评估影响。长时间本身不等于失败，也不应直接解释为低质量。
4. **TQ 不是参与者能力分数。**它评估反馈及可用证据，不评价参与者是否“优秀”；不应用它去折减参与者的无障碍体验或 ACC/USA 结果。
5. **参与者和任务映射并非统一模式。**原始文件、模型输出和转录文件使用不同标识字段。数据字典区分原始字段和标准化字段；未匹配诊断应作为结果审阅的一部分。
6. **这是分析原型。**在用于运营或客户决策前，需要扩大并校准人工标注样本、评估映射覆盖和公平性、确认数据治理，并进行独立验证。

## 当前范围与后续工作

当前交付是 Notebook 驱动的分析原型和交接材料，不包含平台部署、生产 API、自动化视频行为识别或持续运行服务。报告也指出，重试/回退行为的分类和捕捉虽被研究，但没有作为独立评分规则正式接入当前评分链；时间修正仍受任务分段、建议时长基线来源和部分匹配覆盖限制。后续工作建议扩大并多样化验证数据、校准任务时长、提升 LLM 洞察与任务映射质量、建立专家标注流程，并在可靠交互日志可用后再评估是否纳入重试信号。所有自动化结果仍应保持可解释并接受人工复核。

## 数据字典与交接材料

`final_data_dictionary_package/` 包含主文件清单、字段定义、原始字段画像、字段映射规则和输出结构说明。建议需要了解列名、记录粒度或参与者/任务关联方式时，从以下文件开始：

- [主文件清单与数据字典说明](final_data_dictionary_package/Final_Data_Dictionary_and_Master_File_Inventory.md)
- `final_data_dictionary.csv`：汇总字段定义和说明。
- `mapping_rules.csv`：不同输入与输出之间的字段/键映射规则。
- `master_file_inventory.csv`：文件级用途和数据层清单。
- `observed_raw_field_profile.csv`：实际观察到的原始字段画像。
- `output_schema_documentation.csv`：生成结果的输出字段结构。

`SMP_Model_C_Scoring_Documentation_Handover_Pack.pdf` 说明评分逻辑、假设、边界、交接检查和后续开发建议；`CS19-1_Final_Demo_Slide.pdf` 概览项目目标、最终状态和交付成果。详细逐步运行说明仍以 Notebook 目录中的英文指南和 Notebook 内说明为准。
