#!/bin/bash

# -H    host IP adress (default Docker gateaway is 172.17.0.1 so the SLIMM server should be listening to this)
# -p    port number (by default SLIMM or any FIRE application should be listening to 9002)
# -l    log file location and name
# -f    data file location with full file name
# -d    delay between MRD_MESSAGE_ISMRMRD_IMAGE (1022) sends in seconds
#           for example 0.1 stands for 100 miliseconds delay between each image file
#           for example for a dataset with 56 images per volume with 1 seconds per volume (56 images per second), d should be 1/56

# usage
# sh start-fire-send-server.sh measurement-20231010T155525.hdf5 0.01
# first input is the h5 file name
# second input is the delay in seconds

work_dir=/opt/code/python-fire-server-base

if [ $# -lt 2 ];
then
  echo "$0: Missing arguments -f file name -d delay (s)"
  exit 1
elif [ $# -gt 2 ];
then
  echo "$0: Too many arguments: $@"
  exit 1
else
  sudo docker run --rm -it -v ./save:${work_dir}/save -v ./logs:${work_dir}/logs python-fire-server:send -v -H "172.17.0.1" -p 9002 -l ${work_dir}/logs/python-ismrmrd-server.log -f ${work_dir}/save/$1 -d $2
fi