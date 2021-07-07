#!/bin/bash

usage() {
   echo "Usage: checkjobinfo.sh [-h] [-f filename | -o filename ] [-n number] -d date"
   echo "   -h          : Show this help message"
   echo "   -f filename : Read jobids from file"
   echo "   -o filename : Write jobids obtained from job database to file"
   echo "   -n number   : Use each nth job from slurm database output, default 100"
   echo "   -s date     : Look at jobs starting from this date yyyy-mm-dd, default today"
   echo "   -e date     : Look at jobs until this date yyyy-mm-dd, default today"
   exit;
}

getjobs() {
   sacct -nap --start=${date} --end=${enddate} | awk -F '|' '{print $1}' | grep -v '\.batch' | awk "NR % ${skip} == 0"
}

skip=100

while getopts “f:o:s:e:n:h” arg; do
  case ${arg} in
    f)
       fname=${OPTARG}
       ;;
    o)
       oname=${OPTARG}
       ;;
    s)
       startdate=${OPTARG}
       ;;
    e)
       enddate=${OPTARG}
       ;;
    n)
       skip=${OPTARG}
       ;;
    h) 
       usage
       ;;
    *)
       usage
       ;;
  esac
done

if [ -z ${fname} ]; then
   if [ -z ${startdate} ]; then
      startdate=$( date -I)
   fi
   if [ -z ${enddate} ]; then
      enddate=$( date -I)
   fi
   echo "Generating a list of jobs from ${startdate} until ${enddate} and taking each ${skip} job"
   if [ -z ${oname} ]; then
      jobs=$( getjobs )
   else
      echo "Saving list of jobs to $oname"
      getjobs > ${oname}
      jobs=$( cat ${oname} )
   fi
else
   echo "Reading list of jobs from ${fname}, date ignored"
   jobs=$(cat ${fname})
fi


for job in ${jobs}; do
   ./jobinfo ${job}
done
