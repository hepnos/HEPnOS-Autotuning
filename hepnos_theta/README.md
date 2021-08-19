HEPnOS Autotuning
=================

This code is meant to execute on the Theta supercomputer.

Installing
----------

The procedure bellow will install [spack](https://spack.io/), then
create a _hepnos_ environment and install HEPnOS, the HDF5 Dataloader,
and the Parallel Event Processing benchmark in it, as well as their dependencies.

```
git clone https://github.com/hepnos/HEPnOS-Autotuning.git
cd HEPnOS-Autotuning/hepnos_theta
./install.sh
```

Following this installation, please edit `scripts/settings.sh.in` to set
variables such as your project allocation to appropriate values.

**DeepHyper**
From the directory where `HEPnOS-Autotuning/` is located execute:

```
./HEPnOS-Autotuning/hepnos_theta/deephyper_install.sh
```

Then create a `SetUpEnv.sh` following this template and adapting to your settings:


```bash
#!/bin/bash

module load postgresql
module load miniconda-3

# Activate conda env
conda activate /lus/grand/projects/datascience/regele/theta/hepnos/dhenv/

export PYTHONPATH="/lus/grand/projects/datascience/regele/theta/hepnos/HEPnOS-Autotuning/:$PYTHONPATH"
```

Source this script: `source SetUpEnv.sh` and test with the following command (think about adapting `settings.sh.in`):

```
python -m hepnos_theta.run_exp -w exp/exp-test -q debug-cache-quad -t 60 -A radix-io -n 8 --nodes-per-task 4 -as ./SetUpEnv.sh --run hepnos_theta.run.run --problem hepnos_theta.problem.Problem
```

the results will be found in `exp/exp-test`.

Testing the installation
------------------------

The following command can be used to test the installation:

```
python run.py --enable-pep
```

This command will run an experiment on 8 nodes of the debug-flat-quad queue.


Explanations
------------

`run.py` is the entry point for an execution. It can be called either as
a script (`python run.py ...`) or via its `run` function. The script
accept a number of parameters listed bellow. The `run` function accepts
a dictionary containing the same parameters, but with `-` replaced with
`_` (for example `hepnos-num-threads` becomes `hepnos_num_threads`).
In the command line, boolean parameters are turned on or off by having
or not having the flag set (e.g. `--hepnos-progress-thread` present or
absent, rather than `--hepnos-progress-thread=true`).

* Parameters common to HEPnOS, the Dataloader, and PEP
  * `busy-spin`: true or false, indicating whether Mercury should be
    set to busy-spin.

* HEPnOS parameters:
  * `hepnos-pes-per-node`: number processes per node on which to run HEPnOS.
    Possible values: `[1, 2, 4, 8, 16, 32]`
  * `hepnos-progress-thread`: whether to use a progress thread or not in HEPnOS.
    Possible values: `boolean`.
  * `hepnos-num-threads`: number of threads each HEPnOS process can use to service
    RPCs, not including the progress thread and primary thread.
    Possible values: `[0 , ... , 63]`.
  * `hepnos-num-providers`: number of database providers in each HEPnOS process.
    Possible values: `[1, ..., 32]`.
  * `hepnos-num-event-databases`: the number of databases per server process for event data.
    Possible values: `[1, ..., 16]`.
  * `hepnos-num-product-databases`: the number of databases per server process for product data.
    Possible values: `[1, ..., 16]`.
  * `hepnos-pool-type`: type of Argobots pool used by HEPnOS servers.
    Possible values: `[ "fifo_wait", "fifo", "prio_wait" ]`

Constraints: The number of PEs per node (first parameter) constrains the number of threads
that can resonnably be used per process (`hepnos-progress-thread` and `hepnos-num-threads`).
Theta nodes have 64 cores, hence the product of the number of PEs per node and the number of
threads must not exceed 64 (it could, but that would mean oversubscribing the nodes, which
I suspect will lead to performance degradations). There is always a "primary" thread running
on each process. If `hepnos-progress-thread` is provided, one extra thread is created. The
`hepnos-num-threads` is then added. For instance, if we set `hepnos-progress-thread` and
`hepnos-num-threads=4`, the total number of threads will be 6 (1 primary, 1 progress, 4 rpc).

* Dataloader parameters
  * `loader-pes-per-node`: number of processes per node on which to run the Dataloader.
    Possible values: `[1, 2, 4, 8, 16, 32]`
  * `loader-progress-thread`: true or false, indicating whether the Dataloader should use
    a progress thread. Possible values: `boolean`.
  * `loader-batch-size`: the write batch size on loader clients. Possible values: `[1, 2048]` (log-uniform).
  * `loader-async`: whether to rely on asynchronous operations to interact with HEPnOS.
    Possible values: `boolean`.
  * `loader-async-threads`: number of threads to assign for asynchronous operations.
    Relevant only if `loader-async` is set. Possible values: `[1, 63]` (log-uniform).

Constraints: The same kind of constraint on the number of PEs per node and the
total number of threads applies.

Additionally, more parameters can be provided to enable running the
parallel event processing (PEP) benchmark after the data loader.
If enabled, the reported time will be the total time (data loading + PEP benchmark).
To enable this step, the `--enable-pep` parameter should be set on the command line,
or the `DH_HEPNOS_ENABLE_PEP` environment variable should be set to 1.

* PEP parameters
  * `pep-progress-thread`: whether to use a progress thread in PEP processes.
  * `pep-pes-per-node`: number of processes per node on which to run PEP.
     Possible values: `[1, 2, 4, 8, 16, 32]`
  * `pep-num-threads`: the number of threads used by benchmark processes
    to process data. Possible values:
  * `pep-ibatch-size`: the batch size used when processes are loading events
    from HEPnOS. Possible values: `[8 ... 1024]` (log-uniform)
  * `pep-obatch-size`: the batch size used when processes are sending batches
    of events to each other. Possible values: `[8 ... 1024]` (log-uniform)
  * `pep-use-preloading`: whether the benchmark uses preloading of products.

  Constraints: The same kind of constraint on the number of PEs per node and
  total number of threads applies.

Finally, a `nodes` parameter may be provided that contains a list
of host names to use for the experiment.

The `run.py` script can be called on its own, passing parameters as follows:

```
python run.py --hepnos-num-threads=8 ...
```

The `run.py` script is designed to work from any location.
It will create a directory prefixed with `exp-` in the current directory, in
which it will create the configuration files necessary to run the experiment.
It will use `scripts/settings.sh.in` to produce a `settings.sh` file for the
experiment based on the parameters provided by the run function. One important
variable of `scripts/settings.sh.in` is the `HEPNOS_LOADER_DATAFILE`, which
must point to one of the files in the `data` directory. If `run.py` is called
from somewhere different from its location, please edit the variable to provide
a correct path.

`run.py` then calls `scripts/submit.sh` which itself invokes `job.qsub`.
If `run.py` is executed from inside a job (rather than from the login node),
`submit.sh` will recognize this and invoke `job.qsub` as a regular bash script
rather than passing it to `qsub`. The `job.qsub` script invokes `aprun` to deploy
HEPnOS on `N/4` nodes, where `N` is the value of the `NODES_PER_EXP` variable
in `settings.sh.in`. Then it calls
another `aprun` to execute the HEPnOS dataloader application on the remaining nodes.
When this second `aprun` completes, it calls `aprun` again to start the parallel
event processing benchmark if requested, and finally it calls `aprun` once more
one 1 node to send a message to HEPnOS to make it shut down.
