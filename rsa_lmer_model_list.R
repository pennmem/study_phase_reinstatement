library(modelr)

models <- list()

models[['catFR1']] <- list()
models[['FR1']] <- list()
models[['RepFR1']] <- list()

models[['catFR1']][['encoding']] <- formulas(
    ~scale(corr_z),
    m1 = ~(same_category * abs_serialpos_dist_center) + 
    (same_category * abs_serialpos_dist_center | subject_encoding) +
    (same_category * abs_serialpos_dist_center | subject_encoding:session_encoding_encoding) +
    (same_category * abs_serialpos_dist_center | subject_encoding:session_encoding:list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding2) +
    (same_category * abs_serialpos_dist_center | list_encoding) +
    (dummy(same_category) | serialpos_encoding) + 
    (dummy(same_category) | serialpos_encoding2) +  
    (same_category | serialpos_encoding:serialpos_encoding2),
    
    m1_final = ~(same_category * abs_serialpos_dist_scale) + 
    (dummy(same_category) * abs_serialpos_dist_scale || subject_encoding) +
    (abs_serialpos_dist_scale + dummy(same_category):abs_serialpos_dist_scale || subject_encoding:session_encoding) +
    (abs_serialpos_dist_scale || subject_encoding:session_encoding:list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    # (1 | subject:session:list:serialpos_encoding2) +
    (1 | list_encoding) +
    (dummy(same_category) || serialpos_encoding) + 
    (0 + dummy(same_category) || serialpos_encoding2) + 
    (dummy(same_category) || serialpos_encoding:serialpos_encoding2),
)

models[['catFR1']][['encoding_isi']] <- formulas(
    ~scale(corr_z),
    m1 = ~((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category) + 
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding) +
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding:session_encoding) +
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding:session_encoding:list_encoding) +
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:prev_serialpos_encoding_isi) + 
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | serialpos_encoding) + 
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | prev_serialpos_encoding_isi) + 
    ((item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category | serialpos_encoding:prev_serialpos_encoding_isi),
    
        m1_final = ~(item_first + item_recalled) * item_before_isi_recalled * same_category + recall_neighbor + recall_neighbor:same_category + 
(dummy(item_first) * dummy(item_before_isi_recalled) + dummy(item_recalled):dummy(item_before_isi_recalled) + dummy(item_recalled):dummy(same_category) || subject_encoding) +
(dummy(item_first) + dummy(item_recalled) || subject_encoding:session_encoding) +
(dummy(item_recalled) + dummy(item_recalled):dummy(item_before_isi_recalled) + (dummy(item_before_isi_recalled) * dummy(same_category)) || subject_encoding:session_encoding:list_encoding) +
    (dummy(item_recalled) * dummy(item_before_isi_recalled) || list_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:prev_serialpos_encoding_isi) + 
    (dummy(item_recalled) * dummy(same_category) + dummy(item_before_isi_recalled) + dummy(item_recalled):dummy(item_before_isi_recalled):dummy(same_category) + dummy(same_category):dummy(recall_neighbor) || serialpos_encoding) + 
    (dummy(item_before_isi_recalled) + dummy(item_first):dummy(same_category) + dummy(same_category):dummy(recall_neighbor) || prev_serialpos_encoding_isi) + 
 (dummy(same_category) | serialpos_encoding:prev_serialpos_encoding_isi),
    )

models[['catFR1']][['encoding_end']] <- formulas(
    ~scale(corr_z), 
    m1 = ~((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category) + 
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding) +
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding:session_encoding) +
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | subject_encoding:session_encoding:list_encoding) +
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding_end) + 
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | serialpos_encoding) + 
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | serialpos_encoding_end) + 
    ((item_first + item_recalled) * current_item_recalled * same_category + recall_neighbor + recall_neighbor:same_category | serialpos_encoding:serialpos_encoding_end),
    
    m1_final = ~((item_first + item_recalled) * current_item_recalled * same_category) + recall_neighbor + recall_neighbor:same_category + 
((dummy(item_first) + dummy(current_item_recalled) + dummy(same_category))^2 - dummy(item_first):dummy(current_item_recalled) || subject_encoding) +
(dummy(item_first) + dummy(item_recalled) || subject_encoding:session_encoding) +
(dummy(item_recalled) + dummy(same_category) | subject_encoding:session_encoding:list_encoding) +
    (dummy(item_recalled) + dummy(item_first):dummy(current_item_recalled) || list_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding_end) + 
    (dummy(item_recalled) * dummy(current_item_recalled) || serialpos_encoding) + 
    (dummy(same_category) + dummy(recall_neighbor) || serialpos_encoding_end) + 
(dummy(item_first) + dummy(same_category):dummy(recall_neighbor) || serialpos_encoding:serialpos_encoding_end),
    )

models[['catFR1']][['distractor']] <- formulas(
    ~scale(corr_z),
    m1 = ~(item_first + item_recalled) * serialpos_scale + 
((item_first + item_recalled) * serialpos_scale | subject_encoding) +
((item_first + item_recalled) * serialpos_scale | subject_encoding:session_encoding) +
((item_first + item_recalled) * serialpos_scale | subject_encoding:session_encoding:list_encoding) +
((item_first + item_recalled) * serialpos_scale | list_encoding) +
(item_first + item_recalled | serialpos_encoding) + 
(item_first + item_recalled | serialpos_encoding:subject_encoding:session_encoding),
    
    m1_final = ~(item_first + item_recalled) * serialpos_scale + 
    (dummy(item_first) + (dummy(item_recalled) * serialpos_scale) || subject_encoding) +
    (serialpos_scale + dummy(item_recalled) || subject_encoding:session_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding) +
    (serialpos_scale | list_encoding) +
    (1 | serialpos_encoding) + 
    (1 | serialpos_encoding:subject_encoding:session_encoding),
)

