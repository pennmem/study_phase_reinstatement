library(tidyverse)

base_dir <- "~/study_phase_reinstatement"
scratch_dir <- "/scratch/djh/study_phase_reinstatement"
test_period <- 'encoding'
experiment <- 'catFR1'
data_dir <- file.path(scratch_dir, "preproc_data", experiment)
results_dir <- file.path(base_dir, "results")
code_dir <- file.path(base_dir)
module_dir <- file.path(code_dir, "modules")

corr_z_df <- read_csv(file.path(data_dir, 
                                paste(test_period, 'model_df.csv', sep = '_')))

corr_z_df <- corr_z_df %>% 
    group_by(subject_encoding, session_encoding, list_encoding) %>%
    mutate(
        corr_z_list_mean = mean(corr_z)
    ) %>% group_by(subject_encoding, session_encoding) %>%
    mutate(
        corr_z_sess_mean = mean(corr_z_list_mean)
    ) %>% group_by(subject_encoding) %>%
    mutate(
        corr_z_sub_mean = mean(corr_z_sess_mean)
    ) %>% ungroup() %>%
    mutate(
        corr_z_all_mean = mean(corr_z_sub_mean),
        corr_z_list_adj = corr_z - corr_z_list_mean + corr_z_all_mean
    )

corr_z_list_cousineau_df <- corr_z_df %>% 
    group_by(subject_encoding, session_encoding, list_encoding, abs_serialpos_dist, same_category) %>%
    summarize(
        corr_z_list_adj = mean(corr_z_list_adj)
    ) %>% 
    group_by(subject_encoding, session_encoding, abs_serialpos_dist, same_category) %>%
    summarize(
        corr_z_list_adj = mean(corr_z_list_adj)
    ) %>% 
    group_by(subject_encoding, abs_serialpos_dist, same_category) %>%
    summarize(
        corr_z_list_adj = mean(corr_z_list_adj)
    )

mean_se_corr_z_list_cousineau_df <- corr_z_list_cousineau_df %>%
    group_by(abs_serialpos_dist, same_category) %>%
    summarize(mean_corr_z = mean(corr_z_list_adj), 
              se_corr_z = sd(corr_z_list_adj) / sqrt(n())
    ) %>%
    mutate(
        cat_type = if_else(same_category, "Same Category", "Different Category")
    )

ggplot(aes(x = abs_serialpos_dist, 
           y = mean_corr_z, 
           color = cat_type, 
           group = cat_type, 
           ymin = mean_corr_z - (2 * se_corr_z),
           ymax = mean_corr_z + (2 * se_corr_z)
          ), data = mean_se_corr_z_list_cousineau_df) + 
    geom_point(size = 5) + 
    geom_pointrange(linewidth = 1.5) +
    geom_line(linewidth = 1.5) +
    theme_classic() +
    labs(color = "", 
         x = "Serial Position Distance", y = "z-transformed correlation") +
    scale_x_continuous(breaks = 1:11) +
    theme(
        legend.text = element_text(size = 20),
        legend.title = element_text(size = 20),
        axis.text = element_text(size = 20),
        axis.title = element_text(size = 20)
    )
ggsave('figs/encoding_fig2.pdf')