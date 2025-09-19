#!/bin/sh -eu
#
# Copyright 2023 MPOWR IT GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# meta log processor for system-nfo enrichment
#

META_LOG_F_CPOD_HOSTNAME=/.docker/sys_cpod_hostname.log
META_LOG_F_CPOD_IP=/.docker/sys_cpod_ip.log
META_LOG_F_CPOD_K8S_MASTER=/.docker/sys_k8s_master_ip.log
META_SYS_ETH_EXT=eth0

# -- identify + load current pod/container ip to sys_cpod_io.log meta file
ip addr show ${META_SYS_ETH_EXT} | grep "inet\b" | awk '{print $2}' | cut -d/ -f1 > ${META_LOG_F_CPOD_IP} ;

# -- identify + load current pod/container hostname
cat /etc/hostname > ${META_LOG_F_CPOD_HOSTNAME} ;

# -- identify k8s environment
if [ -z ${KUBERNETES_SERVICE_HOST+x} ]; then
    echo "none" > ${META_LOG_F_CPOD_K8S_MASTER} ;
else
    echo "$KUBERNETES_SERVICE_HOST" > ${META_LOG_F_CPOD_K8S_MASTER} ;
fi

