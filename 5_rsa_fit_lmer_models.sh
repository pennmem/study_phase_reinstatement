#!/bin/bash
#
#SBATCH --job-name=lmer3_rsa_models
#SBATCH --partition=RAM
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=5GB
#SBATCH --mail-type=END
#SBATCH --mail-user=djhalp@sas.upenn.edu
#SBATCH --output=lmerslurm_rsa_%A_%a.out

source activate r_env

SRCDIR=$HOME/study_phase_reinstatement_test3

Rscript --vanilla \
$SRCDIR/5_fit_rsa_lmer_models_job.R $SLURM_ARRAY_TASK_ID TRUE $EXP $TP TRUE 20 10 FALSE FALSE TRUE $WS $DF