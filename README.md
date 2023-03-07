# slurm-annotator
service which addes additional info of slurm job into comment field

# installation
clone repo

cd into the slurm-annotator directory and execute
```
 source install
```
this creates all necessary softlinks, such that the service can be started with:
```
systemctl start slurm-annotator.service
```
