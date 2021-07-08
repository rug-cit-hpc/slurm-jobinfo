from collections import namedtuple

import importlib
import io
import os
import pytest
import re

# Location of test script
test_script_dir = os.path.dirname(os.path.realpath(__file__))

# Directory that contains the input files for the tests.
DATA_DIR = os.path.join(test_script_dir, 'data')
# Filenames of the input files.
SACCT_FILE = 'sacct.txt'
SSTAT_FILE = 'sstat.txt'
SQUEUE_FILE = 'squeue.txt'
SCONTROL_FILE = 'scontrol.txt'

# This is not a proper module, so use importlib to load the sources.
pynumparser_loader = importlib.machinery.SourceFileLoader('pynumparser', os.path.join(test_script_dir, '../pynumparser.py'))
pynumparser = pynumparser_loader.load_module()

jobinfo_loader = importlib.machinery.SourceFileLoader('jobinfo', os.path.join(test_script_dir, '../jobinfo'))
jobinfo = jobinfo_loader.load_module()

# Structure to represent real subprocess.popen return values.
Subprocess = namedtuple('Subprocess', ['stdout'])


def sacct_output(jobid):
    '''Mock call to sacct by reading from a file.'''

    with open(os.path.join(DATA_DIR, SACCT_FILE), 'rb') as sacct_file:
        sacct_lines = sacct_file.readlines()
    jobid_lines = [line for line in sacct_lines if line.split(b'\xe2\x98\x83')[0].split(b'.')[0] == jobid]
    return Subprocess(stdout = jobid_lines)


def squeue_output(jobid):
    '''Mock call to squeue by reading from a file.'''
    with open(os.path.join(DATA_DIR, SQUEUE_FILE), 'r') as squeue_file:
        squeue_lines = squeue_file.read()

    squeue_line = re.search(f'{jobid}.*\n', squeue_lines).group(0).strip().split('|', 1)[1]
    print(squeue_lines)
    return Subprocess(stdout = io.BytesIO(squeue_line.encode('UTF-8')))


def sstat_output(jobid):
    '''Mock call to sstat by reading from a file.'''
    with open(os.path.join(DATA_DIR, SSTAT_FILE), 'rb') as sstat_file:
        sstat_lines = sstat_file.readlines()

    jobid_lines = [
        # remove first field, as jobinfo doesn't expect the job id to be there
        line.split(b'|', 1)[1]
        for line in sstat_lines
        # only select lines for which the first field matches jobid or jobid.batch
        if line.split(b'|')[0].decode() in jobid.split(',')]
    return Subprocess(stdout = jobid_lines)


def scontrol_show_nodes_output(node):
    '''Mock call to scontrol by reading from a file.'''
    with open(os.path.join(DATA_DIR, SCONTROL_FILE), 'r') as nodes_file:
        nodes_lines = nodes_file.read()
    node_line = re.search(f'NodeName={node}.*\n', nodes_lines).group(0).strip().encode('UTF-8')
    return Subprocess(stdout = io.BytesIO(node_line))


def popen_side_effect(*args, **kwargs):
    '''
    Side effect function for mocking the call to subprocess.Popen.
    Depending on what Popen is calling, we redirect to the right function.
    '''
    popen_args = list(args[0])
    if popen_args[0] == b'sacct':
        return sacct_output(popen_args[-1])
    elif popen_args[0] == 'scontrol':
        return scontrol_show_nodes_output(popen_args[-1])
    elif popen_args[0] == 'squeue':
        return squeue_output(popen_args[-1])
    elif popen_args[0] == 'sstat':
        return sstat_output(popen_args[-1])


def find_all_jobids():
    '''Find all our test job ids in the sacct.txt file.'''
    jobids = []
    with open(os.path.join(DATA_DIR, SACCT_FILE), 'rb') as sacct_file:
        sacct = sacct_file.readlines()
        jobids = [line.split(b'\xe2\x98\x83', 1)[0].split(b'.')[0].decode() for line in sacct]
    # convert to set to remove duplicates
    return set(jobids)


@pytest.mark.parametrize('jobid', find_all_jobids())
def test_jobinfo(jobid, mocker):
    '''Test jobinfo on a given jobid.'''
    mocker.patch('subprocess.Popen', side_effect=popen_side_effect)
    mocker.patch('os.getuid', return_value=0)
    jobinfo.main(jobid)

# TODO: add gpu jobs, mock the calls to prometheus

# TODO: implement more fine-grained (unit) tests for different functions.
