# Slurm-annotator
Slurm-annotator is a small service which addes additional info of slurm job into comment field.
The current implementation retrieves information from an ARC-CE which submits jobs to the slurm-cluster the additional infromation can be specified in the config file.

# Configuration

The default config file is predefined as follows:
```
{
  "frequency": 30,
  "keywords": [
    "subject",
    "voms",
    "headnode"
  ],
  "WorkDir": "/pool_home/arc6/session/",
  "info_file": "job_info.json",
  "logfile": "/var/log/slurm-annotator/slurm-annotator.log",
  "loglevel": "INFO"
}
```
The frequency is specified in seconds. The default setting is checking ARC every 30 seconds for new jobs. The keyword specifies, which ARC job info should be forwarded to the slurm comment field (here: subject, voms and headnode). More details below in the section [ARC job attributes](#arc-job-attributes).

In order to reduce the load on the slurm scheduler the comment field is only adjusted once. In order to ensure this, an info_file is written in the mounted WorkDir of each ARC job, if the comment field was successfully updated. If the slurm-annotator finds the info_file it will not try to adjust the comment field again.

The loglevel and the path and name of the logfile can be specified in the config file as well. 

# Installation
## Requirements:
- python3
- git
- slurm v21 or newer
- arc v6.17 or newer

## Manual Installation 
Clone the repository:

```
git clone https://github.com/ALU-Schumacher/slurm-annotator.git
```

Change directory into the slurm-annotator directory and execute
```
 source install.sh
```
This script creates all necessary softlinks, such that the service can be started with:

```
systemctl start slurm-annotator.service
```

## Uninstall
Change directory into the slurm-annotator directory and execute
```
 source uninstall.sh
```
The uninstall script will remove the links and asks you if you would like to remove the directory with the config file and the directory with the log file.

## Example for a minimal installation with puppet:

Adjust the **$installdir** to your needs and add the following class to your profil:
```
class slurm_annotator (
  $confdir                 = '/etc/slurm-annotator',
  $logdir                  = '/var/log/slurm-annotator',
  $installdir              = '<put the prefered directory here>',
){

  file { $confdir :
     ensure => directory,
     owner   => "root",
     group  => "root",
     mode   => "755",
  }

  file { $logdir :
     ensure => directory,
     owner   => "root",
     group  => "root",
     mode   => "755",
  }

  vcsrepo { $installdir:
    ensure   => latest,
    provider => git,
    source   => 'https://github.com/ALU-Schumacher/slurm-annotator.git',
    revision => 'main',
    user     => root,
  }

  file {  "${confdir}/config.json":
   ensure  => link,
   target  => "${installdir}/config.json",
  }

  file {  "/usr/bin/slurm-annotator":
   ensure  => link,
   target  => "${installdir}/slurm-annotator.py",
  }

  file {  "/etc/systemd/system/slurm-annotator.service":
   ensure  => link,
   target  => "${installdir}/slurm-annotator.service",
  }

  service { 'slurm-annotator':
    ensure     => running,
    enable     => true,
    hasstatus  => true,
    hasrestart => true,
  }
}

```

# ARC job attributes

The attribute of an ARC job can beretrieved by `arcctl job attr <job ID>`.
An example of a generalized grid job can be found below:

```
arcctl job attr XXXXXXXXXXXXXXXXXX
diskspace                       : 0
argscode                        : 0
lifetime                        : 604800
sessiondir                      : /pool_home/arc6/session/XXXXXXXXXXXXXXXXXX
clientname                      : <ip>:<port>
subject                         : /DC=ch/DC=cern/OU=Organic Units ...
globalurl                       : gsiftp://arc.<domain>:<port>/jobs/XXXXXXXXXXXXXXXXXX
headhost                        : arc.<domain>
priority                        : 50
headnode                        : gsiftp://arc.<domain>:<port>/jobs
freestagein                     : no
delegexpiretime                 : 20230314000058Z
dryrun                          : no
globalid                        : gsiftp://arc.<domain>:<port>//jobs/XXXXXXXXXXXXXXXXXX
downloads                       : 0
args                            : runpilot2-wrapper.sh ...
jobname                         : arc_pilot
interface                       : org.nordugrid.gridftpjob
lrms                            : SLURM
delegationid                    : xxxxxxxxx
localid                         : 4234634
mapped_account                  : atlxxx
voms                            : /atlas/Role=test
queue                           : grid_queue
transfershare                   : _default
uploads                         : 0
starttime                       : 20230310005449Z
rerun                           : 0
```
By adding any of the keywords above to the slurm-annotator config file to the "keywords" list, it the given key:value pair will be added to the slurm comment field. 


# Example slurm job

Listing the detailed job info of a slurm job, after annotating the commend field with the default settings (`"keywords": ["subject", "voms", "headnode"]`) would looks as follows:

```
scontrol show job 4234634
JobId=4234634 JobName=arc_pilot
   UserId=atlxxx(1234) GroupId=atlxxx(5678) MCS_label=N/A
   Priority=1 Nice=50 Account=atlxxx QOS=normal
   ... 
   Comment="{'subject': '/DC=ch/DC=cern/OU=Organic Units ...', 
             'headnode': 'gsiftp://arc.<domain>:<port>/jobs', 
             'voms': '/atlas/Role=test'}" 
   ...
```
Since slurm does not allow to put double quote into the comment field, the keys and the values are placed in single quotes. If you would like to extract the comment field as a json, you need to replace the single quotes first.
