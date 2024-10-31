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

corr_z_df <- read_csv(file.path(data_dir, 
                                paste(test_period, 'model_df.csv', sep = '_')))

print(test_period)
print(model_name)

print(paste(experiment, test_period, model_name, 'fit.rds', sep = '_'))
fp <- file.path(results_dir, paste(experiment, test_period, model_name, 'fit.rds', sep = '_'))
if (file.exists(fp)) {
    m <- readRDS(fp)
} else {
    print('file missing')
}

print(round(anova(m, type='3'), digits = 3))

plot_aes <- aes(x = item_recalled_recode,
                   y = corr_z_unscaled, 
                   ymin = corr_z_unscaled - (corr_z_unscaled_SE), 
                   ymax = corr_z_unscaled + (corr_z_unscaled_SE)
              )
if (test_period == "encoding_isi") {
    ref_grid_nesting <- "item_first %in% item_recalled, recall_neighbor %in% (item_recalled * item_before_isi_recalled)"
    plot_aes <- aes(x = item_recalled_recode,
               y = corr_z_unscaled, 
               color = item_before_isi_recalled_recode,
               ymin = corr_z_unscaled - (corr_z_unscaled_SE), 
               ymax = corr_z_unscaled + (corr_z_unscaled_SE),
              group = item_before_isi_recalled_recode)
    emmeans_rec_ff <- revpairwise ~ item_recalled | item_before_isi_recalled
    if (experiment == "catFR1") {
        emmeans_rec_ff <- revpairwise ~ item_recalled | item_before_isi_recalled * same_category   
    }
} else if (test_period == "encoding_end") {
    ref_grid_nesting <- "item_first %in% item_recalled, recall_neighbor %in% (item_recalled * current_item_recalled)"
    plot_aes <- aes(x = item_recalled_recode,
                       y = corr_z_unscaled, 
                       color = current_item_recalled_recode, 
                       ymin = corr_z_unscaled - (corr_z_unscaled_SE), 
                       ymax = corr_z_unscaled + (corr_z_unscaled_SE),
                       group = current_item_recalled_recode)
    emmeans_rec_ff <- revpairwise ~ item_recalled | current_item_recalled
    if (experiment == "catFR1") {
        emmeans_rec_ff <- revpairwise ~ item_recalled | current_item_recalled * same_category
    }
} else {
    ref_grid_nesting <- "item_first %in% item_recalled"
    emmeans_rec_ff <- revpairwise ~ item_recalled | serialpos_scale
}

RG.rec <- ref_grid(m, data = corr_z_df, weights="cells",
         nesting = ref_grid_nesting)

EMM_rec <- emmeans(RG.rec, emmeans_rec_ff, 
        lmer.df = "satterthwaite", 
                   weights = "cells",
        data = corr_z_df)
print(EMM_rec)

p <- plot(EMM_rec, comparison = TRUE)
contrast_plot_df <- ggplot_build(p)$plot$data

corr_z_scaled <- scale(corr_z_df$corr_z)
corr_z_center <- attr(corr_z_scaled, "scaled:center")
corr_z_scale <- attr(corr_z_scaled, "scaled:scale")

emm_rec_df <- contrast_plot_df %>% mutate(
    lower.SE = the.emmean - lcmpl,
    upper.SE = rcmpl - the.emmean,
    SE = pmax(lower.SE, upper.SE, na.rm = TRUE), #get widest interval to make it even
    corr_z_unscaled = (the.emmean * corr_z_scale) + corr_z_center, #center gets subtracted off
    corr_z_unscaled_SE = (SE * corr_z_scale),
    item_recalled_recode = if_else(item_recalled, 
                            'Recalled', 'Not Recalled')
)

if (test_period == "encoding_end") {
    emm_rec_df <- emm_rec_df %>% mutate(
        current_item_recalled_recode = if_else(current_item_recalled, 
                            'Recalled', 'Not Recalled')
    )
} else if (test_period == "encoding_isi") {
    emm_rec_df <- emm_rec_df %>% mutate(
        item_before_isi_recalled_recode = if_else(item_before_isi_recalled, 
                            'Recalled', 'Not Recalled')
    )
}
if ((experiment == "catFR1") & (test_period != "distractor")) {
    emm_rec_df <- emm_rec_df %>% mutate(
        same_category_recode = if_else(same_category, 'Same Category', 'Different Category')
    )
}

theme(
        axis.text.x = element_text(angle = 45, vjust = .5),
        strip.background = element_blank(),
        strip.text.x = element_text(size = 14)
    )

print(emm_rec_df)
print(plot_aes)
p <- ggplot(plot_aes, 
       data = emm_rec_df) + 
    geom_point(position = position_dodge(width = 0.25), size = 5) + 
    geom_pointrange(position = position_dodge(width = 0.25), linewidth = 1.5) +
    theme_classic() +
    labs(x = "Encoded Item", y = "z-Transformed Correlation") +
    theme(
        legend.text = element_text(size = 20),
        legend.title = element_text(size = 20),
        axis.text = element_text(size = 18),
        axis.title = element_text(size = 20)
    )

if ((experiment != "RepFR1")) {
    if (test_period != "distractor") {
        p <- p + 
            geom_line(position = position_dodge(width = 0.25), linewidth = 1.5) +
            theme(
                axis.text.x = element_text(angle = 45, vjust = .5),
                strip.background = element_blank(),
                strip.text.x = element_text(size = 14)
            )
        if (test_period == "encoding_isi") {
            p <- p + labs(color = "Item Before ISI") +
                ylim(.11, .124)
        } else if (test_period == "encoding_end") {
            p <- p + labs(color = "Current Item") +
                ylim(.1025, .1225)
        }
        if (experiment == "catFR1") {
            p <- p + facet_grid(cols = vars(same_category_recode))
        }
    } else {
        p <- p + ylim(.09, .101)
    }
}

ggsave(file.path('figs', paste(experiment, test_period, 'recall_lmer.pdf', sep = '_')), plot = p)