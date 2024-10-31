#!/bin/bash
#
#SBATCH --job-name=aggregate_rsa_drop_freq
#SBATCH --partition=RAM
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=2:00:00
#SBATCH --mem=15GB
#SBATCH --mail-type=END
#SBATCH --mail-user=djhalp@sas.upenn.edu
#SBATCH --output=slurm_aggregate_rsa_drop_freq_%A_%a.out

SRCDIR=$HOME/study_phase_reinstatement/preproc/

source activate /usr/global/miniconda/py310_23.1.0-1/envs/workshop_311

echo $EXP
echo $TP

python -u $SRCDIR/4_create_model_df.py --df_id $SLURM_ARRAY_TASK_ID --exp $EXP --test_period $TP