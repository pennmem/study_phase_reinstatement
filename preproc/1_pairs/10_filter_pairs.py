import cmlreaders as cml
import numpy as np
import pandas as pd
pd.options.mode.copy_on_write = True
import argparse 

parser = argparse.ArgumentParser()
parser.add_argument('--exp', default='catFR1', type=str)
parser.add_argument('--scratch_dir', default='/scratch/djh/study_phase_reinstatement/', type=str)
args = vars(parser.parse_args())

scratch_dir = args['scratch_dir']
exp = args['exp']

preproc_dir = scratch_dir + 'preproc_data/' + exp + '/'
pairs_preproc_dir = preproc_dir + 'pairs/'

ix = cml.get_data_index()
exp_ix = ix.query('experiment == @exp')

distance_threshold = 25
atlas = 'vox'
loc_cols = [atlas + '.x', atlas + '.y', atlas + '.z']

contacts_dfs = []
pairs_dfs = []
contacts_error_dfs = []
pairs_error_dfs = []
ec_error_dfs = []

for (subject, experiment, montage, localization), df_montage in exp_ix.groupby(['subject', 'experiment', 'montage', 'localization']):
    has_contacts = False
    reader = cml.CMLReader(subject=subject, experiment=experiment, montage=montage, localization=localization)
    try:
        contacts = reader.load("contacts")
        contacts['subject'] = subject
        contacts['experiment'] = experiment
        contacts['montage'] = montage
        contacts['localization'] = localization
        contacts_dfs.append(contacts)
    except:
        contacts_error_dfs.append({'subject': subject, 'experiment': experiment, 'montage': montage, 'localization': localization})
    
    try:
        pairs = reader.load("pairs")
        pairs['subject'] = subject
        pairs['experiment'] = experiment
        pairs['montage'] = montage
        pairs['localization'] = localization
        pairs_dfs.append(pairs)
    except:
        pairs_error_dfs.append({'subject': subject, 'experiment': experiment, 'montage': montage, 'localization': localization})
        
pairs_df = pd.concat(pairs_dfs)
contacts_df = pd.concat(contacts_dfs)

print('pairs: ', pairs_df.shape, pairs_df.subject.nunique())

# exclude micros, pairs with mismatching types (don't think this ever happens) and missing types
pairs_df.query('(type_1 != "uD") and (type_1 == type_1) and (type_1 == type_2)', inplace=True)
print('excluding micros: ', pairs_df.shape, pairs_df.subject.nunique())

print('contacts: ', contacts_df.shape, contacts_df.subject.nunique())
# requiring distance to be there
contacts_df.query('((`vox.x` == `vox.x`) and (`vox.y` == `vox.y`) and (`vox.z` == `vox.z`))', inplace=True)
print('excluding missing info: ', contacts_df.shape, contacts_df.subject.nunique())

contact_locs = contacts_df[['subject', 'experiment', 'montage', 'localization', 'contact', 'label']+loc_cols]
contact_locs.rename(columns={'contact': 'contact_ind'}, inplace=True)
contact_locs[loc_cols] = contact_locs[loc_cols].astype(float)
        
schemes_df = pairs_df.merge(contact_locs, #how='left', #only include pairs that are in contacts
                     left_on=['subject', 'experiment', 'montage', 'localization', 'contact_1'], 
                     right_on=['subject', 'experiment', 'montage', 'localization', 'contact_ind'], suffixes=("", "_1")
                            ).merge(contact_locs, # how='left', 
                                    left_on=['subject', 'experiment', 'montage', 'localization', 'contact_2'], 
                                    right_on=['subject', 'experiment', 'montage', 'localization', 'contact_ind'], suffixes=("", "_2"))
print('contacts merge: ', schemes_df.shape, schemes_df.subject.nunique())

schemes_df['dist'] = np.linalg.norm(schemes_df[[col + '_1' for col in loc_cols]].values - schemes_df[[col + '_2' for col in loc_cols]].values,
                   axis=1)

schemes_df['label_len'] = schemes_df['label'].str.split('-').apply(len)
weird_label_pairs = schemes_df.query('label_len > 2') # some pairs have weird labels
weird_label_pairs.dist.max() # these are all fine
print('weird_label_pairs: ', weird_label_pairs.shape, weird_label_pairs.subject.nunique())

schemes_df2 = schemes_df.query('label_len == 2')
schemes_df2[['label_pairs_1', 'label_pairs_2']] = schemes_df2['label'].str.split('-', expand=True)
schemes_df2.query('(label_1 == label_pairs_1) and (label_2 == label_pairs_2)', inplace=True) # mismatch between contacts and pairs
print('mismatch labels: ', schemes_df2.shape, schemes_df2.subject.nunique())

schemes_df2['label_pairs_num_1'] = schemes_df2['label_pairs_1'].str.extract(r'(\d+$)')
schemes_df2['label_pairs_num_2'] = schemes_df2['label_pairs_2'].str.extract(r'(\d+$)')
schemes_df2['label_pairs_num_dist'] = abs(schemes_df2['label_pairs_num_1'].astype(int) - 
                                          schemes_df2['label_pairs_num_2'].astype(int))
schemes_df2.query('label_pairs_num_dist == 1 or (type_1 != "D")', inplace=True) # exclude non-neighboring depth pairs
print('label distance: ', schemes_df2.shape, schemes_df2.subject.nunique())

schemes_df2.query('dist < @distance_threshold', inplace=True) # exclude pairs more than 25 mm apart
print('actual distance: ', schemes_df2.shape, schemes_df2.subject.nunique())

final_schemes_df = pd.concat([schemes_df2, weird_label_pairs])
print('final: ', final_schemes_df.shape, final_schemes_df.subject.nunique())

final_schemes_df['n_contacts'] = final_schemes_df.groupby(['subject', 'montage'])['label'].transform('count')
final_schemes_df.query('n_contacts >= 10', inplace=True)

print(final_schemes_df.groupby(['subject', 'montage']).size().to_frame('n').sort_values('n'))
final_schemes_df.to_csv(pairs_preproc_dir+'pairs.csv', index=False)