# Tests for jobinfo

The file `test_jobinfo.py` contains tests for jobinfo, implemented using `pytest`.
Besides `pytest` itself, it also requires `pytest-mock`.
The latter is used to mock the calls to the SLURM commands;
instead, it will read in pregenerated data dumps (obtained by running the SLURM commands). See the `data` directory for more information.
