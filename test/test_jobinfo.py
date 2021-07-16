from collections import namedtuple

import importlib
import io
import os
import re
import pytest


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
pynumparser_loader = importlib.machinery.SourceFileLoader(
    'pynumparser', os.path.join(test_script_dir, '../pynumparser.py')
)
pynumparser = pynumparser_loader.load_module()

jobinfo_loader = importlib.machinery.SourceFileLoader(
    'jobinfo', os.path.join(test_script_dir, '../jobinfo')
)
jobinfo = jobinfo_loader.load_module()

# Structure to represent return values for subprocess and requests calls.
Subprocess = namedtuple('Subprocess', ['stdout'])
Request = namedtuple('Request', ['content'])

# GPU usage values for mocked call to Prometheus
GPU_USAGE_VALUES = b'[[0,"50"], [1,"100"]]'

# Job structure for tests
testjob = jobinfo.Meta(
    JobID=123,
    JobName='test',
    User='testuser',
    Partition='cpu',
    NodeList='test-node[001-003]',
    NNodes=3,
    ncpus=6,
    NTasks=3,
    State='RUNNING',
    Submit='2020-01-01T11:00:00',
    start='2020-01-01T12:00:00',
    end='2020-01-01T13:00:00',
    timelimit='01:00:00',
    elapsed='01:00:00',
    TotalCPU='06:00:00',
    UserCPU=1,
    SystemCPU=1,
    ReqMem='1Gn',
    MaxRSS='1G',
    TRESUsageInTot=(6*1024**3, 0),
    TRESUsageOutTot='',
    MaxDiskWrite='',
    MaxDiskRead='',
    MaxRSSNode='',
    MaxDiskWriteNode='',
    MaxDiskReadNode='',
    Comment='',
    MaxMemPerTask='',
    MaxDiskWritePerTask='',
    MaxDiskReadPerTask='',
    dependencies='',
    reason='',
)

CPU_HINTS = [
    "Check the file in- and output pattern of your application.",
    "The program efficiency is very low.",
    "The program efficiency is low. Your program is not using the assigned cores",
]
MEMORY_HINT = "You requested much more memory than your program used."


def sacct_output(jobid):
    '''Mock call to sacct by reading from a file.'''

    with open(os.path.join(DATA_DIR, SACCT_FILE), 'rb') as sacct_file:
        sacct_lines = sacct_file.readlines()
    jobid_lines = [
        line for line in sacct_lines if line.split(b'\xe2\x98\x83')[0].split(b'.')[0] == jobid
    ]
    return Subprocess(stdout=jobid_lines)


def squeue_output(jobid):
    '''Mock call to squeue by reading from a file.'''
    with open(os.path.join(DATA_DIR, SQUEUE_FILE), 'r') as squeue_file:
        squeue_lines = squeue_file.read()

    squeue_line = re.search(f'{jobid}.*\n', squeue_lines).group(0).strip().split('|', 1)[1]
    print(squeue_lines)
    return Subprocess(stdout=io.BytesIO(squeue_line.encode('UTF-8')))


def sstat_output(jobid):
    '''Mock call to sstat by reading from a file.'''
    with open(os.path.join(DATA_DIR, SSTAT_FILE), 'rb') as sstat_file:
        sstat_lines = sstat_file.readlines()

    jobid_lines = [
        line for line in sstat_lines
        # only select lines for which the first field matches jobid or jobid.batch
        if line.split(b'|')[0].decode() in jobid.split(',')]
    return Subprocess(stdout=jobid_lines)


def scontrol_show_nodes_output(node):
    '''Mock call to scontrol by reading from a file.'''
    with open(os.path.join(DATA_DIR, SCONTROL_FILE), 'r') as nodes_file:
        nodes_lines = nodes_file.read()
    node_line = re.search(f'NodeName={node}.*\n', nodes_lines).group(0).strip().encode('UTF-8')
    return Subprocess(stdout=io.BytesIO(node_line))


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
    mocker.patch(
        'requests.get',
        return_value=Request(content=b'{"data":{"result":[{"values":' + GPU_USAGE_VALUES + b'}]}}')
    )
    jobinfo.main(jobid)


