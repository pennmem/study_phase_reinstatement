import pandas as pd
import cmlreaders as cml
import seaborn as sns
import numpy as np
import argparse 
sns.set_context('talk')

parser = argparse.ArgumentParser()
parser.add_argument('--exp', default='catFR1', type=str)
args = vars(parser.parse_args())
exp = args['exp']

data_dir = '/scratch/djh/study_phase_reinstatement_test3/preproc_data/'+exp+'/'
if exp == 'RepFR1':
    test_period = 'distractor'
else:
    test_period = 'encoding_isi'
model_df = pd.read_csv(data_dir + test_period + '_model_df.csv')

n_session_df = model_df.groupby(['subject_encoding'], as_index=False).agg({'session_encoding': 'nunique'})
g = sns.displot(x='session_encoding', data=n_session_df, binwidth=1)
g.set(xlabel='# Sessions', ylabel='# Subjects', )
g.savefig('../figs/'+exp+'_n_sessions.pdf')

n_list_df = model_df.groupby(['subject_encoding', 'session_encoding'], as_index=False).agg(
    {'list_encoding': 'nunique'})

g = sns.displot(x='list_encoding', data=n_list_df, binwidth=1)
g.set(xlabel='# Lists')
g.savefig('../figs/'+exp+'_n_lists_per_session.pdf')

subs_used = model_df.subject_encoding.unique()
pairs_dir = data_dir + '/pairs/'
pairs = pd.read_csv(pairs_dir + 'pairs.csv')

pairs_df = pairs.query('subject in @subs_used')
montage_n_pairs_df = pairs_df.groupby(['subject', 'montage']).size().to_frame('n_pairs').reset_index()
sub_min_n_pairs_df = montage_n_pairs_df.groupby('subject', as_index=False).agg({'n_pairs': 'min'})

g = sns.displot(x='n_pairs', data=sub_min_n_pairs_df, binwidth=20)
g.set(xlabel='# Bipolar Pairs', ylabel='# Subjects')
g.savefig('../figs/'+exp+'_n_pairs_per_subject.pdf')

# Get localizations

exp_ix = cml.get_data_index().query('experiment == @exp')
sub_sess_df = model_df[['subject_encoding', 'session_encoding']].drop_duplicates()
sessions_used = exp_ix.merge(sub_sess_df, 
                             left_on=['subject', 'session'],
                             right_on=['subject_encoding', 'session_encoding'],
                             how='right')
montages_used = sessions_used.drop_duplicates(subset=['subject', 'montage', 'localization'])

localizations = []
montages_used = sessions_used.drop_duplicates(subset=['subject', 'montage', 'localization'])
for (subject, experiment, montage, localization), df_montage in montages_used.groupby(['subject', 'experiment', 'montage', 'localization']):
    reader = cml.CMLReader(subject=subject, experiment=experiment, localization=localization, montage=montage)
    try:
        localization_df = reader.load('localization')
        localization_df['subject'] = subject
        localization_df['experiment'] = experiment
        localization_df['montage'] = montage
        localization_df['localization'] = localization
        localizations.append(localization_df)
    except:
        # print(montage_df['subject'])
        continue
    

localizations_df = pd.concat(localizations).loc['pairs'].reset_index()
localizations_df['label'] = localizations_df['index'].apply(lambda r: r[0] + '-' + r[1])
pair_localizations = pairs_df.merge(localizations_df, on=['subject', 'montage', 'label'], how='left')

all_atlases = ['stein.region', 'das.region', 'atlases.mtl', 'atlases.whole_brain', 'wb.region', 'mni.region', 'atlases.dk', 'dk.region', 
    'ind.corrected.region', 'mat.ind.corrected.region', 'ind.snap.region', 'mat.ind.snap.region', 'ind.dural.region', 'mat.ind.dural.region', 
    'ind.region', 'mat.ind.region', 'avg.corrected.region', 'avg.mat.corrected.region', 'avg.snap.region', 'avg.mat.snap.region', 'avg.dural.region',
    'avg.mat.dural.region', 'avg.region', 'avg.mat.region', 'mat.tal.region']
atlases = [atlas for atlas in all_atlases if atlas in pair_localizations.columns]

pair_localizations[atlases] = pair_localizations[atlases].apply(lambda x: x.astype(str).str.lower().str.strip())
pair_localizations[atlases] = pair_localizations[atlases].apply(lambda x: x.astype(str).str.lower().str.strip('"'))
pair_localizations[atlases] = pair_localizations[atlases].replace(to_replace=['nan', 'unknown', 'none', '[]', 'left tc', '', ' '], value=np.nan)

#try to fill NAs in order of priority in all_atlases
pair_localizations['subregion_original'] = pair_localizations['stein.region']
for atlas in atlases:
    pair_localizations['subregion_original'] = pair_localizations['subregion_original'].fillna(pair_localizations[atlas])
    
print('missing localizations')
print(pair_localizations.query('subregion_original != subregion_original').shape)
print(pair_localizations.query('subregion_original != subregion_original').groupby('subject').size())
pair_localizations.query('subregion_original == subregion_original', inplace=True)

regionalization_df = pd.read_csv('regionalization_df.csv')

pair_localizations_merge = pair_localizations.merge(regionalization_df, 
                                                    how='left', indicator=True)
missing_labels = pair_localizations_merge.query('_merge != "both"')
print('missing matched localization: ', missing_labels.shape, missing_labels.subject.nunique())

sub_elec_region_df = pair_localizations_merge.groupby(['subject', 'region']).size().to_frame('n_region_electrodes').reset_index()

n_subs_elec_region_df = sub_elec_region_df.query(
    'n_region_electrodes > 0 and region != ["Other", "Other Cortex", "Subcortical", "Occipital"]'
                                                ).groupby('region', as_index=False).agg({'subject': 'nunique'})

n_subs_elec_region_df['region'] = n_subs_elec_region_df['region'].replace(to_replace={'Cingulate': 'CC',
                                                    'Other Temporal': 'TL',
                                                    'Parietal': 'PL'
                                                   })

g = sns.catplot(x="region", y="subject",
                 data=n_subs_elec_region_df,
                 kind="bar")
g.set(xlabel='Regions', ylabel='# Subjects')
g.set_xticklabels(rotation=90)
g.refline(y=sub_elec_region_df.subject.nunique(), label='Total Subjects')
g.savefig('../figs/'+exp+'_subject_electrode_region.pdf')