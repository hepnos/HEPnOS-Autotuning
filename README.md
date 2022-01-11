# HEPnOS Autotuning experiments

## Installing

This repository is meant to provide reproducible experiments.
To install the necessary dependencies on one of the supported
platforms, use the following procedure after having cloned
this repository.

```
$ mkdir build
$ cd build
$ ../install.sh <platform>
```

Replace `<platform>` with the appropriate platform name, for
instance `theta`, `bebop`, or `linux`.

Note: the `linux` setup is for building in a standard Linux cluster
with no specific job scheduler. The installation script will make
no assumption about the presence of existing, system-provided libraries,
and will install absolutely all the dependencies needed from scratch
(hence the build time can be pretty long). The `hepnos/autotuning/linux/hosts.txt`
file can be edited to provide a list of hosts usable by _mpirun_.

## Reproducibility

The `install.sh` script will install the [spack](https://spack.readthedocs.io/)
package manager and use it to manage all non-python dependencies. It will
install [miniconda](https://docs.conda.io/en/latest/miniconda.html) via spack
and use it to manage all python dependencies.

The script relies on a set of files providing global and platform-specific
configurations.
- `settings.sg` provides the URL and references (commit, tag, or branch)
  to use for downloading _spack_ and _mochi-spack-packages_, the repository
  that provides Mochi-specific packages.
- `pip-requirements.txt` provides the list of requirements for `pip` to
  install within the miniconda environment that will be created.
- `spack-requirements.txt` provides the list of non-python packages that
  need to be installed using spack.
- `hepnos/autotuning/<platform>/spack.yaml` is a platform-specific YAML
  file that spack will use as a basis for creating environments.
- `hepnos/autotuning/<platform>/settings.sh` (if present) is a file
  that will be sourced by `install.sh` to provide platform-specific
  environment variables.

By default, `install.sh` will use the above files to install the necessary
dependencies. In the process, it will create a `pip-requirements.<platform>.lock`
file  describing the exact version of each python package installed by pip.
If such a file is present, `install.sh` will use it in place of `pip-requirements.txt`.

### Freezing the repository

Once it's time to provide reviewers with an archive from which they
can reproduce experiments, please do the following:
- Make sure the `pip-requirements.<platform>.lock` files are provided;
- Make sure the references in `settings.sh` point to _commits_, NOT branches or tags;
- Make sure dependencies in `spack-requirements.txt` point to numbered versions
  (not _main_, _develop_, or other branch-based version).
