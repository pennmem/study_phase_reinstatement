import numpy as np
from ptsa.data.filters import ResampleFilter, ButterworthFilter, MorletWaveletFilter
import cmlreaders as cml
import os
import pandas as pd
pd.options.mode.copy_on_write = True
import xarray as xr
import cf_xarray as cfxr
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--row_id', default=0, type=int)
parser.add_argument('--exp', default='catFR1', type=str)
parser.add_argument('--no_overwrite', action='store_true')
parser.add_argument('--period', type=str)
parser.add_argument('--scratch_dir', default='/scratch/djh/study_phase_reinstatement/', type=str)
args = vars(parser.parse_args())

LINEFILT = [58, 62]
FREQS = np.logspace(np.log10(3),np.log10(180), 8)
exp = args['exp']
period = args['period']
row_id = args['row_id']
                
pow_params = {
    # Timing chosen to match Kragel et al. (2021). Presumably this was used because it was the parameters initially used for Ezzyat et al. (2017) classification studies. Eventually start and end time reduced.
    'encoding': {
        'start_time': -0.5,
        'end_time': 2.1,
        'buf': 1.0,
        'ev_type': ['WORD'],
        'time_slice': slice(15, 1575)
    },
    'encoding_end': {
        'start_time': 1.1,
        'end_time': 1.6,
        'buf': 1.0,
        'ev_type': ['WORD']
    },
    'encoding_isi': {
        'start_time': -0.7, #min time is -.75
        'end_time': 0,
        'buf': 1.0,
        'ev_type': ['WORD']
    },
    'distractor': {
        'buf': 1.0,
        'start_time': -20.0,
        'end_time': 0.0,
        'powhz': 1.0,
        'ev_type': ['DISTRACT_END']
    },
    'countdown': {
        'buf': 1.0,
        'start_time': 0.0,
        'end_time': 10.0,
        'powhz': 1.0,
        'ev_type': ['COUNTDOWN_START']
    }
}

if exp == "RepFR1":
    pow_params['countdown'] = {
        'buf': 1.0,
        'start_time': 0.0,
        'end_time': 3.8,
        'powhz': 1.0,
        'ev_type': ['COUNTDOWN']
    }
    pow_params['distractor'] = {
        'buf': 1.0,
        'start_time': -7.0,
        'end_time': 0.0,
        'powhz': 1.0,
        'ev_type': ['REC_START']
    }
    pow_params['encoding'] = {
        'start_time': -0.5,
        'end_time': 2.1,
        'buf': 1.0,
        'ev_type': ['WORD'],
        'time_slice': slice(0, 750)
    }

ix = cml.CMLReader.get_data_index()
exp_ix = ix.query('experiment == @exp')

print(exp_ix.shape, 'total # sessions')
df_sess = exp_ix.iloc[args['row_id']]
print(df_sess['subject'])
scratch_dir = args['scratch_dir']

subject = df_sess['subject']
session = df_sess['session']

resamplerate = 1000
preproc_dir = scratch_dir + 'preproc_data/' + exp + '/'
power_preproc_dir = preproc_dir + 'power/'
behavioral_preproc_dir = preproc_dir + 'behavioral/'
pairs_preproc_dir = preproc_dir + 'pairs/'
raw_fp = power_preproc_dir + period + '/' + subject + '_' + str(session)
nc_fp = raw_fp + '.nc'

print(args['no_overwrite'])
if os.path.exists(nc_fp) and args['no_overwrite']:
    print(nc_fp + ' exists')