models[['FR1']][['encoding_isi']] <- formulas(
    ~scale(corr_z),
    
    m1 = ~((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor) + 
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | subject_encoding) + 
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | subject_encoding:session_encoding) +
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | subject_encoding:session_encoding:list_encoding) +
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:prev_serialpos_encoding_isi) + 
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | serialpos_encoding) + 
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | prev_serialpos_encoding_isi) + 
    ((item_first + item_recalled) * item_before_isi_recalled + recall_neighbor | serialpos_encoding:prev_serialpos_encoding_isi),
    
    m1_final = ~((item_first + item_recalled) * item_before_isi_recalled) + recall_neighbor + 
(dummy(item_recalled) + dummy(item_first) + dummy(item_before_isi_recalled) || subject_encoding) +
(dummy(item_first) + dummy(item_recalled) || subject_encoding:session_encoding) +
(dummy(item_first) || subject_encoding:session_encoding:list_encoding) +
    (dummy(recall_neighbor) || list_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
(1 | subject_encoding:session_encoding:list_encoding:prev_serialpos_encoding_isi) + 
    ((dummy(item_recalled) * dummy(item_before_isi_recalled)) + dummy(recall_neighbor) || serialpos_encoding) + 
    (dummy(item_first) || prev_serialpos_encoding_isi) + 
(dummy(item_recalled) | serialpos_encoding:prev_serialpos_encoding_isi),
)

models[['FR1']][['encoding_end']] <- formulas(
    ~scale(corr_z), 
    m1 = ~((item_first + item_recalled) * current_item_recalled + recall_neighbor) + 
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | subject_encoding) +
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | subject_encoding:session_encoding) +
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | subject_encoding:session_encoding:list_encoding) +
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding_end) + 
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | serialpos_encoding) + 
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | serialpos_encoding_end) + 
    ((item_first + item_recalled) * current_item_recalled + recall_neighbor | serialpos_encoding:serialpos_encoding_end),
    
    m1_final = ~((item_first + item_recalled) * current_item_recalled + recall_neighbor) + 
    ((dummy(item_recalled) * dummy(current_item_recalled)) + dummy(item_first) || subject_encoding) +
    (dummy(item_first) + dummy(item_recalled):dummy(current_item_recalled) + dummy(current_item_recalled) || subject_encoding:session_encoding) +
    (dummy(recall_neighbor) || subject_encoding:session_encoding:list_encoding) +
    (dummy(item_first):dummy(current_item_recalled) + dummy(item_recalled) + dummy(current_item_recalled) + dummy(recall_neighbor) || list_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding) +
    (1 | subject_encoding:session_encoding:list_encoding:serialpos_encoding_end) + 
    (dummy(item_first) + (dummy(item_recalled) * dummy(current_item_recalled)) || serialpos_encoding) + 
    ((dummy(item_recalled) * dummy(current_item_recalled)) || serialpos_encoding_end) + 
    (dummy(item_first) + dummy(item_recalled) + dummy(recall_neighbor) || serialpos_encoding:serialpos_encoding_end)
    )

models[['FR1']][['distractor']] <- formulas(
    ~scale(corr_z),
    m1 = ~(item_first + item_recalled) * serialpos_scale + 
((item_first + item_recalled) * serialpos_scale | subject_encoding) +
((item_first + item_recalled) * serialpos_scale | subject_encoding:session_encoding) +
((item_first + item_recalled) * serialpos_scale | subject_encoding:session_encoding:list_encoding) +
((item_first + item_recalled) * serialpos_scale | list_encoding) +
(item_first + item_recalled | serialpos_encoding) + 
(item_first + item_recalled | serialpos_encoding:subject_encoding:session_encoding),
    
    m1_final = ~(item_first + item_recalled) * serialpos_scale + 
    (dummy(item_recalled) * serialpos_scale | subject_encoding) +
    (dummy(item_first) + dummy(item_recalled) + serialpos_scale | subject_encoding:session_encoding) +
    (serialpos_scale | subject_encoding:session_encoding:list_encoding) +
    (dummy(item_first):serialpos_scale + serialpos_scale + dummy(item_recalled):serialpos_scale || list_encoding) +
    (dummy(item_first) | serialpos_encoding) + 
    (1 | serialpos_encoding:subject_encoding:session_encoding)
)

models[['RepFR1']][['distractor']] <- formulas(
    ~scale(corr_z),
    m1 = ~(item_first + item_recalled) * serialpos_scale + 
((dummy(item_first) + dummy(item_recalled)) * serialpos_scale | subject_encoding) +
((dummy(item_first) + dummy(item_recalled)) * serialpos_scale | subject_encoding:session_encoding) +
((dummy(item_first) + dummy(item_recalled)) * serialpos_scale | subject_encoding:session_encoding:list_encoding) +
((dummy(item_first) + dummy(item_recalled)) * serialpos_scale | list_encoding) +
((dummy(item_first) + dummy(item_recalled)) | serialpos_encoding) + 
((dummy(item_first) + dummy(item_recalled)) | serialpos_encoding:subject_encoding:session_encoding),
    
    m1_final = ~(item_first + item_recalled) * serialpos_scale + 
(serialpos_scale + dummy(item_first):serialpos_scale || subject_encoding) +
(dummy(item_recalled) + serialpos_scale || subject_encoding:session_encoding) +
(dummy(item_recalled) * serialpos_scale | subject_encoding:session_encoding:list_encoding) +
(serialpos_scale + dummy(item_recalled):serialpos_scale || list_encoding) +
(dummy(item_first) | serialpos_encoding) + 
(1 | serialpos_encoding:subject_encoding:session_encoding)
)
