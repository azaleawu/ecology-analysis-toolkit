# Atacama soil example

`atacama_counts.tsv` contains positive library-by-ASV counts for five soil libraries from site BAQ2420 in the Baquedano transect. These are the derived counts from Shuai Wu's published DADA2 workflow, run on the QIIME 2 2024.10 teaching subset of Neilson et al. (2017). The underlying study is archived under ERP019482. Each library belongs to the same 16S V4 comparison group. The file contains 128 distinct ASVs and 4,261 reads after chimera removal.

Run `python toolkit.py run count-table --out results/atacama` to summarize observed richness and natural-log Shannon diversity and calculate Bray–Curtis distances after scaling each library to sum to one. The sample is small and the exercise is descriptive. The output uses the original library identifiers. Use `--input PATH` with the positive-depth libraries from one compatible analysis group for your own study.

[Original study](https://doi.org/10.1128/mSystems.00195-16) · [Teaching data](https://docs.qiime2.org/2024.10/tutorials/atacama-soils/) · [Exact upstream workflow and library-level counts](https://github.com/azaleawu/soil-amplicon-dada2/blob/7a38dabcf5c945b53eafa5e7ead577418f03f106/docs/soil-example.md)
