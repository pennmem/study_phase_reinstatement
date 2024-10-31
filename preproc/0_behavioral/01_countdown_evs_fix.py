import cmlreaders as cml
import pandas as pd
import numpy as np
pd.options.mode.copy_on_write = True
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--experiment', type=str)
args = vars(parser.parse_args())
experiment = args['experiment']
    
scratch_dir = '/scratch/djh/study_phase_reinstatement/'
preproc_dir = scratch_dir + 'preproc_data/' + experiment + '/'
behavioral_preproc_dir = preproc_dir + 'behavioral/'

all_events = pd.read_csv(behavioral_preproc_dir+'events.csv')

preproc_events = pd.read_csv(behavioral_preproc_dir+'events.csv')
all_events = cml.CMLReader.load_events(subjects=preproc_events.subject.unique(),
                                       experiments=[experiment], 
                                              data_type='task_events')
#some countdown trials are missing list ids
if "RepFR" in experiment:
    all_events.loc[(all_events['type'] == "COUNTDOWN") & (all_events['list'] == -999), 'list'] = np.nan
    all_events['list'] = all_events.groupby(['subject', 'session'])['list'].bfill()
all_events = all_events[all_events['list'] > 0] # removing practice lists
all_events = all_events.reset_index()
print('# subjects:', all_events.subject.nunique())

if "RepFR" in experiment:
    countdown_evs = all_events.query('type == ["COUNTDOWN"] or (type == "WORD" and serialpos == 0)')
    countdown_diff_evs = countdown_evs
else:
    countdown_evs = all_events.query('type == ["COUNTDOWN_END", "COUNTDOWN_START"]').copy()

    #fix issue with countdown coming at end of list after list 1
    countdown_evs['type_occurrence'] = countdown_evs.groupby(['subject', 'session', 'list', 'type']).cumcount()

    #one subject had many restarts or unknown why other subjects have duplicates?
    countdown_evs['max_type_occurrence'] = countdown_evs.groupby(['subject', 'session', 'list'])['type_occurrence'].transform('max')
    countdown_evs['bad_list'] = ((countdown_evs['max_type_occurrence'] >= 2) | 
                                 (countdown_evs['eegfile'] == "") | countdown_evs['eegfile'].isna() | #no eegfile often means list cutoff
                                 ((countdown_evs['max_type_occurrence'] != 0) & (countdown_evs['list'] > 1)))
    countdown_evs['any_bad_list'] = countdown_evs.groupby(['subject', 'session', 'list'])['bad_list'].transform('max')

    sess_to_fix_df = countdown_evs[(countdown_evs['type_occurrence'] == 1) & (countdown_evs['list'] == 1)][['subject', 'session']].drop_duplicates()
    countdown_evs = countdown_evs.merge(sess_to_fix_df, how='left', indicator=True)
    countdown_evs['list'] = countdown_evs['list'].astype(int)
    countdown_evs['new_list'] = countdown_evs['list']
    countdown_evs.loc[((countdown_evs['type_occurrence'] == 1) & (countdown_evs['list'] == 1) & (countdown_evs['any_bad_list'] == False)) | # second occurrence of countdown in list 1
                      ((countdown_evs['_merge'] == 'both') & (countdown_evs['list'] != 1)), # bad session and list != 1
                     'new_list'] += 1
    countdown_evs = countdown_evs[['subject', 'session', 'list', 'type_occurrence', 'index', 'type', 'new_list', 'bad_list', 'any_bad_list']]

    fixed_evs = all_events.merge(countdown_evs, how='left')
    fixed_evs = fixed_evs.query('bad_list == False')
    fixed_evs.loc[~pd.isna(fixed_evs['new_list']), 'list'] = fixed_evs.loc[~pd.isna(fixed_evs['new_list']), 'new_list']
    fixed_evs['list'] = fixed_evs['list'].astype(int)
    countdown_diff_evs = fixed_evs.query('type == ["COUNTDOWN_END", "COUNTDOWN_START"]')

countdown_diff_evs['diff'] = countdown_diff_evs.groupby(['subject', 'session', 'list'])['mstime'].diff()
countdown_diff_evs['diff'] = countdown_diff_evs.groupby(['subject', 'session', 'list'])['diff'].bfill()

if 'RepFR' in experiment:
    print('incorrect countdown timing: ', countdown_diff_evs.query('diff < 3980 or diff > 10000').subject.unique())
    print(countdown_diff_evs.subject.nunique())
    countdown_diff_evs.query('(diff > 3980) and (diff < 10000)', inplace=True)
    print(countdown_diff_evs.subject.nunique())
else:
    print('incorrect countdown timing: ', countdown_diff_evs.query('diff < 10000').subject.unique())
    countdown_diff_evs.query('diff > 10000', inplace=True)
    #drop unnecessary columns
    countdown_diff_evs.drop(columns=['type_occurrence', 'new_list', 'bad_list', 'any_bad_list'], inplace=True)

countdown_diff_evs.to_csv(behavioral_preproc_dir+'countdown_events.csv', index=False)

diff_df = countdown_diff_evs.groupby(['subject', 'session']).agg({'diff': ['mean', 'std']})
diff_df.columns = ['diff_mean', 'diff_std']
diff_df = diff_df.reset_index()
diff_df['diff_mean_s'] = diff_df['diff_mean'] / 1000
diff_df['diff_std_s'] = diff_df['diff_std'] / 1000
print(diff_df.query('diff_std != 0 and diff_mean != 0').sort_values('diff_std_s', ascending=False)[0:20])