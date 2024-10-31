library(tidyverse)
library(emmeans)
library(broom.mixed)
source('modules/lmer_utils.R')
emm_options(lmerTest.limit = 500000)

args <- commandArgs(trailingOnly=TRUE)
experiment <- args[1]
test_period <- args[2]
model_name <- args[3]

base_dir <- "~/study_phase_reinstatement"
scratch_dir <- "/scratch/djh/study_phase_reinstatement"
data_dir <- file.path(scratch_dir, "preproc_data", experiment)
results_dir <- file.path(base_dir, "results")
code_dir <- file.path(base_dir)
module_dir <- file.path(code_dir, "modules")

emm_contrast_dfs <- list()
emm_rec_dfs <- list()
dropped_freq_hz_list <- c(3, 5.4, 9.7, 17.3, 31.1, 55.9, 100.3, 180)

for (drop_freq_ind in 1:8) {
    drop_freq_python_ind <- drop_freq_ind - 1
    corr_z_df <- read_csv(file.path(data_dir, 
                                paste(test_period, 'model_df', 'drop_freq', paste0(drop_freq_python_ind, '.csv'), sep = '_')))
    
    mod_fp <- file.path(results_dir, paste(experiment, test_period, model_name, 'drop_freq', drop_freq_python_ind, 'fit.rds', sep = '_'))
    if(file.exists(mod_fp)) {
        m <- readRDS(file.path(mod_fp))
    } else {
        print('file missing')
    }
    
    emmeans_rec_ff <- revpairwise ~ item_recalled | item_before_isi_recalled
    if (experiment == "catFR1") {
        emmeans_rec_ff <- revpairwise ~ item_recalled | item_before_isi_recalled * same_category   
    }
    ref_grid_nesting <- "item_first %in% item_recalled, recall_neighbor %in% (item_recalled * item_before_isi_recalled)"
    
    RG.rec <- ref_grid(m, 
                       data = corr_z_df, 
                       weights="cells",
                       nesting = ref_grid_nesting)
    EMM_rec <- emmeans(RG.rec, emmeans_rec_ff, 
                   lmer.df = "satterthwaite", 
                   weights = "cells",
                   data = corr_z_df)
    
    corr_z_scale <- scale(corr_z_df$corr_z)
    corr_z_center <- attr(corr_z_scale, "scaled:center")
    corr_z_scale <- attr(corr_z_scale, "scaled:scale")
    emm_contrast_dfs[[drop_freq_ind]] <- EMM_rec$contrasts %>% as.data.frame() %>% 
        mutate(
            item_before_isi_recalled_recode = ifelse(item_before_isi_recalled, 
                                   "Item before ISI recalled", 
                                   "Item before ISI not recalled"),
            corr_z_diff_unscaled = (estimate * corr_z_scale), #center gets subtracted off
            corr_z_diff_unscaled_SE = (SE * corr_z_scale),
            dropped_freq = drop_freq_ind,
            dropped_freq_hz = dropped_freq_hz_list[[drop_freq_ind]]
        )
    if (experiment == "catFR1") {
        emm_contrast_dfs[[drop_freq_ind]] <- emm_contrast_dfs[[drop_freq_ind]] %>% mutate(
            same_category_recode = if_else(same_category, 'Same Category', 'Different Category')
        )
    }
}

emm_contrast_drop_freq_df <- bind_rows(emm_contrast_dfs)

p <- ggplot(aes(y = corr_z_diff_unscaled, 
           x = dropped_freq_hz, 
           ymin = corr_z_diff_unscaled - (2 * corr_z_diff_unscaled_SE), 
           ymax = corr_z_diff_unscaled + (2 * corr_z_diff_unscaled_SE)), 
       data = emm_contrast_drop_freq_df) +
    geom_point(size = 5) + 
    geom_pointrange(linewidth = 1.5) +
    geom_hline(yintercept = 0) +
    theme_classic() +
    labs(x = "Dropped Frequency (Hz)", y = "Recalled - Not Recalled") +
    scale_x_continuous(trans = 'log2') + 
    ylim(-.003, .011) +
    theme(
        strip.placement = "outside",
        strip.background = element_blank(), # Make facet label background white.
        strip.text = element_text(size = 16),
        axis.text = element_text(size = 16),
        axis.title = element_text(size = 16)
    ) 
if (experiment == "catFR1") {
    p <- p + facet_grid(cols = vars(same_category_recode), rows = vars(item_before_isi_recalled_recode))
} else {
    p <- p + facet_grid(rows = vars(item_before_isi_recalled_recode))
}

ggsave(file.path('figs', paste(experiment, test_period, 'recall_lmer_drop_freq.pdf', sep = '_')), plot = p)