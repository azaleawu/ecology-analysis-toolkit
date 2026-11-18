#!/usr/bin/env python3
"""Generate an offline HTML tool directory from the three published TSV catalogues."""
import csv
import html
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    "microbiome": "Microbiome & communities",
    "models": "Statistical modelling & machine learning",
    "ecology": "Spatial & field ecology",
}
# Task synonyms also allow an English catalogue to be searched with Chinese keywords.
SYNONYMS = {
    "Import and organize": "导入 整理 数据结构 丰度表 ASV OTU 数据管理",
    "Inspect composition": "组成 群落组成 相对丰度 堆叠柱状图",
    "Assess contamination": "去污染 污染物 空白 阴性对照 contaminant blank",
    "Compositional transformations": "组成型数据 组成数据 对数比 零值替代 clr ilr",
    "Alpha diversity and coverage": "alpha diversity α多样性 阿尔法多样性 丰富度 稀释曲线 覆盖度",
    "Beta diversity and ordination": "beta diversity β多样性 贝塔多样性 群落距离 排序 pcoa nmds",
    "Differential abundance": "差异丰度 差异类群 差异分析 biomarker",
    "Indicator taxa": "指示种 指示类群",
    "Network inference": "网络 共现网络 关联网络 网络推断 cooccurrence co-occurrence",
    "Network comparison": "网络 共现网络 网络比较",
    "Feature association": "特征关联 比例性 组成数据关联",
    "Phylogenetic ecology": "系统发育 谱系 系统发育多样性",
    "Community assembly": "群落构建 群落组装 群落装配 零模型 null model",
    "Functional potential": "功能预测 功能潜力 扩增子功能预测",
    "Functional traits": "功能性状 功能注释 真菌功能 guild",
    "Taxon sharing and partitioning": "群落共享 共有类群 交集",
    "Source mixtures": "来源追踪 源解析 溯源 source tracking",
    "Multivariate modeling": "多变量建模 多元群落模型",
    "Visualization and reporting": "绘图 可视化 热图 进化树",
    "Functional profiles": "功能谱 通路 功能注释",
    "Structural equation modelling": "结构方程 结构方程模型 路径分析 SEM path analysis structural equation modeling",
    "Causal design": "因果推断 有向无环图 混杂 DAG",
    "Observational comparisons": "观察性研究 倾向评分 匹配 平衡",
    "Mixed-effects models": "混合效应 混合模型 随机效应 层级模型 glmm lmm",
    "Hierarchical Bayesian models": "贝叶斯 层级贝叶斯 mcmc bayes",
    "Nonlinear responses": "非线性响应 非线性 广义加性模型 GAM GAMM",
    "Thresholds and time series": "生态阈值 拐点 突变点 变点 时间序列 breakpoint",
    "Quantile regression": "分位数回归",
    "Event times": "生存分析 事件时间",
    "Temporal models": "时间序列 时序 状态空间模型",
    "Meta-analysis": "整合分析 元分析 荟萃分析 meta analysis",
    "Model diagnostics": "模型诊断 残差 过度离散",
    "Model contrasts": "边际效应 边际均值 模型对比",
    "Bayesian diagnostics": "贝叶斯诊断 后验检验 posterior",
    "Model comparison": "模型比较 交叉验证 loo",
    "Penalized regression": "正则化回归 惩罚回归 lasso ridge",
    "Random forests": "随机森林 rf",
    "Gradient boosting": "梯度提升 梯度提升树 增强树 机器学习 boosting",
    "Machine learning workflows": "机器学习 建模流程",
    "Hyperparameter tuning": "调参 超参数优化",
    "Grouped validation": "分组交叉验证 分组验证 留出站点",
    "Spatial validation": "空间验证 空间交叉验证 空间分块 spatial cross validation",
    "Predictive metrics": "预测性能 模型指标",
    "Model interpretation": "模型解释 可解释机器学习 变量重要性 特征重要性",
    "Spatial data and GIS": "空间分析 地理信息 GIS 栅格 矢量 制图 空间数据",
    "Environmental data and remote sensing": "遥感 环境变量 气候数据 环境协变量 卫星数据",
    "Occurrence data and taxonomy": "物种分布记录 物种出现记录 物种名 分类学 坐标清洗",
    "Traits and comparative ecology": "性状 功能多样性 比较生态学 系统发育",
    "Field sampling and population ecology": "野外采样 野外调查 种群生态学 占域模型 检测概率 栖息地",
    "Distribution and conservation": "物种分布模型 生态位 保护规划 SDM habitat suitability",
    "Time series and evidence synthesis": "时间序列 证据综合 趋势分析 系统综述",
}
TOOL_SYNONYMS = {
    "vegan": "PERMANOVA adonis adonis2 betadisper NMDS Bray Curtis 群落差异方差分析 置换方差分析",
    "segmented": "断点回归 生态阈值 阈值 breakpoint segmented regression",
    "SHAP": "Shapley shap值 夏普利",
    "XGBoost": "xgb extreme gradient boosting 极端梯度提升",
    "ranger": "随机森林 random forest RF",
    "ecmwfr": "ERA5 ERA5-Land 哥白尼 气候再分析",
    "Google Earth Engine": "GEE 地球引擎 NDVI 遥感植被指数",
    "unmarked": "不完全检测 occupancy",
    "iNEXT": "稀释曲线 rarefaction extrapolation coverage",
    "iCAMP": "群落构建 群落组装 群落装配",
    "decontam": "阴性对照 污染识别 去污染",
    "spdep": "Moran's I 莫兰指数 空间自相关",
    "ANCOMBC": "ancom-bc ancom-bc2 ancombc2",
    "biomod2": "生态位模型 物种分布预测",
    "metafor": "元分析 荟萃分析 meta regression 效应量",
}
EXPECTED = ["task", "tool", "ecosystem", "input", "main_output", "when_to_use", "source_url"]
ENVIRONMENTS = ["R", "Python", "CLI", "Bioconductor", "QIIME 2", "Database", "GIS", "Cloud", "JavaScript"]


