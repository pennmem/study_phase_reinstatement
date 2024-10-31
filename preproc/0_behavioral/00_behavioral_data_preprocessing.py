import cmlreaders as cml
import pandas as pd
import numpy as np
pd.options.mode.copy_on_write = True
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--experiment', type=str)
args = vars(parser.parse_args())
experiment = args['experiment']

if "RepFR" in experiment:
    n_list_items = 27
    mstime_diff_min = 1300
    mstime_diff_max = 2800
else:
    n_list_items = 12
    mstime_diff_min = 2350
    mstime_diff_max = 2800
rare_item_min_subjects = 6
    
scratch_dir = '/scratch/djh/study_phase_reinstatement/'
preproc_dir = scratch_dir + 'preproc_data/' + experiment + '/'
behavioral_preproc_dir = preproc_dir + 'behavioral/'

if "catFR" in experiment:
    use_subs = cml.get_data_index().query('experiment == @experiment and system_version != 4').subject.unique()
else:
    use_subs = None

all_events = cml.CMLReader.load_events(subjects=use_subs, experiments=[experiment], 
                                              data_type='task_events')

events = all_events.query('type == ["WORD", "DISTRACT_END", "REC_START", "REC_WORD", "COUNTDOWN", "COUNTDOWN_START", "COUNTDOWN_END"]')

#some countdown trials are missing list ids
if "RepFR" in experiment:
    events.loc[(events['type'] == "COUNTDOWN") & (events['list'] == -999), 'list'] = np.nan
    events['list'] = events.groupby(['subject', 'session'])['list'].bfill()
    
events = events[events['list'] > 0] # removing practice lists
events['subject'] = events['subject'].astype(str)
if 'item' not in events.columns:
    events.rename(columns={'item_name': 'item'}, inplace=True)
# if 'trial' not in events.columns:
#     events.rename(columns={'list': 'trial'}, inplace=True)

events['item'] = events.item.str.strip().str.lower()
events.loc[events['item'] == 'axe', 'item'] = 'ax'
if 'catFR' in experiment:
    events['category'] = events.category.str.strip().str.lower()

bad_subs = []
bad_lists = []
#drop subjects with no recalls
word_rec_evs = events.query('type == ["WORD", "REC_WORD"]')
n_types = word_rec_evs.groupby('subject', as_index=False).agg({'type': 'nunique'})
no_recall_subs = n_types.query('type != 2')
bad_subs += no_recall_subs.subject.unique().tolist()
print('no recalls', no_recall_subs.subject.unique().tolist())

#drop subjects with rare_items (i.e. spanish) -- only need to do this when category matters
if "catFR" in experiment:
    word_evs = events.query('type == ["WORD"]')
    item_sub_df = word_evs.groupby(['item'], as_index=False).agg({'subject': 'nunique'})
    rare_items = item_sub_df.query('subject < @rare_item_min_subjects').item.unique()
    bad_subs += word_evs.query('item in @rare_items').subject.unique().tolist()
    print('rare items', word_evs.query('item in @rare_items').subject.unique().tolist())

#only stanford subject so remove to be safe
bad_subs += ['R1696L']

print('unique subjects', events.subject.nunique())
print('unique sessions', events.groupby(['subject', 'session']).ngroups)

bad_lists.append(events.query('subject in @bad_subs')[['subject', 'session', 'list']])
events.query('subject not in @bad_subs', inplace=True)

print('removing all bad subjects')

print('unique subjects', events.subject.nunique())
print('unique sessions', events.groupby(['subject', 'session']).ngroups)

#removing subjects who were presented with the same word multiple times (probably repeated data)
events['rep_num'] = events.groupby(['subject', 'session', 'list', 'type', 'item']).cumcount() + 1
word_evs = events.query('type == "WORD"')
repeat_events = word_evs.query('rep_num > 1')
if "RepFR" not in experiment:
    # bad_subs += repeat_events.subject.unique().tolist() 
    bad_lists.append(repeat_events[['subject', 'session', 'list']].drop_duplicates())
    print('too many pres', repeat_events.subject.unique().tolist())

#drop subjects with messed up recalls
rec_evs = events.query('type == "REC_WORD"')
joint_evs = word_evs.merge(rec_evs[['subject', 'session', 'list', 'item']], how='left', indicator=True)
incorrect_recalled_columns = joint_evs.query('(recalled == 1 and _merge != "both") or (recalled == 0 and _merge == "both")')
bad_lists.append(incorrect_recalled_columns[['subject', 'session', 'list']].drop_duplicates())
print('messed up recalls', incorrect_recalled_columns.subject.unique().tolist())

# drop lists without the typical number of items
# almost always the last list in a session (because subjects get tired) so don't need to drop the whole session
n_list_pres = word_evs.groupby(['subject', 'session', 'list'], as_index=False).size()
wrong_length_lists = n_list_pres.query('size != @n_list_items')[['subject', 'session', 'list']].drop_duplicates()
print('too many items per list', wrong_length_lists.subject.unique())
bad_lists.append(wrong_length_lists)

