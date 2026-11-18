# 生态学与微生物组分析工具库

按科研问题整理的 143 个已有工具和数据资源，配有 6 个经过实际运行的 R/Python 分析示例。每条记录写明适用场景、所需输入、分析产出及原作者入口。[English README](README.md) · [在线检索工具](https://azaleawu.github.io/ecology-analysis-toolkit/browse.html) · [下载后可离线打开的检索页](browse.html)

| 你手里的数据或问题 | 入口与选择 |
| --- | --- |
| ASV 计数表、分类表、样品信息 | [微生物组与群落分析，49 项](catalog/microbiome.tsv)。从 phyloseq 或 mia 组织数据，用 vegan 看群落差异，按实验设计选择 ANCOM-BC2、ALDEx2 或 MaAsLin 3。也涵盖指示种、网络、群落组装和真菌功能类群。 |
| 环境因子、样地重复观测、预测目标 | [生态建模与预测，45 项](catalog/models.tsv)。用 lavaan 或 piecewiseSEM 研究路径，用 glmmTMB 或 mgcv 处理分层或非线性响应，用 XGBoost 或 ranger 预测，再根据外推目标选择站点留出或空间分块。 |
| 样点坐标、遥感栅格、物种记录、性状、野外调查 | [空间与野外生态，49 项](catalog/ecology.tsv)。包括栅格提取、坐标核查、占域模型、物种分布模型、保护规划、时间序列和证据整合。 |

## 从一个真实土壤样例开始

在项目目录中运行以下命令。检索工具只需 Python 3。最后两条命令会用阿塔卡马沙漠土壤的真实 ASV 计数生成样品多样性表、Bray–Curtis 距离表和热图。

```sh
python toolkit.py find 结构方程
python toolkit.py find 差异丰度
python toolkit.py recipes
python -m pip install numpy scipy matplotlib
python toolkit.py run count-table --out results/atacama
```

该例含同一采样点的 5 个文库、128 个 ASV，共 4,261 条去嵌合体后的序列。其余五个示例用模拟数据说明用法，全部可以替换成自己的输入。[真实数据出处](data/README.md) · [六个示例的依赖、输入列及输出](README.md#six-worked-analyses)

| 示例命令名 | 输出能回答什么 |
| --- | --- |
| `count-table` | 每个文库观察到多少 ASV？标准化到相对丰度后，哪些文库的组成更接近？ |
| `community` | 不同生境的独立样地在群落组成上是否有差异？组内离散度如何？ |
| `path-analysis` | 在预先指定的路径模型中，降水和温度经土壤水分关联到呼吸的间接效应有多大？ |
| `boosted-trees` | 用其他站点训练的模型，在整站留出的数据上能否优于训练集均值基线？ |
| `spatial` | WGS84 样点在环境栅格中对应什么值？哪些点位落在空值或覆盖范围之外？ |
| `meta-analysis` | 在统一效应尺度与方向后，不同独立研究的合并效应及异质性有多大？ |

工具目录持续可扩充。使用第三方工具和数据时，请引用对应软件、数据库或论文。仓库中的工作包括工具筛选、分类与文档整理、检索入口和可运行的分析示例。
