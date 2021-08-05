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
cd hepnos-autotuning/theta
./install.sh
```

Following this installation, please edit `scripts/settings.sh.in` to set
variables such as your project allocation to appropriate values.


Testing the installation
------------------------

The following command can be used to test the installation:

```
python run.py --enable-pep
```

This command will run an experiment on 8 nodes of the debug-flat-quad queue.


Explanations
------------

`run.py` is the entry point for an execution. It provides a `run`
function accepting the following parameters:

* `hepnos_num_threads`: the number of threads that a server can use,
  not including the progress thread. Since 2 servers are deployed on
  each node, this number can range from 0 to 31.
* `hepnos_num_databases`: the number of databases per server for event
  data and for product data. For example if set to 16, each server
  will create 16 databases for event data and 16 other databases for
  product data.
* `busy_spin`: true or false, indicating whether Mercury should be
  set to busy-spin.
* `loader_progress_thread`: true or false, indicating whether the client will execute
  store operation asynchronously, trying to overlap with file read operations.
* `loader_batch_size`: the write batch size on loader clients.

Additionally, more parameters can be provided to enable running the
parallel event processing (PEP) benchmark after the data loader.
If enabled, the reported time will be the total time (data loading + PEP benchmark).
To enable this step, the `enable_pep` parameter should be set to `True`
and the following parameters should be provided.

* `pep_num_threads`: the number of threads used by benchmark processes
  to process data. Should be at least 1 and up to 31.
* `pep_ibatch_size`: the batch size used when processes are loading events
  from HEPnOS.
* `pep_obatch_size`: the batch size used when processes are sending batches
  of events to each other.
* `pep_use_preloading`: whether the benchmark uses preloading of products.
* `pep_pes_per_node`: number of benchmark processes per node.
* `pep_cores_per_pe`: number of cores allocated per benchmark process.

Finally, a `nodes` parameter may be provided that contains a list
of host names to use for the experiment.

The `run.py` script can be called on its own, passing parameters as follows:

```
python run.py --hepnos-num-threads=8 ...
```

Note the use of `-` in parameter names when used on the command line.

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