# lists with timing issues
# this is probably just a glitch, don't need to remove the whole subject
word_evs[['mstime_diff']] = word_evs.groupby(['subject', 'session', 'list'])[['mstime']].diff(periods=1)
timing_issues = word_evs.query('mstime_diff > @mstime_diff_max or mstime_diff < @mstime_diff_min')[['subject', 'session', 'list']].drop_duplicates()
print('lists with timing issues', timing_issues.subject.unique())
bad_lists.append(timing_issues)
# print(word_evs.query('mstime_diff > @mstime_diff_max or mstime_diff < @mstime_diff_min'))

#drop lists with repeated encoding periods -- in this case drop both
word_rec_evs['duplicate_list_item_serialpos'] = word_rec_evs.duplicated(subset=['subject', 'list', 'serialpos', 'item', 'type'], keep=False)
# count how many are duplicated to make sure its the full list
duplicates_df = word_rec_evs.groupby(['subject', 'session', 'list', 'type'], as_index=False).agg({'duplicate_list_item_serialpos': 'sum', 'item': 'count'})
full_duplicate_list_types = duplicates_df.query('duplicate_list_item_serialpos == item')
full_duplicate_list_types['n_types'] = full_duplicate_list_types.groupby(['subject', 'session', 'list'])['type'].transform('nunique')
# if only encoding is duplicated then REC_WORD will not show up as duplicated
duplicated_encoding = full_duplicate_list_types.query('type == "WORD" and n_types == 1')
dup_encoding_lists = duplicated_encoding[['subject', 'session', 'list']].drop_duplicates()
print('duplicated encoding', dup_encoding_lists.subject.unique())
bad_lists.append(dup_encoding_lists)

# Some data is completely duplicated -- in this case, keep one of them
word_rec_evs['duplicate_list_item_serialpos'] = word_rec_evs.duplicated(subset=['subject', 'list', 'serialpos', 'item', 'type']) # keep first occurrence
duplicates_df = word_rec_evs.groupby(['subject', 'session', 'list', 'type'], as_index=False).agg({'duplicate_list_item_serialpos': 'sum', 'item': 'count'})
full_duplicate_list_types = duplicates_df.query('duplicate_list_item_serialpos == item')
full_duplicate_list_types['n_types'] = full_duplicate_list_types.groupby(['subject', 'session', 'list'])['type'].transform('nunique')
true_duplicates = full_duplicate_list_types.query('type == "WORD" and n_types == 2') 

dup_lists = true_duplicates[['subject', 'session', 'list']].drop_duplicates()
print('duplicated data', dup_lists.subject.unique())
bad_lists.append(dup_lists)

# subjects with clear eegoffset errors -- likely to be errors in the experiment timing, recall accuracy
# need to fix here because error is often with REC_WORDS not corresponding to the correct list etc.
task_events = events.query('type == ["WORD", "REC_WORD"] and eegfile != "" and eegoffset != -1')
task_events['eegoffset_diff'] = task_events.groupby('eegfile')['eegoffset'].diff()
eegoffset_errors = task_events.query('eegoffset_diff < 0')
eegoffset_error_lists = eegoffset_errors[['subject', 'session', 'list']].drop_duplicates()
bad_lists.append(eegoffset_error_lists)
print('offset errors', eegoffset_error_lists.subject.unique())

bad_lists_df = pd.concat(bad_lists).drop_duplicates()
print(bad_lists_df)
print(bad_lists_df.subject.unique())

events = events.merge(bad_lists_df, how='left', indicator=True)
print(events.query('_merge == "both"'))
events = events.query('_merge != "both"').drop(columns='_merge')
bad_lists_df.to_csv(experiment+'_bad_lists_df.csv', index=False)

print('unique subjects', events.subject.nunique())
print('unique sessions', events.groupby(['subject', 'session']).ngroups)

#Read in fixed lists from before to make sure we don't add new subjects
ssl = pd.read_csv(experiment+'_subj_sess_list.csv')
events = events.merge(ssl)

print('merging with old subject list')
print('unique subjects', events.subject.nunique())
print('unique sessions', events.groupby(['subject', 'session']).ngroups)

events = events.assign(row_order=range(len(events)))
word_evs = events.query('type == "WORD"')
rec_evs = events.query('type == "REC_WORD"')
rec_evs['recall_repeat'] = rec_evs.duplicated(subset=['subject', 'session', 'list', 'item'])
rec_evs['outpos'] = rec_evs.groupby(['subject', 'session', 'list']).cumcount() + 1
rec_evs_no_repeats = rec_evs.query('recall_repeat == False') # make sure the first time recalled is the one matched with encoding
word_evs = word_evs.merge(rec_evs_no_repeats[['subject', 'session', 'list', 'item', 'outpos']], how='left')
word_evs['first_recalled'] = word_evs['outpos'] == 1

word_evs[['prev_item', 'prev_serialpos', 'prev_recalled', 'prev_outpos']] = word_evs.groupby(['subject', 'session', 'list'])[['item', 'serialpos', 'recalled', 'outpos']].shift()
if experiment == 'catFR1':
    word_evs[['prev_category']] = word_evs.groupby(['subject', 'session', 'list'])[['category']].shift()

other_evs = events.query('type != ["WORD", "REC_WORD"]')
events = pd.concat([word_evs, rec_evs, other_evs])
events.sort_values('row_order', inplace=True)
print(word_evs)

events.to_csv(behavioral_preproc_dir+'events.csv', index=False)

