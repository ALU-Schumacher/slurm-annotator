mkdir /etc/slurm-annotator
export annotator_dir=$PWD
ln -s $annotator_dir/config.json /etc/slurm-annotator/config.json
ln -s $annotator_dir/slurm-annotator.py /usr/bin/slurm-annotator
ln -s $annotator_dir/slurm-annotator.service /etc/systemd/system/slurm-annotator.service
