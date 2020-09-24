HEPnOS Autotuning
=================

This code is meant to execute on the Bebop supercomputer.

Installing
----------

The procedure bellow will install [spack](https://spack.io/), then
create a _hepnos_ environment and install HEPnOS and the HDF5 Dataloader
in it, as well as their dependencies.

```
git clone https://xgitlab.cels.anl.gov/sds/hep/hepnos-autotuning.git
cd hepnos-autotuning/bebop
./install.sh
```

Following this installation, please edit `scripts/settings.sh.in` to set
variables such as your project allocation to appropriate values.


Testing the installation
------------------------

Once installed, this experimental setup can be tested by calling:

```
python run.py
```

This will automatically submit a 4-node job.
Once the job start, it will complete in about 3 min.


Running with various parameters
-------------------------------

`run.py` is the entry point for an execution. It provides a `run`
function accepting a list as parameters. This list must contain
5 elements corresponding to the following parameters:

* **Number of threads:** the number of threads that a server can use,
  not including the progress thread. Since 2 servers are deployed on
  each node, this number can range from 0 to 31.
* **Number of databases:** the number of databases per server for event
  data and for product data. For example if set to 16, each server
  will create 16 databases for event data and 16 other databases for
  product data.
* **Busy spin:** true or false, indicating whether Mercury should be
  set to busy-spin.
* **Async:** true or false, indicating whether the client will execute
  store operation asynchronously, trying to overlap with file read operations.
* **Batch size:** the batch size on clients (int).

The `run.py` script is designed to work from its location as current working
directory, and will not work properly for now if invoked from somewhere else.
It will create a directory prefixed with `exp-` in which it will create the
configuration files necessary to run the experiment. It then calls a `submit.sh`
script which itself invokes `job.qsub`. If `run.py` is executed from inside
a job (rather than from the login node), `submit.sh` will recognize this
and invoke `job.qsub` as a regular bash script rather than passing it to `qsub`.
The `job.qsub` script invokes `aprun` to deploy HEPnOS on 2 nodes, then it call
another `aprun` to execute the HEPnOS dataloader application on 2 other nodes.
When this second `aprun` completes, it calls `aprun` once more one 1 node to send
a message to HEPnOS to make it shut down.
