import pandas as pd
pd.options.mode.copy_on_write = True
import numpy as np
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--exp', default='catFR1', type=str)
parser.add_argument('--test_period', default='encoding_isi', type=str)
parser.add_argument('--df_id', default=-1, type=int)
args = vars(parser.parse_args())

df_id = args['df_id']
exp = args['exp']
test_period = args['test_period']

scratch_dir = '/scratch/djh/study_phase_reinstatement/'
output_dir = scratch_dir + 'preproc_data/' + exp + '/'
# scratch_dir = '../'
encoding_period = 'encoding'

test_period_str = test_period
if test_period == 'encoding':
    test_period_str = test_period + '2'
agg_rsa_fn = '_'.join([test_period, encoding_period, 'raw_item_corr_df'])
model_df_fn = test_period+'_model_df'
if df_id != -1:
    print('drop_freq', df_id)
    agg_rsa_fn = agg_rsa_fn + '_drop_freq_' + str(df_id)
    model_df_fn = model_df_fn + '_drop_freq_' + str(df_id)
print(agg_rsa_fn)
fp = output_dir + agg_rsa_fn + '.csv'
model_df_fp = output_dir + model_df_fn + '.csv'

rsa_df = pd.read_csv(fp)
print(rsa_df.shape)

test_prefix = ''
if test_period == 'encoding_isi':
    test_prefix = 'prev_'

within_list_query = ('(session_' + test_period_str + ' == session_' + encoding_period + 
                     ') and (list_' + test_period_str + ' == list_' + encoding_period + ')')
if test_period == 'encoding':
    within_list_query += (' and (serialpos_' + test_period_str + 
                          ' > serialpos_' + encoding_period+')')
elif test_period in ['encoding_isi', 'encoding_end']: #no RepFR1 so can assume list length == 12
    within_list_query += (' and (' + test_prefix + 'serialpos_' + test_period_str + 
                          ' >= 7 and serialpos_' + encoding_period+' <= 6)')

within_list_rsa_df = rsa_df.query(within_list_query)

if test_period == 'distractor':
    cols = within_list_rsa_df.columns
    groupby_cols = [col for col in cols if col not in ['time_distractor', 'corr_z']]
    print(groupby_cols)
    #average over time
    within_list_rsa_df = within_list_rsa_df.groupby(
        groupby_cols, as_index=False).agg(
        {'corr_z': 'mean'})

change_na_cols = ['outpos', 'prev_outpos', 'prev_serialpos', 'prev_recalled', 'prev_category']
encoding_change_na_cols = [col+'_'+encoding_period for col in change_na_cols]
test_change_na_cols = [col+'_'+test_period_str for col in change_na_cols]
change_na_cols = encoding_change_na_cols + test_change_na_cols
change_na_cols = [col for col in change_na_cols if col in within_list_rsa_df.columns]
within_list_rsa_df[change_na_cols] = within_list_rsa_df[change_na_cols].replace(to_replace=[-999.0, 'NA'], value=np.nan)

if test_period != 'distractor':
    if exp == 'catFR1':
        within_list_rsa_df['same_category'] = (within_list_rsa_df['category_'+encoding_period] == 
                                               within_list_rsa_df[test_prefix+'category_'+test_period_str])
    within_list_rsa_df['serialpos_dist'] = (within_list_rsa_df['serialpos_'+encoding_period] - 
                                            within_list_rsa_df[test_prefix+'serialpos_'+test_period_str])
    within_list_rsa_df['abs_serialpos_dist'] = abs(within_list_rsa_df['serialpos_dist'])
    within_list_rsa_df['abs_serialpos_dist_center'] = within_list_rsa_df['abs_serialpos_dist'] - within_list_rsa_df['abs_serialpos_dist'].mean() #center is not in middle because there are more small distances
    within_list_rsa_df['abs_serialpos_dist_scale'] = within_list_rsa_df['abs_serialpos_dist_center'] / within_list_rsa_df['abs_serialpos_dist_center'].max()
    print(within_list_rsa_df[['abs_serialpos_dist', 'abs_serialpos_dist_scale']].drop_duplicates())
    within_list_rsa_df['pair_recalled'] = (within_list_rsa_df['recalled_'+encoding_period] + 
                                           within_list_rsa_df[test_prefix+'recalled_'+test_period_str])
    within_list_rsa_df['outpos_dist'] = (within_list_rsa_df['outpos_'+encoding_period] - 
                                         within_list_rsa_df[test_prefix+'outpos_'+test_period_str])
    within_list_rsa_df['abs_outpos_dist'] = abs(within_list_rsa_df['outpos_dist'])
    within_list_rsa_df['recall_neighbor'] = within_list_rsa_df['abs_outpos_dist'] == 1

if test_period == 'distractor':
    within_list_rsa_df['serialpos_center'] = 2 * (within_list_rsa_df['serialpos_'+encoding_period] - within_list_rsa_df['serialpos_'+encoding_period].mean())
    within_list_rsa_df['serialpos_scale'] = within_list_rsa_df['serialpos_center'] / within_list_rsa_df['serialpos_center'].max()
    print(within_list_rsa_df[['serialpos_'+encoding_period, 'serialpos_scale']])
within_list_rsa_df.rename(columns={'first_recalled_'+encoding_period: 'item_first',
                                   'recalled_'+encoding_period: 'item_recalled'},
                          inplace=True)
    

if test_period == 'encoding_isi':         
    print({'prev_recalled_'+test_period_str: 'item_before_isi_recalled'})
    within_list_rsa_df = within_list_rsa_df.rename(columns={'prev_recalled_'+test_period_str: 'item_before_isi_recalled'})
if test_period == 'encoding_end':
    within_list_rsa_df = within_list_rsa_df.rename(columns={'recalled_'+test_period_str: 'current_item_recalled'})

#fully balanced same category
if test_period in ['encoding_isi', 'encoding_end'] and exp == 'catFR1':
    within_list_rsa_df = within_list_rsa_df.query('(serialpos_encoding != 5 and abs_serialpos_dist > 2) or (abs_serialpos_dist > 3)')

print('n_subs: ', within_list_rsa_df['subject_'+encoding_period].nunique())

print(within_list_rsa_df['item_recalled'].unique())
    
boolean_cols = ['item_first', 'item_recalled', 'same_category', 'recall_neighbor', 'item_before_isi_recalled', 'current_item_recalled']
boolean_cols = [col for col in boolean_cols if col in within_list_rsa_df.columns]
for col in boolean_cols:
    within_list_rsa_df[col] = within_list_rsa_df[col].astype('boolean')
    
print(within_list_rsa_df.columns)
print(within_list_rsa_df[boolean_cols])
print(within_list_rsa_df['item_recalled'].unique())

within_list_rsa_df.to_csv(model_df_fp, index=False)
