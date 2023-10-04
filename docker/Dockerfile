# ----- First stage to build ismrmrd and siemens_to_ismrmrd -----
FROM python:3.10.2-slim AS mrd_converter
ARG  DEBIAN_FRONTEND=noninteractive
ENV  TZ=America/Chicago

# Python Dependencies from the requirements.txt file
WORKDIR /usr/local/lib/
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt


#FROM ubuntu:20.04
#ARG DEBIAN_FRONTEND=noninteractive
FROM python:3.10.2-slim

# Copy /usr/local/lib/ which includes additional python libraries from the previous stage
COPY --from=mrd_converter /usr/local/lib/ /usr/local/lib/

# Copy local code to the appropriate palce inside the image
RUN mkdir -p /opt/code/python-fire-server-send \
	&& mkdir -p /opt/code/python-fire-server-send/venv \
	&& mkdir -p /opt/code/python-fire-server-send/docker .
COPY ./ /opt/code/python-fire-server-send

# Ensure startup scripts are marked as executable, which may be lost if files
# are copied in Windows
RUN find /opt/code/python-fire-server-send -name *.sh -exec chmod +x {} \;

# Set the starting directory so that code can use relative paths
WORKDIR /opt/code/python-fire-server-send

ENTRYPOINT [ "python3", "/opt/code/python-fire-server-send/main.py"]
CMD ["/bin/bash"]
# Replace the above CMD with this ENTRYPOINT to allow allow "docker stop"
# commands to be passed to the server.  This is useful for deployments, but
# more annoying for development
# ENTRYPOINT [ "python3", "/opt/code/python-fire-server-base/main.py", "-v", "-H=0.0.0.0", "-p=9002", "-l=/tmp/python-fire-server-base.log"]

# , "-v", "-H", "127.0.0.1", "-p", "9002", "-l", "./log/python-ismrmrd-server.log", "-f", "/tmp/save/measurement-20231002T110706.hdf5"