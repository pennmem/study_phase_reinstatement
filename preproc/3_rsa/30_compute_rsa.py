import os
import sys
sys.path.append('/home1/djhalp/study_phase_reinstatement/modules/')
import eeg_utils as eu
import xarray as xr
import numpy as np
import cmlreaders as cml
import argparse 
parser = argparse.ArgumentParser()
parser.add_argument('--row_id', default=0, type=int)
parser.add_argument('--exp', default='catFR1', type=str)
parser.add_argument('--test_period', default='distractor', type=str)
parser.add_argument('--encoding_period', default='encoding', type=str)
parser.add_argument('--no_overwrite', action='store_true')
parser.add_argument('--drop_freqs', action='store_true')
parser.add_argument('--scratch_dir', default='/scratch/djh/study_phase_reinstatement/', type=str)
args = vars(parser.parse_args())

exp = args['exp']
test_period = args['test_period']
encoding_period = args['encoding_period']
drop_freqs = args['drop_freqs']
scratch_dir = args['scratch_dir']

ix = cml.CMLReader.get_data_index()
exp_ix = ix.query('experiment == @exp')
print(exp_ix.shape)

df_sess = exp_ix.iloc[args['row_id']]

preproc_dir = scratch_dir + 'preproc_data/' + exp + '/'
power_preproc_dir = preproc_dir + 'power/'
rsa_preproc_dir = preproc_dir + 'rsa/'
behavioral_preproc_dir = preproc_dir + 'behavioral/'

test_preproc_fp = power_preproc_dir + test_period + '/' + df_sess['subject'] + '_' + str(df_sess['session']) + '.nc'
encoding_preproc_fp = power_preproc_dir + encoding_period + '/' + df_sess['subject'] + '_' + str(df_sess['session']) + '.nc'
output_fn = rsa_preproc_dir + test_period + '_' + encoding_period + '_' + df_sess['subject'] + '_' + str(df_sess['session'])
countdown_fp = power_preproc_dir + 'countdown' + '/' + df_sess['subject'] + '_' + str(df_sess['session']) + '.nc'
output_fp = output_fn + '.csv'
print('encoding', encoding_preproc_fp)
print('test', test_preproc_fp)
print(output_fp)

if ((not os.path.exists(output_fp)) or (not args['no_overwrite'])):
    print(test_preproc_fp, os.path.exists(test_preproc_fp))
    print(encoding_preproc_fp, os.path.exists(encoding_preproc_fp))
    if os.path.exists(test_preproc_fp) and os.path.exists(encoding_preproc_fp):
        countdown_pow_stacked_raw = eu.load_nc_cfxr(countdown_fp, idxnames=["event", "cf"])
        word_pow_stacked_raw = eu.load_nc_cfxr(encoding_preproc_fp, idxnames=["event", "cf"])
        word_z_pow_stacked_raw = eu.normalize_features(word_pow_stacked_raw, countdown_pow_stacked_raw)
        
        if test_period == encoding_period:
             test_z_pow_stacked = eu.set_event_names(word_z_pow_stacked_raw, encoding_period+'2', col='event', copy=True)  
        else:
            test_pow_stacked_raw = eu.load_nc_cfxr(test_preproc_fp, idxnames=["event", "cf"])
            test_z_pow_stacked_raw = eu.normalize_features(test_pow_stacked_raw, countdown_pow_stacked_raw)
            test_z_pow_stacked = eu.set_event_names(test_z_pow_stacked_raw, test_period, col='event')
        if test_period == 'distractor':
            test_z_pow_stacked = test_z_pow_stacked.rename({'time': 'time_'+test_period})
        word_z_pow_stacked = eu.set_event_names(word_z_pow_stacked_raw, encoding_period, col='event')
        
        print('word_z')
        print(word_z_pow_stacked)
        print('test_z')
        print(test_z_pow_stacked)
        print(test_z_pow_stacked.coords)
        if drop_freqs == True:
            freqs = word_z_pow_stacked.unstack('cf').frequency.data
            for drop_freq in range(len(freqs)):
                output_fp = output_fn + '_drop_freq_' + str(drop_freq) + '.csv'
                print(output_fp)
                if ((not os.path.exists(output_fp)) or (not args['no_overwrite'])):
                    mask = np.ones(len(freqs), dtype=bool)
                    mask[drop_freq] = False
                    use_freqs = freqs[mask]
                    word_freq_z_pow_stacked = word_z_pow_stacked.unstack('cf').sel(frequency=use_freqs).stack(cf=['channel', 'frequency'])
                    corr_arr = xr.corr(word_freq_z_pow_stacked, test_z_pow_stacked, dim='cf')
                    del word_freq_z_pow_stacked
                    corr_df = corr_arr.to_dataframe('corr')
                    if test_period == 'distractor':
                        corr_df = corr_df.reset_index(level='time_distractor')
                    corr_df = corr_df.reset_index(drop=True)
                    del corr_arr
                    corr_df['corr_z'] = np.arctanh(corr_df['corr'])
                    corr_df.to_csv(output_fp, index=False)
                    del corr_df                           
        else:
            corr_arr = xr.corr(word_z_pow_stacked, test_z_pow_stacked, dim='cf')
            print(corr_arr.coords)
            corr_df = corr_arr.to_dataframe(name='corr')
            if test_period == 'distractor':
                corr_df = corr_df.reset_index(level='time_distractor')
                print(corr_df.columns)
            corr_df = corr_df.reset_index(drop=True)
            print(corr_df.shape)
            print(corr_df.columns)
            corr_df['corr_z'] = np.arctanh(corr_df['corr'])
            corr_df.to_csv(output_fp, index=False)
    else:
        print('files dont exist')
else:
    print('already_done')