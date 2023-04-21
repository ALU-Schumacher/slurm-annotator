#!/usr/bin/python3
import subprocess
import json
import os.path
import time
import json
import logging
import argparse
import glob

def get_job_list():
   """Return list of arc jobs in state INLRMS."""
   logging.debug('Getting list of arc jobs')
   jobs = []
   result = subprocess.run(['/sbin/arcctl', 'job', 'list' , '-s', 'INLRMS'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
   if result.returncode == 0:
      jobs = result.stdout.decode("utf-8").split()
   else:
      logging.error(result.stderr)
   return jobs


def get_harvesterid(job,config):
   """  
    retrieves harvester ID from _condor_stderr file name
    if the stderr file does not exists harvesterID is set to 0
   """
   name = glob.glob("{0}/{1}/_condor_stderr.*".format(config['WorkDir'],job))
   if name and "_" in name[0] and len(name[0].split("_")) > 3:
      return name[0].split("_")[-2]
   else:
      return 0 


def get_comment(job,config):
   """
      Return slurm job id and dict containing all keywords defined in the config file 
      and its corresponding info 
   """
   logging.debug('Creating comments for each arc job')
   comments = {}

   data = None
   my_dict = {}

   info_filename = "{0}{1}/{2}".format(config['WorkDir'],job,config['info_file'])
   ## check if info_file already exists and is complete 
   if os.path.isfile(info_filename) and not config['dry_run']:
      with open(info_filename) as f:
         my_dict = json.load(f)
      if sorted(list(my_dict.keys())) == sorted(config["keywords"]):
         return None, None

   ## ugly ad-hoc solution retrieve harvester ID from strerr file name
   if "harvesterID" in config["keywords"]:
      hid = get_harvesterid(job,config)
      if hid:
         my_dict["harvesterID"] = hid

   ## only try to retieve data from arcctl if a keyword is missing
   if sorted(list(my_dict.keys())) == sorted(config["keywords"]):
      return attr['localid'], my_dict

   try:
       attr = {}
       with open('{0}/job.{1}.local'.format(config['jobstatusDir'],job), 'r') as reader:
           data = reader.read()
   except:
       logging.error(".local file not found for Job: {0}".format(job))
   # create voms dict with all voms attributes
   for line in data.split('\n'):
       schar = line.find("=")
       k = line[:schar]
       v = line[schar+1:]
       if k not in attr.keys():
           attr[k]=v
   # select attributes by keywords from config 
   for key in config["keywords"]:
       if key in attr.keys():
           my_dict[key] = attr[key]
   return attr['localid'], my_dict


def upload_dict_to_job(comment,jobid):
   """
   uploads comment with pseudo json for each job id to slurm
   """
   #convert " -> ', since comment field does not allow " 
   nice_dict = json.dumps(comment)
   nice_dict = nice_dict.replace('"',"'")
   logging.debug('/bin/scontrol update JobId={0} comment="{1}"'.format(jobid, nice_dict))
   out, err = None,None
   result = subprocess.run(['/bin/scontrol', 'update', 'JobId={0}'.format(jobid), 
			    'comment="{0}"'.format(nice_dict)], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE
                          )
   if result.returncode:
      logging.error(result.stderr)
   return result.returncode


def upload_comments_all_jobs(jobs, config):
   """
   loops over all key value pairs of the comments dict, tries to upload the new comment
   and stores the comment into a json file in the WorkDir, such that upload is done
   only once
   """
   for job in jobs:
      jobid, comment = get_comment(job,config)
      if jobid == None or config['dry_run']:
         logging.debug("data {0} from arc job: {1} to slurm job {2}".format(job, jobid,comment))
         continue
      try:
         logging.info("Upload data {0} from arc job: {1} to slurm job {2}".format(job, jobid,comment))
         out = upload_dict_to_job(comment,jobid)
         if int(out) == 0:
            with open("{0}{1}/{2}".format(config['WorkDir'],job,config['info_file']), 'w') as f:
               json.dump(comment, f)
      except:
          logging.error("Could not write info file for job: ", job)


def main(config):
   """
   generates list of arc jobs, creates dict with jobids and new comments
   then uploads the pseudo json to slurm 
   """
   jobs = get_job_list()
   upload_comments_all_jobs(jobs, config)   
   logging.info('Successfully finished slurm-annotator run!')

if __name__ == "__main__":

   parser = argparse.ArgumentParser(description='Process some integers.')
   parser.add_argument('-d', '--dry-run', action='store_true', 
                       help='dry-run omits changes in slurm')
   parser.add_argument('-c', '--config', dest='config_file',
                       default='/etc/slurm-annotator/config.json',
                       help='specify a config file')   
   parser.add_argument('-l', '--log-file', dest='logfile',
                       default = None,
                       help='specify a log file')

   args = parser.parse_args()
   conf = {}
   try:
      with open(args.config_file, 'r') as f:
         conf = json.load(f)
   except:
      print("ERROR:: cannot read config file")
   config =  conf
   d_args = vars(args)
   for k, v in dict(d_args).items():
      if v is None:
         del d_args[k]
   config.update(d_args)
   logging.basicConfig(filename=config['logfile'], 
                       format='%(asctime)s - %(levelname)s - %(message)s', 
                       level=config['loglevel']
                       )
   logging.info('Successfully started slurm-annotator')

   while True:
      main(config)
      if config["dry_run"]:
          break
      else:
          time.sleep(config['frequency'])