def environments(ecosystem):
    words = [w.strip().casefold() for w in ecosystem.split("/")]
    envs = []
    for label in ENVIRONMENTS:
        term = label.casefold()
        if any(term == word or term in word.split() for word in words):
            envs.append(label)
    return envs or [ecosystem]


def read_entries():
    entries = []
    for field in FIELDS:
        with (ROOT / "catalog" / f"{field}.tsv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if reader.fieldnames != EXPECTED:
                raise ValueError(f"Unexpected column names in {field}.tsv")
            for row in reader:
                if not all(row.get(key) for key in EXPECTED):
                    raise ValueError(f"Incomplete entry in {field}.tsv: {row}")
                if urlsplit(row["source_url"]).scheme not in {"https", "http"}:
                    raise ValueError(f"Unsupported source URL for {row['tool']}")
                entries.append((field, row))
    return entries


def card(field, row):
    esc = lambda key: html.escape(row[key], quote=True)
    more = html.escape(f"{SYNONYMS.get(row['task'], '')} {TOOL_SYNONYMS.get(row['tool'], '')}", quote=True)
    envs = html.escape("|".join(environments(row["ecosystem"])), quote=True)
    return f'''<article class="card" data-field="{field}" data-task="{esc("task")}" data-env="{envs}" data-keywords="{more}">
      <div class="card-head"><span class="task">{esc("task")}</span><span class="ecosystem">{esc("ecosystem")}</span></div>
      <h2>{esc("tool")}</h2><p class="use">{esc("when_to_use")}</p>
      <details><summary>Inputs and outputs</summary><dl><dt>Input</dt><dd>{esc("input")}</dd><dt>Output</dt><dd>{esc("main_output")}</dd></dl></details>
      <div class="source"><a target="_blank" rel="noopener noreferrer" href="{esc("source_url")}" aria-label="Upstream source for {esc("tool")}">Upstream source <span aria-hidden="true">↗</span></a></div>
    </article>'''


CSS = """
:root{color-scheme:light;--ink:#152f29;--muted:#506760;--forest:#155a44;--line:#cfdbd4;--paper:#f4f6f0;--white:#fff;--accent:#bce0af}
*{box-sizing:border-box}body{margin:0;color:var(--ink);background:var(--paper);font:16px/1.5 "Inter","Source Sans 3",system-ui,sans-serif}
a{color:var(--forest);text-underline-offset:.2em}button,input,select{font:inherit}button,select,summary{cursor:pointer}
:focus-visible{outline:3px solid #72942c;outline-offset:3px}.wrap{max-width:1240px;margin:auto;padding:0 clamp(1rem,4vw,3.75rem)}
header{background:#173e33;color:white;padding:2.1rem 0 1.9rem}.byline{font-size:.92rem;color:#c8dfcc;margin:0 0 1rem}
header h1{font:600 clamp(2rem,5vw,3.8rem)/1.06 "Inter",system-ui,sans-serif;letter-spacing:-.045em;margin:0}
header .intro{max-width:52rem;color:#e0ecdf;margin:.85rem 0 0}.filters{display:grid;grid-template-columns:1.25fr 1.1fr 1.3fr .8fr;gap:.75rem;padding:1.35rem 0 .9rem}
label{display:flex;flex-direction:column;gap:.3rem;font-size:.8rem;font-weight:650;color:var(--muted)}
input,select{height:2.7rem;min-width:0;width:100%;background:#fff;border:1px solid #9fb2a4;border-radius:.45rem;padding:0 .65rem;color:var(--ink);font-size:.94rem;font-weight:400}
.statusline{display:flex;align-items:center;justify-content:space-between;gap:1rem;margin:.1rem 0 1rem}.statusline p{margin:0;color:var(--muted);font-size:.9rem}
button{border:1px solid var(--forest);border-radius:.4rem;background:transparent;color:var(--forest);font-size:.88rem;padding:.36rem .8rem;font-weight:600}
button:hover{background:#e0eadd}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.95rem}
.card{min-width:0;background:var(--white);border:1px solid var(--line);border-radius:.65rem;padding:1rem 1.15rem .9rem;display:flex;flex-direction:column}
.card-head{display:flex;align-items:baseline;justify-content:space-between;gap:.7rem;flex-wrap:wrap}.task{font-weight:650;color:var(--forest);font-size:.78rem}
.ecosystem{font-size:.74rem;color:#466258}.card h2{font-size:1.4rem;line-height:1.18;letter-spacing:-.025em;margin:.65rem 0 .35rem;overflow-wrap:anywhere}
.use{font-size:.95rem;margin:0 0 .8rem}details{font-size:.86rem;color:var(--muted);margin:.05rem 0 .9rem}summary{color:var(--ink)}
dl{display:grid;grid-template-columns:auto 1fr;gap:.4rem .65rem;line-height:1.4;margin:.6rem 0 0}dt{font-weight:650}dd{margin:0}
.source{margin-top:auto;padding-top:.7rem;border-top:1px solid #e4ebe5}.source a{font-size:.85rem;font-weight:650;text-decoration:none}.source a:hover{text-decoration:underline}
.more{text-align:center;margin:1.3rem 0 2rem}.more button{background:var(--forest);color:white;padding:.6rem 1.25rem}.empty{margin:2rem 0}
[hidden]{display:none!important}footer{font-size:.83rem;color:var(--muted);margin:1.5rem 0;padding:1rem 0;border-top:1px solid var(--line)}
@media(max-width:950px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}.filters{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:590px){.cards{grid-template-columns:minmax(0,1fr)}header{padding:1.5rem 0}.filters{gap:.6rem}label:first-child{grid-column:1/-1}label:last-child{grid-column:1/-1}.card{padding:1rem}.card-head{align-items:flex-start}}
@media print{header{background:white;color:black;padding:.5rem 0}.byline,header .intro{color:#333}.filters,.more,.statusline button{display:none}.cards{display:block}.card{break-inside:avoid;box-shadow:none;margin:.5rem 0}}
"""

JS = r"""
const $ = id => document.getElementById(id);
const cards = Array.from(document.querySelectorAll('article.card'));
const q = $('search'), field = $('field'), task = $('task'), env = $('env');
const pageSize = 18;
let limit = pageSize;
const normalize = s => s.toLowerCase().normalize('NFKC');
const entries = cards.map(card => {
  const text = normalize([card.querySelector('h2').textContent, card.dataset.task,
    card.querySelector('.ecosystem').textContent, card.querySelector('.use').textContent,
    card.querySelector('dl').textContent, card.dataset.keywords].join(' '));
  return {card, text, words: new Set(text.split(/[^a-z0-9]+/))};
});
function refreshTasks(){
  const previous = task.value;
  const available = new Set(cards.filter(c => !field.value || c.dataset.field === field.value).map(c => c.dataset.task));
  task.replaceChildren(new Option('All tasks',''));
  Array.from(available).sort().forEach(t => task.add(new Option(t,t)));
  if(available.has(previous)) task.value = previous;
}
function update(reset=true){
  if(reset) limit = pageSize;
  const words = normalize(q.value.trim()).split(/\s+/).filter(Boolean);
  let matches = 0;
  for(const {card,text,words: tokens} of entries){
    const hit = (!field.value || card.dataset.field === field.value) &&
      (!task.value || card.dataset.task === task.value) &&
      (!env.value || card.dataset.env.split('|').includes(env.value)) &&
      words.every(w => /^[a-z0-9]{1,3}$/.test(w) ? tokens.has(w) : text.includes(w));
    card.hidden = !hit || matches >= limit;
    if(hit) matches++;
  }
  $('count').textContent = matches ? 'Showing ' + Math.min(limit,matches) + ' of ' + matches +
    ' matching tool' + (matches === 1 ? '' : 's') : '0 matching tools';
  $('empty').hidden = matches !== 0;
  $('more').hidden = matches <= limit;
  $('reset').disabled = !q.value && !field.value && !task.value && !env.value;
}
q.addEventListener('input',() => update());
field.addEventListener('change',() => {refreshTasks(); update()});
[task,env].forEach(c => c.addEventListener('change',() => update()));
$('reset').addEventListener('click',() => {q.value='';field.value='';env.value='';task.value='';refreshTasks();update();q.focus()});
$('more').addEventListener('click',() => {limit+=pageSize;update(false)});
refreshTasks();update();
"""


def main():
    entries = read_entries()
    field_options = "".join(f'<option value="{key}">{value}</option>' for key, value in FIELDS.items())
    available = sorted({tag for _, row in entries for tag in environments(row["ecosystem"])})
    env_options = "".join(f'<option>{html.escape(tag)}</option>' for tag in available)
    cards = "\n".join(card(field, row) for field, row in entries)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ecology tool directory · Shuai Wu</title><style>{CSS}</style></head><body>
<header><div class="wrap"><p class="byline">Shuai Wu · 武帅</p><h1>Ecology tool directory</h1>
<p class="intro">Explore {len(entries)} tools for microbiome analysis, ecological modelling and field research. Search in English or Chinese.</p></div></header>
<main class="wrap">
<section class="filters" aria-label="Find tools">
<label for="search">Search / 搜索<input id="search" type="search" placeholder="e.g. SEM, 差异丰度, XGBoost"></label>
<label for="field">Field / 领域<select id="field"><option value="">All fields</option>{field_options}</select></label>
<label for="task">Task / 任务<select id="task"><option value="">All tasks</option></select></label>
<label for="env">Environment / 环境<select id="env"><option value="">All environments</option>{env_options}</select></label></section>
<div class="statusline"><p id="count" role="status" aria-live="polite">{len(entries)} tools</p><button type="button" id="reset">Clear filters</button></div>
<noscript><p>All entries are visible. Use your browser’s find command to search.</p></noscript>
<div class="cards" id="results">{cards}</div><p id="empty" class="empty" hidden>Try a broader keyword or clear a filter.</p>
<div class="more"><button type="button" id="more" hidden>Show more tools</button></div>
<footer>Directory works offline. Upstream documentation links require an internet connection.</footer></main>
<script>{JS}</script></body></html>'''
    target = ROOT / "browse.html"
    target.write_text(document, encoding="utf-8")
    print(f"Generated {target.name} with {len(entries)} entries.")


if __name__ == "__main__":
    main()