else:
    print(df_sess['subject'], df_sess['session'])
    ev_type = pow_params[period]['ev_type']
    montage = df_sess['montage']
    reader = cml.CMLReader(subject=df_sess['subject'], 
                           experiment=df_sess['experiment'], session=df_sess['session'],
                           localization=df_sess['localization'], montage=df_sess['montage'])
    if period == 'countdown':
        events = pd.read_csv(behavioral_preproc_dir+'countdown_events.csv')
    else:
        events = pd.read_csv(behavioral_preproc_dir+'events.csv')
    events.query('subject == @subject and session == @session', inplace=True)
    print(events.columns)
    
    buf = pow_params[period]['buf'] * 1000
    rel_start = pow_params[period]['start_time'] * 1000
    rel_stop = pow_params[period]['end_time'] * 1000
    #need to remove events without eeg first
    events.query('eegfile == eegfile and eegfile != ""', inplace=True)
    
    print(events.shape)  
    if (events.shape[1] == 0) or (events.shape[0] == 0):
        print('no events')
    else:
        #these columns screw up saving and don't need them for now
        print('preprocessing')
        drop_cols = ['stim_params', 'distractor']
        for col in drop_cols:
            if col in events.columns:
                events.drop(columns=col, inplace=True)
        events.query('type == @ev_type', inplace=True)
        
        #for saving as nc can't have columns with all NAs
        events.dropna(axis=1, how='all', inplace=True)
        #for saving as nc need to use int32
        events = events.astype({col: 'int32' for col in events.select_dtypes('int64').columns})
        events = events.astype({col: 'int32' for col in events.select_dtypes('bool').columns})
        # these columns are often all False so don't get read as boolean
        false_cols = ['is_stim', 'stim_list', 'answer_correct']
        for col in false_cols:
            if col in events.columns:
                events[col] = events[col].astype('int32')
        # other object cols don't get read as boolean
        object_cols = ['first_recalled']
        for col in object_cols:
            if col in events.columns:
                events[col] = events[col].astype('int32')
        
        print(events)
        # change NAs to be nc compatible
        change_na_cols = ['outpos', 'prev_outpos', 'prev_serialpos', 'prev_recalled', 'prev_category']
        for col in change_na_cols:
            if col in events.columns:
                na_value = -999
                if col == 'prev_category':
                    na_value = 'NA'
                events[col] = events[col].fillna(value=na_value)
        
        # need to drop cols for saving (too many calls screws up cfxr)
        drop_cols = ['is_stim', 'stim_list', 'phase', 'answer_correct', 'row_order', 'item_num', 'category_num', 'protocol', 'exp_version', 'prev_item', 'intrusion', 'msoffset'] #msoffset is always within 50ms...not sure what we could use it for
        if period != 'encoding_isi':
            drop_cols = drop_cols + ['prev_category', 'prev_recalled', 'prev_serialpos', 'prev_outpos']
        else:
            drop_cols = drop_cols + ['first_recalled', 'mstime'] #in theory we can get mstime back from eegoffset (or merging)
        if exp != 'RepFR1':
            drop_cols = drop_cols + ['rep_num']
        for col in drop_cols:
            if col in events.columns:
                events.drop(columns=col, inplace=True)
                
        # https://app.asana.com/0/search?q=R1216E&child=1159824042357163
        if subject == "R1216E" and session == 0:
            events['eegfile'] = "R1216E_FR1_0_15Sep16_2125" 
        
        pairs = pd.read_csv(pairs_preproc_dir+'pairs.csv')
        pairs.query('subject == @subject and montage == @montage', inplace=True)
        
        dat = reader.load_eeg(events=events,
                              rel_start=-buf+rel_start,
                              rel_stop=buf+rel_stop,
                              scheme=pairs).to_ptsa()
        dat = dat.astype(float) - dat.mean('time')
        print(dat.coords)

        # Notch Butterworth filter for 60Hz line noise:
        dat = ButterworthFilter(freq_range=LINEFILT, filt_type='stop', order=4).filter(timeseries=dat)

        dat = ResampleFilter(resamplerate=resamplerate).filter(timeseries=dat)
        dat = MorletWaveletFilter(freqs=FREQS, output='power',
            width=5, verbose=True).filter(timeseries=dat)
        dat.data = np.log10(dat.data)

        dat = dat.remove_buffer(duration=(buf / 1000))

        if period == 'encoding':
            dat = dat.sel(time=pow_params[period]['time_slice'])
        if period not in ['distractor', 'countdown']:
            dat_mean = dat.mean('time') # average over time
        else: 
            print('chunking time')
            times = np.arange(rel_start, rel_stop + (1000 / pow_params[period]['powhz']), 1000 / pow_params[period]['powhz'])
            dat_mean = dat.groupby_bins('time', times, labels=times[:-1]).mean()
            dat_mean = dat_mean.rename({'time_bins': 'time'})
            print(dat_mean)

        pow_stacked = dat_mean.stack(cf=("channel", "frequency"))
        print(pow_stacked.coords)
        
        pow_stacked_ds = pow_stacked.to_dataset(name='eeg')
        print(pow_stacked_ds.coords)
        encoded = cfxr.encode_multi_index_as_compress(pow_stacked_ds, idxnames=["event", "cf"])
        encoded.to_netcdf(nc_fp)
