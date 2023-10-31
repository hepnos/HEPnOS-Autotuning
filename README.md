# HEPnOS Autotuning experiments

Important: the scripts have been written for the bash shell. If you are using
another shell (e.g. zsh, fish, tcsh, etc.) please switch to bash for reproducing
these experiments.

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

Once the installation script completed, you will find, among other files and
folders, a `user.yaml` file in the build directory. This file needs to be
edited to provide user-specific information including _project_ (the allocation
from which to charge node-hours) and _pdomain_ (protection domain for Theta,
which needs to be a unique name across all users. We recommend setting it to
`hep-<username>`, replacing `<username>` as appropriate).

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
$ source setup-env.sh
```

### Running a test experiment

To run a single instance of the HEPnOS Workflow, you can run the following commands
from the build directory.

```bash
$ python3 -m hepnos.autotuning.problems.simple --wdir test
$ test/submit.sh
```

This will submit a 4-node job with default parameters to run the workflow. The `dataloader-outout.txt`
and `pep-output.txt` files in the `test` directory will eventually be filled
and a runtime will be printed at the end.

Note: on Bebop you may end up with core files produced by the `hepnos-pep-benchmark` executable.
These crashes happen at the end of the run when the underlying PSM2 networking library disconnects.
We have not yet found a way to address this, but it does not affect the reported run times or
the validity of the results.

### Running the DeepHyper workflow

To run the DeepHyper workflow, you will need to use the scripts located in the `dh` folder
that the installation script copied in your build directory. First, let's create a folder
to be used as a working directory for our experiment.

```
mkdir my-experiment
cd my-experiment
```

Then, we can submit a DeepHyper experiment as follows.

```
../dh/submit.sh <nodes_per_exp> [ <other params> ... ]
```

Where `<nodes_per_exp>` is the number of nodes to use per instance of the HEPnOS workflow
(it should be a multiple of 4).
Other parameters may include the following:
- `--model <MODEL>` to specify the model to use (`RF`, `GP`, or `DUMMY`);
- `--disable_pep` to disable the second step (PEP) of the workflow;
- `--more_params` to use 20 parameters instead of 16;
- `--fit-generative-model <file.csv>` to do transfer learning from a previous CSV files.
For example:

```
../dh/submit.sh 4 --more_params
```
will run the DeepHyper workflow with 4 nodes per HEPnOS workflow instance,
enabling the PEP part, and using a 20-parameter space.

As the job progresses, folders in the form `exp-<id>` will appear, along with log
files named `exp-<id>.log`. As instances finish executing, DeepHyper will remove
the corresponding folder, but keep the log file.

The results of the search are appended to a `results.csv` file, where each line corresponds
to an evaluation of the HEPnOS workflow. The `objective` column contains the run time of
the workflow instance (negative because DeepHyper attemps to maximize its objective).
The values starting with "F" are used to indicate errors, such as DeepHyper killing the instance
because it took too much time to complete by itself (the timeout is set to 5min for the dataloader part
of the workflow, and 5min for the PEP part).
