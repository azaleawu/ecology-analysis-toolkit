#!/usr/bin/env Rscript
# Usage: Rscript recipes/path_analysis.R [output_directory] [input.csv]
# CSV columns: precipitation_mm, temperature_c, soil_moisture_pct, respiration.
# Each row is an independent sampling unit. Adapt the sampling model for repeated sites.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) > 2L) stop("Usage: Rscript path_analysis.R [output_directory] [input.csv]")
if (!requireNamespace("lavaan", quietly = TRUE)) stop("Install lavaan with install.packages('lavaan').")
out <- if (length(args)) args[1] else file.path("outputs", "path_analysis")
columns <- c("precipitation_mm", "temperature_c", "soil_moisture_pct", "respiration")

if (length(args) == 2L) {
  observations <- read.csv(args[2], check.names = FALSE)
} else {
  set.seed(41)
  n <- 180L
  rain <- rnorm(n, 600, 90)
  temp <- rnorm(n, 12, 3)
  water <- 24 + 0.035 * (rain - 600) - 0.7 * (temp - 12) + rnorm(n, sd = 2.5)
  flux <- 4 + 0.18 * (water - 24) + 0.24 * (temp - 12) + rnorm(n, sd = 0.8)
  observations <- data.frame(precipitation_mm = rain, temperature_c = temp,
                             soil_moisture_pct = water, respiration = flux)
}
if (!all(columns %in% names(observations))) stop("Required CSV columns: ", paste(columns, collapse = ", "))
data <- observations[columns]
if (!all(vapply(data, is.numeric, logical(1))) || any(!is.finite(as.matrix(data)))) {
  stop("Input columns must contain finite numeric measurements.")
}
if (nrow(data) <= length(columns) || any(vapply(data, sd, numeric(1)) == 0)) {
  stop("The path model requires multiple observations and varying predictors and response.")
}

# Rain reaches respiration through moisture. Temperature also has a direct path.
model <- '
  soil_moisture_pct ~ a * precipitation_mm + b * temperature_c
  respiration       ~ c * soil_moisture_pct + d * temperature_c
  rain_via_moisture := a*c
  temp_via_moisture := b*c
  temp_total        := d + b*c
'
fit <- lavaan::sem(model, data = data, estimator = "MLR")
if (!lavaan::lavInspect(fit, "converged")) stop("Path model did not converge.")
params <- lavaan::parameterEstimates(fit, standardized = TRUE, ci = TRUE)
paths <- params[params$op %in% c("~", ":="),
                c("lhs", "op", "rhs", "est", "se", "ci.lower", "ci.upper", "std.all")]
stats <- lavaan::fitMeasures(fit, c("chisq.scaled", "df", "pvalue.scaled", "cfi.robust", "rmsea.robust", "srmr"))
dir.create(out, showWarnings = FALSE, recursive = TRUE)
write.csv(paths, file.path(out, "paths.csv"), row.names = FALSE)
write.csv(data.frame(measure = names(stats), value = as.numeric(stats)),
          file.path(out, "model_fit.csv"), row.names = FALSE)
write.csv(data, file.path(out, "observations.csv"), row.names = FALSE)
cat(sprintf("Fit path model to %d independent observations. Outputs: %s\n", nrow(data), out))
