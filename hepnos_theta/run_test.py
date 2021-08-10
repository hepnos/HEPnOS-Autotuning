import re
import subprocess

def __make_node_list(nodes):
    if nodes is None:
        return None
    result = []
    for n in nodes:
        m = re.search('([0-9]+)', n)
        result.append(str(int(str(m.group(0)))))
    return result

def run(config, nodes=None):
    val = config["loader_batch_size"]
    num_nodes = len(nodes)
    node_list = ",".join(__make_node_list(nodes))
    cmd_temp = "aprun -n {num_nodes} -L {node_list} -N 1 echo 'val({val})'"
    cmd = cmd_temp.format(num_nodes=num_nodes, node_list=node_list, val=val).split(" ")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    output = proc.stdout
    error = proc.stderr
    print(f"nodes{nodes}\n command: {' '.join(cmd)}\n -- outpout --\n{output}\n\n -- error --\n{error}")
    m = re.search('val\([0-9]+\)', output)
    return int(m.group(0)[4:-1])
