# HEPnOS Autotuning experiments

## Installing

This repository is meant to provide reproducible experiments.
To install the necessary dependencies on one of the supported
platforms, use the following procedure after having cloned
this repository.

```bash
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

### Note on reproducibility

The `install.sh` script will install the [spack](https://spack.readthedocs.io/)
package manager and use it to manage all non-python dependencies. It will
install [miniconda](https://docs.conda.io/en/latest/miniconda.html) via spack
and use it to manage all python dependencies.

The script relies on a set of files providing global and platform-specific
configurations.
- `sources.yaml` provides the URL and references (commit, tag, or branch)
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
dependencies. In the process, it will create a a `sources.yaml.lock` file
specifying the exact commit used for spack and mochi, and a `pip-requirements.txt.lock`
file describing the exact version of each python package installed by pip.
If such a files are present in the build directory when calling `install.sh`,
it will use them in place of `sources.yaml` and `pip-requirements.txt`.

### Freezing the repository

Once it's time to provide reviewers with an archive from which they
can reproduce experiments, please do the following:
- Erase everything from the build directory except for
  `pip-requirements.txt.lock` and `sources.yaml.lock`
- Make sure dependencies in `spack-requirements.txt` point to
  numbered versions (not _main_, _develop_, or other branch-based version).

## Running the experiments

From this point, it is assumed that the working directory is the `build` directory
created in the above installation procedure.

The `setup-env.sh` file is a script that will be used to setup our environment.
Before trying to run any experiment, please run:

```bash
$ source ../setup-env.sh
```

You are now ready to setup an experiment, which you can do with the following command.

```bash
$ python -m hepnos.autotuning.setup \
    --activation-script ../setup-env.sh \
    -w <experiment-folder> \
    -q <job-queue> \
    -A <allocation-name> \
    -t <job-duration> \
    -n <number-of-nodes> \
    --step <hepnos-exp-step> \
    --nodes-per-task <nodes-per-task>
```

This will create a folder and generate a script in it that can be run with the
platform's job managed, for instance on Theta:

```bash
$ qsub exp/job.sh
```

On Bebop:

```bash
$ sbatch exp/job.sh
```

Or on a Linux workstation:

```bash
$ ./exp/job.sh
```
