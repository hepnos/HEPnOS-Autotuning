HEPnOS Autotuning
=================

This code is meant to execute on the Theta supercomputer.

Installing
----------

The procedure bellow will install [spack](https://spack.io/), then
create a _hepnos_ environment and install HEPnOS and the HDF5 Dataloader
in it, as well as their dependencies.

```
git clone https://xgitlab.cels.anl.gov/sds/hep/hepnos-autotuning.git
cd hepnos-autotuning
./install.sh
```

Following this installation, please edit `scripts/settings.sh.in` to set
variables such as your project allocation to appropriate values.

Testing
-------
