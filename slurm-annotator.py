#!/usr/bin/env python
import commands
import json
import os.path
import time
import json

def get_job_list():
   """Return list of arc jobs in state INLRMS."""
   logging.debug('Getting list of arc jobs')
   jobs_text = commands.getstatusoutput('/sbin/arcctl job list -s INLRMS')[1]
   jobs = []
   for j in jobs_text.split('\n'):
      if "ERROR" in j:
         continue
      jobs.append(j)
   return jobs


def create_comments_dict(jobs,config):
   """
   Return dict with slurm job ids as keys and pseudo json containing all keywords 
   and its corresponding info as comment string as value
   """
   logging.debug('Creating comments for each arc job')
   comments = {}
   for job in jobs:
      if os.path.isfile("{0}{1}/{2}".format(config['WorkDir'],job,config['info_file'])):
         continue
      my_dict = {}
      try:
         job_info = commands.getstatusoutput('/sbin/arcctl job attr {0}'.format(job))[1]
         attr = job_info.split("\n")
         for a in attr:
            my_key = a.split(':', 1)[0].replace(" ","")
            my_value = a.split(':', 1)[1]
            if my_value.startswith(" "):
               my_value = my_value[1:]
            if my_key in config['keywords']:
               my_dict[my_key] = my_value
            if my_key == "localid":
               jobid = int(my_value)
         logging.debug(job, my_dict)
         comments[jobid] = my_dict
      except:
          logging.error("Attr infos could not be retrieved for job: ", job)
   return comments


def upload_dict_to_job(comment,jobid):
   """
   uploads comment with pseudo json for each job id to slurm
   """
   #convert " -> ', since comment field does not allow " 
   nice_dict = json.dumps(comment)
   nice_dict = nice_dict.replace('"',"'")
   #print(nice_dict)
   logging.debug('/bin/scontrol update JobId={0} comment="{1}"'.format(jobid, nice_dict))
   out,err = commands.getstatusoutput('/bin/scontrol update JobId={0} comment="{1}"'.format(jobid,nice_dict))
   if err:
      logging.error(err)
   return out


def upload_comments_all_jobs(comments, config):
   """
   loops over all key value pairs of the comments dict, tries to upload the new comment
   and stores the comment into a json file in the WorkDir, such that upload is done
   only once
   """
   for jobid, comment in comments.items():
      print(jobid, comment)    
      try:
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
   jobs = get_job_list()#[:5]
   comments = create_comments_dict(jobs, config)
   #print(json.dumps(comments,indent=2))
   upload_comments_all_jobs(comments, config)   


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
   logging.debug('Successfully started slurm-annotator')
   while True:
      main(config)
      time.sleep(config['frequency'])
