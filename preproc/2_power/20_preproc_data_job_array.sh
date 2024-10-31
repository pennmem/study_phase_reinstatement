#!/bin/bash
#
#SBATCH --job-name=slurm_preproc
#SBATCH --partition=RAM
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=2:00:00
#SBATCH --mem=70GB
#SBATCH --mail-type=END
#SBATCH --mail-user=djhalp@sas.upenn.edu
#SBATCH --output=slurm_preproc_%A_%a.out

SRCDIR=$HOME/study_phase_reinstatement/preproc/2_power

source activate /usr/global/miniconda/py310_23.1.0-1/envs/workshop_311

echo $EXP
echo $PERIOD
python -u $SRCDIR/20_preproc_data.py --row_id $SLURM_ARRAY_TASK_ID --exp $EXP --period $PERIOD