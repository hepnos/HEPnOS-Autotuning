#!/bin/sh

NODES_PER_EXP=4 # should be divisible by 4
HEPNOS_PROJECT=radix-io # change for your project allocation
HEPNOS_PDOMAIN=hep-mdorier
HEPNOS_DATASET=nova # name of the dataset
HEPNOS_LABEL=abc # label to use for the products
HEPNOS_ENABLE_PROFILING=0
HEPNOS_UTILITY_TIMEOUT=60
	# list of HDF5 files to ingest
HEPNOS_LOADER_DATAFILE=$EXPDIR/$HEPNOS_EXP_PLATFORM-50files.txt
HEPNOS_LOADER_VERBOSE=critical # verbose level
HEPNOS_LOADER_PRODUCTS=(
	hep::rec_energy_numu
	hep::rec_hdr
	hep::rec_sel_contain
	hep::rec_sel_cvn2017
	hep::rec_sel_cvnProd3Train
	hep::rec_sel_remid
	hep::rec_slc
	hep::rec_spill
	hep::rec_trk_cosmic
	hep::rec_trk_kalman
	hep::rec_trk_kalman_tracks
	hep::rec_vtx
	hep::rec_vtx_elastic_fuzzyk
	hep::rec_vtx_elastic_fuzzyk_png
	hep::rec_vtx_elastic_fuzzyk_png_cvnpart
	hep::rec_vtx_elastic_fuzzyk_png_shwlid) # products to load
HEPNOS_LOADER_ENABLE_PROFILING=0
HEPNOS_LOADER_SOFT_TIMEOUT=10000

# 50files.txt
HEPNOS_LOADER_TIMEOUT=600 # timeout in seconds, after which the application will be killed

HEPNOS_ENABLE_PEP=1 # enable parallel event processing benchmark
HEPNOS_PEP_VERBOSE=info # at least info is needed
HEPNOS_PEP_PRODUCTS=(
	hep::rec_energy_numu
	hep::rec_hdr
	hep::rec_sel_contain
	hep::rec_sel_cvn2017
	hep::rec_sel_cvnProd3Train
	hep::rec_sel_remid
	hep::rec_slc
	hep::rec_spill
	hep::rec_trk_cosmic
	hep::rec_trk_kalman
	hep::rec_trk_kalman_tracks
	hep::rec_vtx
	hep::rec_vtx_elastic_fuzzyk
	hep::rec_vtx_elastic_fuzzyk_png
	hep::rec_vtx_elastic_fuzzyk_png_cvnpart
	hep::rec_vtx_elastic_fuzzyk_png_shwlid) # products to process
HEPNOS_PEP_ENABLE_PROFILING=0
HEPNOS_PEP_TIMEOUT=600 # timeout in seconds, after which the application will be killed

CONST_TIMEOUT=99999999
CONST_FAILURE=88888888

HEPNOS_PES_PER_NODE=2
HEPNOS_LOADER_ASYNC_THREADS=-1
HEPNOS_LOADER_BATCH_SIZE=512
HEPNOS_LOADER_PES_PER_NODE=2
HEPNOS_PEP_PES_PER_NODE=8
HEPNOS_PEP_OBATCH_SIZE=128
HEPNOS_PEP_IBATCH_SIZE=128
HEPNOS_PEP_THREADS=6
HEPNOS_PEP_PRELOAD=--preload
