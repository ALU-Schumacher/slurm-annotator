#!/usr/bin/python3
import subprocess
import json
import os.path
import time
import json
import logging

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


def get_comment(job,config):
   """
   Return slurm job id and dict containing all keywords defined in the config file 
   and its corresponding info 
   """
   logging.debug('Creating comments for each arc job')
   comments = {}
   if os.path.isfile("{0}{1}/{2}".format(config['WorkDir'],job,config['info_file'])):
      return None, None   
   my_dict = {}
   try:
      attr = []
      result = subprocess.run(['/sbin/arcctl', 'job', 'attr' , job], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      if result.returncode == 0:
         attr = result.stdout.decode("utf-8").split('\n')
      else:
         logging.error(result.stderr)
      for a in attr:
         try:
            my_key = a.split(':', 1)[0].replace(" ","")
            my_value = a.split(':', 1)[1]
         except:
            continue
         if my_value.startswith(" "):
            my_value = my_value[1:]
         if my_key in config['keywords']:
            my_dict[my_key] = my_value
         if my_key == "localid":
            jobid = int(my_value)
      logging.debug(job, my_dict)
   except:
      logging.error("Attr infos could not be retrieved for job: ", job)
   return jobid, my_dict



def upload_dict_to_job(comment,jobid):
   """
   uploads comment with pseudo json for each job id to slurm
   """
   #convert " -> ', since comment field does not allow " 
   nice_dict = json.dumps(comment)
   nice_dict = nice_dict.replace('"',"'")
   logging.debug('/bin/scontrol update JobId={0} comment="{1}"'.format(jobid, nice_dict))
   out, err = None,None
   result = subprocess.run(['/bin/scontrol', 'update', 'JobId={0}'.format(jobid), 'comment="{0}"'.format(nice_dict)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
      if jobid == None:
         continue
      try:
         logging.info("Upload data {0} form arc job: {1} to slurm job {2}".format(job, jobid,comment))
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
   try:
      with open('/etc/slurm-annotator/config.json', 'r') as f:
         config = json.load(f)
   except:
      print("ERROR:: cannot read config file")
   logging.basicConfig(filename=config['logfile'], 
                       format='%(asctime)s - %(levelname)s - %(message)s', 
                       level=config['loglevel']
                       )
   logging.info('Successfully started slurm-annotator')
   while True:
      main(config)
      time.sleep(config['frequency'])



