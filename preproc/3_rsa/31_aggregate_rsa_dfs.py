import cmlreaders as cml
import os
import pandas as pd
pd.options.mode.copy_on_write = True
import numpy as np
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--df_id', default=-1, type=int)
parser.add_argument('--exp', default='catFR1', type=str)
parser.add_argument('--test_period', default='encoding_isi', type=str)
args = vars(parser.parse_args())

df_id = args['df_id']
exp = args['exp']
test_period = args['test_period']
ix = cml.CMLReader.get_data_index()
exp_ix = ix.query('experiment == @exp')

#collect results
mean_item_item_corr_dfs = []
scratch_dir = '/scratch/djh/study_phase_reinstatement/'
output_dir = scratch_dir + 'preproc_data/' + exp + '/'
# scratch_dir = '../'
encoding_period = 'encoding'

test_period_str = test_period
if test_period == 'encoding':
    test_period_str = 'encoding2'

aggregate_rsa_fn = test_period + '_' + encoding_period + '_raw_item_corr_df'
if df_id != -1:
    print('drop_freq', df_id)
    aggregate_rsa_fn = aggregate_rsa_fn + '_drop_freq_' + str(df_id)
aggregate_rsa_fp = output_dir + aggregate_rsa_fn + '.csv'
rsa_dfs = []
for (subject, session), df_sess in exp_ix.groupby(['subject', 'session']):
    sess_fn = test_period + '_' + encoding_period + '_' + subject + '_' + str(session)
    if df_id != -1:
        sess_fn = sess_fn + '_drop_freq_' + str(df_id)
    sess_fp = output_dir + 'rsa/' + sess_fn + '.csv'
    print(sess_fp)
    if not os.path.exists(sess_fp):
        print('missing')
        continue

    print(subject, session)

    rsa_df = pd.read_csv(sess_fp)
    
    # reducing columns for memory size
    cols_to_keep = ['subject_'+encoding_period, 'list_'+test_period_str, 'session_'+test_period_str, 
                    'serialpos_'+test_period_str, 'item_'+encoding_period, 'recalled_'+encoding_period,
                    'first_recalled_'+encoding_period,
                    'session_'+encoding_period, 'list_'+encoding_period, 'serialpos_'+encoding_period]
    outpos_cols = ['outpos_'+encoding_period, 'outpos_'+test_period_str]
    for col in outpos_cols: #if session has no recalls, this column will be all NA and get dropped earlier
        if col in rsa_df.columns:
            cols_to_keep += [col]
    if 'distractor' in test_period:
        cols_to_keep = cols_to_keep + ['time_'+test_period_str]
    else:
        cols_to_keep = cols_to_keep + ['item_'+test_period_str]
    if 'encoding' in test_period:
        cols_to_keep = cols_to_keep + ['recalled_'+test_period_str]
    if test_period == 'encoding_isi':
        cols_to_keep += ['prev_recalled_'+test_period_str, 'prev_serialpos_'+test_period_str]
        if 'prev_outpos_'+test_period_str in rsa_df.columns:
            cols_to_keep += ['prev_outpos_'+test_period_str] #if session has no recalls, this column will be all NA and get dropped earlier
    if exp == 'catFR1':
        cols_to_keep = cols_to_keep + ['category_'+encoding_period, 'category_'+test_period_str]
        if test_period == 'encoding_isi':
            cols_to_keep += ['prev_category_'+test_period_str]
    
    rsa_size_df = rsa_df.groupby(cols_to_keep).size().to_frame('size')
    assert rsa_size_df.query('size != 1').shape[0] == 0
    rsa_df = rsa_df[cols_to_keep + ['corr_z']]
    rsa_dfs.append(rsa_df)
                          
aggregate_rsa_df = pd.concat(rsa_dfs)

aggregate_rsa_df.to_csv(aggregate_rsa_fp, index=False)