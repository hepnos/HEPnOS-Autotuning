# Autotuning Simulation with Random-Forest Surrogate Model

Folders:
* The `data` folder contains CSV files from real experiments run with DeepHyper.
* The `exp` folder contains CSV files from simulated experiments using a surrogate-model in the black-box function.
* The `models` folder contains pre-computed surrogate-models.
* The `10k-samples` contains inferences from pre-computed surrogate-models randomly-sampled without duplication.

## Create and Save a Surrogate Model

To create a surrogate model from `data/exp-DUMMY-4-false-false*.csv` experiments and saved it as `models/model-4-false-false.pkl` run the following command:
```console
$ python create_surrogate_model.py -i "data/exp-DUMMY-4-false-false*.csv" -o models/model-4-false-false.pkl
```

To reload the surrogate model and test it run:
```console
$ python test_surrogate_model.py -i data/exp-DUMMY-4-false-false-1.csv -m models/model-4-false-false.pkl
```

## List Pre-Computed Surrogate Models

To list pre-computed surrogate models:
```
$ ls -l models/
```

## Execute a Search with Deephyper

To execute a search with DeepHyper run:
```console
$ python exec_deephyper -m models/model-4-true-true.pkl
```