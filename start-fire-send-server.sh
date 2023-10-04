#!/bin/bash

# -H    host IP adress (default Docker gateaway is 172.17.0.1 so the SLIMM server should be listening to this)
# -p    port number (by default SLIMM or any FIRE application should be listening to 9002)
# -l    log file location and name
# -f    data file location with full file name
# -d    delay between MRD_MESSAGE_ISMRMRD_IMAGE (1022) sends in seconds
#           for example 0.1 stands for 100 miliseconds delay between each image file
#           for example for a dataset with 56 images per volume with 1 seconds per volume (56 images per second), d should be 1/56

sudo docker run --rm -it -v /tmp/save:/tmp/save python-fire-server:send -v -H "172.17.0.1" -p 9002 -l ./log/python-ismrmrd-server.log -f /tmp/save/measurement-20231002T110706.hdf5 -d 0.1