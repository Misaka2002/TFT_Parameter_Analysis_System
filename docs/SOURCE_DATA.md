# 公开示例数据来源

## 数据集与许可

程序内置的三条 TFT 示例曲线取自斯图加特大学 DaRUS 数据仓库的 Figure 1 原始数据目录。数据集名称为 **Replication Data for: High Gain Operational Amplifier Using Enhancement and Depletion Mode a-IGZO TFTs**，DOI 为 [10.18419/DARUS-5121](https://doi.org/10.18419/DARUS-5121)，许可为 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。

依据该许可分发或改编材料时，应注明来源、附上许可链接，并说明是否修改。本项目保留数据仓库提供的原始文本文件和绘图脚本，未修改这些文件。软件对数据所作的分析由本项目完成，不代表原作者认可或背书。

- [DaRUS 数据集页面](https://darus.uni-stuttgart.de/dataset.xhtml?persistentId=doi:10.18419/DARUS-5121)
- [DaRUS API 元数据](https://darus.uni-stuttgart.de/api/datasets/:persistentId/?persistentId=doi:10.18419/DARUS-5121)
- [DaRUS ReadMe.txt，文件 ID 386874](https://darus.uni-stuttgart.de/api/access/datafile/386874)
- [原始曲线 1，文件 ID 386703](https://darus.uni-stuttgart.de/api/access/datafile/386703)
- [原始曲线 2，文件 ID 386708](https://darus.uni-stuttgart.de/api/access/datafile/386708)
- [原始曲线 3，文件 ID 386695](https://darus.uni-stuttgart.de/api/access/datafile/386695)
- [官方 Figure 1 脚本，文件 ID 386714](https://darus.uni-stuttgart.de/api/access/datafile/386714)
- [关联论文 PDF](https://www.pqe.uni-stuttgart.de/documents/Publikationen/2022/High_Gain_Operational_Amplifier_Using_Enhancment_and_Depletion_Mode_a-IGZO_TFTSV2.pdf)

数据集署名作者为 Yannick Schellander、Marius Winter、Ge Ge、Yunyi Ouyang、Simon Obermüller、Patrick Schalberger 和 Norbert Fruehauf。仓库中的五份原始材料按原样保留，程序生成的曲线和参数属于本项目的分析结果。

## 本地文件与完整性

原始材料保存在 `data/raw/DaRUS_5121_Figure1/`。下表中的 MD5 与 DaRUS API 文件清单一致，用于核对下载文件是否完整；MD5 并非安全签名。

| 文件 | DaRUS 文件 ID | 大小（字节） | MD5 |
|---|---:|---:|---|
| `YO10_10um_10um_120nm_1.txt` | 386703 | 3370 | `c377a850fd340ab294a76420c8b69e45` |
| `YO10_10um_10um_120nm_2.txt` | 386708 | 3359 | `aad144ab491119c6fa92b5b4c55eebd6` |
| `YO10_10um_10um_120nm_3.txt` | 386695 | 3394 | `338aaba4bc77970346f5d72af1e7ad1c` |
| `Script.py` | 386714 | 8706 | `5a25cb312999abe79c8668fa7f23b332` |
| `ReadMe.txt` | 386874 | 461 | `5a0db1f47cf2749ccc05186f661de5f1` |

三条曲线文件均为 200 行，两列以制表符分隔，没有表头。第一列依据官方脚本中的变量名 `Ugate` 及论文 Figure 1 的说明识别为栅极电压 `UG`，单位为 V；第二列依据变量名 `Idrain` 和图中纵轴标记识别为漏极电流 `ID`，单位为 A。检查的第一条曲线从 −20.0 V 扫描到 19.8 V，步进为 0.2 V。

## 已有依据的器件与测量条件

论文 Figure 1 将该输入特性标为双栅 a-IGZO TFT，沟道宽度 `W = 10 µm`、沟道长度 `L = 10 µm`，漏极偏置标记为 `UD = 10 V`。文件名中的 `120nm` 是沟道层厚度的名义标记。官方 `Script.py` 按排序后的 YO10 文件列表与厚度数组对应，将第一条 YO10 曲线绘为 `h = 122.6 nm`。名义标记和脚本使用值描述的是同一组样品，不能把 120 nm 或 122.6 nm 当作栅介质厚度。

论文的工艺说明还给出底栅介质结构：175 nm SiN 与 50 nm SiOx 叠层；顶栅隔离层为 130 nm SiOx。官方绘图脚本也采用 `d = 130 nm`，并令相对介电常数 `εr = 4` 来估算单层栅介质电容。因此，130 nm 指顶栅 SiOx 厚度，与 YO10 文件名中的沟道厚度不是同一参数。

## 尚未明确的条件与使用限制

- `εr = 4` 是官方参考脚本的假设值。论文没有说明这是该样品的实测介电常数，因此不能将其写成实验测量结果。
- 数据和图注称器件为双栅 TFT，但现有材料没有明确指出 `UG` 扫描实际连接顶栅还是底栅。论文同时描述底栅介质叠层与 130 nm 顶栅 SiOx，而参考脚本只用单层 130 nm 计算电容。根据现有资料，无法确定 `UG` 对应的电容模型。迁移率计算必须把所用端口和电容模型作为假设明确列出；条件不足时应不计算迁移率。
- 文件名后缀 `_1`、`_2`、`_3` 代表三条曲线，但公开材料未说明它们来自同一器件的重复扫描，还是来自不同器件。不能据此将其当作已确认的独立器件或独立统计重复。
- 随数据保留的 `Script.py` 是来源材料和方法参考，本项目没有执行它。本程序另行实现分析功能，采用区间内的多点最小二乘拟合；参考脚本采用最大斜率处的两点切线法，两种方法的结果不保证一致。

程序所用示例路径、文件哈希、已确认条件及未知事项也保存在 [`data/example_metadata.json`](../data/example_metadata.json)，供界面和导出记录读取。
