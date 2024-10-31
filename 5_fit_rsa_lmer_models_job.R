library(tidyverse)
library(lme4)
library(lmerTest)

args <- commandArgs(trailingOnly=TRUE)

model_id <- args[1]
model_name_or_num <- args[2]
experiment <- args[3]
test_period <- args[4]
use_jitter <- args[5]
my_max_n_tries <- as.integer(args[6])
my_tol_n_tries <- as.integer(args[7])
update <- args[8]
verbose <- args[9]
use_REML <- args[10]
warm_start <- as.integer(args[11])
drop_freq <- args[12]

print(paste('max_n_tries: ', my_max_n_tries))
print(paste('tol_n_tries: ', my_tol_n_tries))
print(paste('using REML: ', use_REML))
print(paste('experiment: ', experiment))
print(paste('test_period: ', test_period))
print(paste('warm_start: ', warm_start))
print(paste('drop_freq: ', drop_freq))

base_dir <- "~/study_phase_reinstatement"
scratch_dir <- "/scratch/djh/study_phase_reinstatement"
# base_dir <- ""
data_dir <- file.path(scratch_dir, "preproc_data", experiment)
results_dir <- file.path(base_dir, "results")
code_dir <- file.path(base_dir)
module_dir <- file.path(code_dir, "modules")

source(file.path(module_dir, "lmer_utils.R"))

if(!is.na(drop_freq)) {
    corr_z_df <- read_csv(file.path(data_dir, 
                                paste(test_period, 'model_df', 'drop_freq', paste0(drop_freq, '.csv'), sep = '_')))

} else {
    corr_z_df <- read_csv(file.path(data_dir, 
                                paste(test_period, 'model_df.csv', sep = '_')))
}
source(file.path(code_dir, "rsa_lmer_model_list.R"))
corr_z_df <- corr_z_df %>% 
    mutate(
        serialpos_encoding_fct = factor(serialpos_encoding)
)

# print(models[[test_period]])
print(model_id)

if(model_name_or_num) {
    model_id <- as.integer(model_id)
    model_name <- names(models[[experiment]][[test_period]])[[model_id]]
} else {
    model_name <- model_id
}

if(use_REML) {
    REML_str <- "REML"
} else {
    REML_str <- "ML"
}

print("update")
print(update)
if(update) {
    prev_mod <- readRDS(file.path(results_dir, paste(experiment, test_period, model_name, REML_str, "fit.rds", sep = '_')))
} else {
    prev_mod <- c()
}
print(prev_mod)

print("verbose")
print(verbose)

ff <- models[[experiment]][[test_period]][[model_name]]
print(model_name)
print(ff)

if(warm_start != 0) {
    if(warm_start < 0) {
        warm_start_model_id <- model_id + warm_start
    } else {
        warm_start_model_id <- warm_start
    }
    print(warm_start_model_id)
    warm_start_model_name <- names(models[[experiment]][[test_period]])[[warm_start_model_id]]
    prev_mod_path <- file.path(results_dir, paste(experiment, test_period, warm_start_model_name, REML_str, "fit.rds", sep = '_'))
    if(!file.exists(prev_mod_path)) {
        prev_mod_path <- file.path(results_dir, paste(experiment, test_period, warm_start_model_name, "REML", "fit.rds", sep = '_'))
    }
    prev_singular_mod <- readRDS(prev_mod_path)
    pars <- getME(prev_singular_mod, "theta")
    print('old pars')
    print(pars)
    lmod <- lFormula(ff, data = corr_z_df)
    pfun <- lme4:::mkPfun(diag.only = FALSE, old = TRUE, prefix = NULL)
    tnames <- c(unlist(mapply(pfun, names(lmod$reTrms$cnms), lmod$reTrms$cnms)))
    start <- pars[tnames]
    print('selected pars')
} else {
    start <- NULL
}
print(start)

if(!is.na(drop_freq)) {
    save_path <- file.path(results_dir, paste(experiment, test_period, model_name, REML_str, "drop_freq", drop_freq, "fit_unfinished.rds", sep = '_'))
} else {
    save_path <- file.path(results_dir, paste(experiment, test_period, model_name, REML_str, "fit_unfinished.rds", sep = '_'))
}

mod <- fit_lmer(ff, data = corr_z_df, max_n_tries = my_max_n_tries, use_jitter = use_jitter, tol_n_tries = my_tol_n_tries, prev_m = prev_mod,
               use_verbose = verbose, use_REML = use_REML, save_path = save_path, start = start)

if(!is.na(drop_freq)) {
    saveRDS(mod, file.path(results_dir, paste(experiment, test_period, model_name, REML_str, "drop_freq", drop_freq, "fit.rds", sep = '_')))
} else {
    saveRDS(mod, file.path(results_dir, paste(experiment, test_period, model_name, REML_str, "fit.rds", sep = '_')))
}


print('warnings: ')
print(warnings())