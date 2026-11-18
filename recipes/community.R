#!/usr/bin/env Rscript
# Usage: Rscript recipes/community.R OUTPUT_DIR [counts.tsv metadata.tsv]
# counts.tsv: first column sample_id; remaining columns are integer feature counts.
# metadata.tsv: sample_id, habitat. Each row must be an independent sampling unit.
# For matched, nested or repeated samples, adapt the design and permutation scheme.
suppressPackageStartupMessages(library(vegan))
args <- commandArgs(trailingOnly = TRUE)
if (!length(args) %in% c(1L, 3L)) {
  stop("Usage: Rscript recipes/community.R OUTPUT_DIR [counts.tsv metadata.tsv]")
}
out <- args[1L]
set.seed(20261118)

if (length(args) == 3L) {
  tab <- read.delim(args[2L], check.names = FALSE, stringsAsFactors = FALSE)
  meta <- read.delim(args[3L], check.names = FALSE, stringsAsFactors = FALSE)
  if (names(tab)[1L] != "sample_id" || !all(c("sample_id", "habitat") %in% names(meta))) {
    stop("Counts must start with sample_id; metadata needs sample_id and habitat.")
  }
  if (anyNA(tab$sample_id) || anyNA(meta$sample_id) ||
      anyDuplicated(tab$sample_id) || anyDuplicated(meta$sample_id) ||
      !setequal(tab$sample_id, meta$sample_id) || anyDuplicated(names(tab))) {
    stop("Supply one matching unique sample_id per table and unique feature names.")
  }
  meta <- meta[match(tab$sample_id, meta$sample_id), , drop = FALSE]
  counts <- as.matrix(tab[-1L])
  rownames(counts) <- tab$sample_id
} else {
  # Each simulated library represents a distinct sampling plot.
  meta <- data.frame(sample_id = sprintf("plot_%02d", 1:24),
                     habitat = rep(c("grassland", "woodland"), each = 12))
  baseline <- rgamma(32, shape = 1.2)
  counts <- t(vapply(meta$habitat, function(h) {
    weights <- baseline * exp(rnorm(length(baseline), sd = 0.65))
    if (h == "woodland") weights[1:8] <- weights[1:8] * 2
    as.integer(rmultinom(1, sample(800:1800, 1), weights))
  }, integer(length(baseline))))
  dimnames(counts) <- list(meta$sample_id, sprintf("ASV_%02d", seq_along(baseline)))
}
if (!ncol(counts) || !is.numeric(counts) || any(!is.finite(counts)) ||
    any(counts < 0) || any(counts != round(counts)) || any(rowSums(counts) == 0)) {
  stop("Provide nonnegative integer counts and a nonzero library size for every sample.")
}
if (anyNA(meta$habitat) || any(!nzchar(trimws(as.character(meta$habitat))))) {
  stop("Missing habitat label.")
}
meta$habitat <- droplevels(factor(meta$habitat))
if (nlevels(meta$habitat) < 2L || any(table(meta$habitat) < 2L)) {
  stop("Supply at least two habitats and two independent samples per habitat.")
}
if (dir.exists(out) && length(list.files(out, all.files = TRUE, no.. = TRUE))) {
  stop("Choose an empty output directory to preserve previous results.")
}
if (!dir.exists(out) && !dir.create(out, recursive = TRUE)) stop("Cannot create output directory.")
write_tsv <- function(x, name) {
  write.table(x, file.path(out, name), sep = "\t", row.names = FALSE, quote = FALSE)
}
alpha <- data.frame(meta[c("sample_id", "habitat")], reads = rowSums(counts),
                    observed_features = specnumber(counts), shannon_ln = diversity(counts))
write_tsv(alpha, "alpha.tsv")
# Observed richness is sensitive to depth. Use coverage-standardized comparisons where needed.
distances <- vegdist(decostand(counts, method = "total"), method = "bray")
if (!any(distances > 0)) stop("Identical relative profiles give no ordination.")
ord <- wcmdscale(distances, k = 2, eig = TRUE, add = "lingoes")
coords <- as.matrix(ord$points)
if (ncol(coords) == 1L) coords <- cbind(coords, 0) # display rank-one distances on a line
coord_table <- data.frame(meta[c("sample_id", "habitat")], axis1 = coords[, 1], axis2 = coords[, 2])
write_tsv(coord_table, "ordination.tsv")
permanova <- adonis2(distances ~ habitat, data = meta, permutations = 999, add = "lingoes")
dispersion <- permutest(betadisper(distances, meta$habitat, add = "lingoes",
                                   bias.adjust = TRUE), permutations = 999)
write_tsv(data.frame(term = rownames(permanova), as.data.frame(permanova), check.names = FALSE),
          "permanova.tsv")
write_tsv(data.frame(term = rownames(dispersion$tab), dispersion$tab, check.names = FALSE),
          "dispersion.tsv")
cols <- hcl.colors(nlevels(meta$habitat), palette = "Dark 3")
pdf(file.path(out, "ordination.pdf"), width = 6, height = 5)
plot(coords[, 1:2, drop = FALSE], col = cols[meta$habitat], pch = 19, asp = 1,
     xlab = "PCoA 1", ylab = "PCoA 2")
legend("topright", levels(meta$habitat), col = cols, pch = 19, bty = "n")
invisible(dev.off())
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
message("Wrote diversity, ordination, PERMANOVA and dispersion results to ", out)
