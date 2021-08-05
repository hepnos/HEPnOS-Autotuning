#!/bin/bash
# USER CONFIGURATION
CPUS_PER_NODE=2

# Script to launch Ray cluster
head_node=$HOSTNAME
#head_node_ip=$(dig $head_node a +short | awk 'FNR==2') # VERIFY ON THETA !!!!!!!!!
head_node_ip=10.128.0.49 # $(dig $head_node a +short | awk 'FNR==2') # VERIFY ON THETA !!!!!!!!!


# if we detect a space character in the head node IP, we'll
# convert it to an ipv4 address. This step is optional.
if [[ "$head_node_ip" == *" "* ]]; then
IFS=' ' read -ra ADDR <<<"$head_node_ip"
if [[ ${#ADDR[0]} -gt 16 ]]; then
  head_node_ip=${ADDR[1]}
else
  head_node_ip=${ADDR[0]}
fi
echo "IPV6 address detected. We split the IPV4 address as $head_node_ip"
fi

# Starting the Ray Head Node
port=6379
ip_head=$head_node_ip:$port
export ip_head
echo "IP Head: $ip_head"

echo "Starting HEAD at $head_node"

source activate /lus/theta-fs0/projects/OptADDN/hepnos/sw/dh-theta
cd exp_v2/
# mkdir exp_run_72
cd exp_run_73

ray start --head --node-ip-address=$head_node_ip --port=$port \
    --num-cpus $CPUS_PER_NODE --block &
    
ls -l /tmp/
cp -rf /tmp/ray/* /lus/theta-fs0/projects/OptADDN/hepnos/tmp/ray/

# # optional, though may be useful in certain versions of Ray < 1.0.
# sleep 10

deephyper hps ambs --evaluator ray --ray-address auto --num-cpus-per-task 1 --problem hps_2.hepnos.problem.Problem --run hps_2.hepnos.model_run.run

cp -rf /tmp/ray/* /lus/theta-fs0/projects/OptADDN/hepnos/tmp/ray/

# Activate env or conda env if applicable:
#source activate /lus/theta-fs0/projects/OptADDN/hepnos/sw/dh-theta
#cd exp_v2/
#mkdir exp_run_64
#cd exp_run_64
#deephyper hps ambs --evaluator ray --problem hps_2.hepnos.problem_v3.Problem --run hps_2.hepnos.model_run_v3.run --num-workers 32
# qsub -A OptADDN --queue debug-flat-quad --time 1:00:00 -I -n 8