@pytest.mark.parametrize(
    'test_input, expected',
    [
        ('mycluster-gpunode42', ['mycluster-gpunode42']),
        ('mycluster-gpu[01-05]', ['mycluster-gpu0' + str(i) for i in range(1, 6)]),
        ('mycluster-gpu[01-03,40-42]', ['mycluster-gpu01', 'mycluster-gpu02', 'mycluster-gpu03',
                                        'mycluster-gpu40', 'mycluster-gpu41', 'mycluster-gpu42']),
    ]
)
def test_parse_gpu_string(test_input, expected):
    assert jobinfo.parse_gpu_string(test_input) == expected


@pytest.mark.parametrize(
    'gpu_usage_samples, expected_total_usage',
    [
        (b'[[0, 0], [1, 0], [2, 0], [3, 0]]', 0),
        (b'[[0, 0], [1, 100], [2, 100], [3, 0]]', 50),
        (b'[[0, 100], [1, 100], [2, 100], [3, 100]]', 100),
        (b'[]', -1),
    ]
)
def test_get_gpu_usage(gpu_usage_samples, expected_total_usage, mocker):
    ret_value_content = b'{"data":{"result":[{"values":' + gpu_usage_samples + b'}]}}'
    mocker.patch('requests.get', return_value=Request(content=ret_value_content))
    assert jobinfo.get_gpu_usage('dummy', 'start', 'end') == expected_total_usage


def test_get_gpus_usage(mocker):
    usage1 = b'[[0, 0], [1, 100], [2, 100], [3, 0]]' # 50%
    ret_value_content = b'{"data":{"result":[{"values":' + usage1 + b'}]}}'
    mocker.patch('requests.get', return_value=Request(content=ret_value_content))
    expected = [('my-gpu01', 50), ('my-gpu02', 50)]
    assert jobinfo.get_gpus_usage('my-gpu[01-02]', 'start', 'end') == expected


@pytest.mark.parametrize(
    'job_fields, expected_hints',
    [
        # No hints for jobs without an end time
        ({'end': 'UNKNOWN'}, []),
        # No hints for short jobs or ones without CPU time
        ({'elapsed': '00:01:00'}, []),
        ({'TotalCPU': '00:00:00'}, []),
        # No hints for GPU jobs
        ({'Partition': 'gpu'}, []),
        # Set memory usage to a very low value
        ({'TRESUsageInTot': (100*1024**2, 0), 'ReqMem': '10Gc'}, [MEMORY_HINT]),
        # Request 4x4 GB in total, only use 8 GB: below the total threshold and per-core threshold
        ({'ncpus': 4, 'ReqMem': '4Gc' ,'TRESUsageInTot': (8*1024**3, 0)}, [MEMORY_HINT]),
        # Request 4x4 GB in total, only use 11 GB: below the total threshold, but above the per-core one
        ({'ncpus': 4, 'ReqMem': '4Gc' ,'TRESUsageInTot': (11*1024**3, 0)}, []),
        # Request 1 core, but only use it for 70%
        ({'ncpus': 1, 'elapsed': '01:00:00', 'TotalCPU': '00:30:00'}, [CPU_HINTS[0]]),
        # Request 10 core, but only use one (10%)
        ({'ncpus': 10, 'elapsed': '01:00:00', 'TotalCPU': '01:00:00'}, [CPU_HINTS[1]]),
        # Request 10 core, but only use them about half of the time
        ({'ncpus': 10, 'elapsed': '01:00:00', 'TotalCPU': '05:00:00'}, [CPU_HINTS[2]]),
    ],
)
def test_hints(job_fields, expected_hints, mocker, capfd):
    mocker.patch('subprocess.Popen', side_effect=popen_side_effect)

    mytestjob = testjob._replace(**job_fields)
    jobinfo.get_hints(mytestjob)
    stdout, stderr = capfd.readouterr()
    for hint in expected_hints:
        assert hint in stdout

    non_expected_hints = set(CPU_HINTS + [MEMORY_HINT]).difference(expected_hints)
    for hint in non_expected_hints:
        assert hint not in stdout
