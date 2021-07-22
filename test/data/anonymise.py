#!/usr/bin/env python3

import os
import random
import re
import string


# Name of the original input files, see README.md for more information on how to generate them.
SACCT_FILE = 'sacct.txt'
SSTAT_FILE = 'sstat.txt'
SQUEUE_FILE = 'squeue.txt'
SCONTROL_FILE = 'scontrol.txt'

# We assume all cluster nodes are named like: <cluster>-<nodetype><number>.
# We rename them to <CLUSTER_PREFIX_ANON>-<nodetype><number>.
CLUSTER_PREFIX_ANON = b'mycluster'
# All usernames will be renamed to <USERNAME_PREFIX_ANON><number>.
USERNAME_PREFIX_ANON = b'user'

# Column number (start counting at 0) of sacct output file that contains the name of the job/user.
SACCT_JOBNAME_COLUMN = 1
SACCT_USERNAMES_COLUMN = 2
# sacct separator
SACCT_SEPARATOR = b'\xe2\x98\x83'

sacct_lines = []
sacct_lines_anon = []


def random_job_name():
    '''Return a random job name between 3 and 15 characters.'''
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(3, 15))).encode('UTF-8')


def find_usernames():
    '''Find all usernames in the third column of the sacct dump.'''
    with open(SACCT_FILE, 'rb') as sacct:
        sacct_lines = sacct.readlines()

    usernames = [
        line.split(SACCT_SEPARATOR)[SACCT_USERNAMES_COLUMN]
        for line in sacct_lines
        if line.split(SACCT_SEPARATOR)[SACCT_USERNAMES_COLUMN]
    ]
    # Convert to set to get unique usernames.
    return set(usernames)


def find_cluster_prefixes():
    '''Find the cluster prefixes from the node names in the scontrol dump.'''
    with open(SCONTROL_FILE, 'rb') as scontrol_file:
        scontrol = scontrol_file.read()
    # Find all nodenames.
    nodes = re.findall(rb'NodeName=(\S+)', scontrol)
    # Find the prefix by splitting by the hypen symbol.
    prefixes = [node.split(b'-', 1)[0] for node in nodes]
    # Return a list of unique prefixes.
    return list(set(prefixes))


def generate_anonymised_usernames(usernames):
    '''Make a mapping from original usernames to anonymised ones.'''
    return {user: USERNAME_PREFIX_ANON + b'%d' % (i+1) for i, user in enumerate(usernames)}


def generate_anonymised_cluster_prefixes(cluster_prefixes):
    '''Make a mapping from original cluster prefixes to anonymised ones.'''
    return {prefix: CLUSTER_PREFIX_ANON + b'%d' % (i+1) for i, prefix in enumerate(cluster_prefixes)}


def anonymise(file, usernames, cluster_prefixes):
    '''Anonymise a file by replacing all usernames and cluster prefixes by anonymised versions.'''
    with open(file, 'rb') as file_handle:
        contents = file_handle.read()

    for username, username_anon in generate_anonymised_usernames(usernames).items():
        contents = contents.replace(username, username_anon)

    for cluster_prefix, cluster_prefix_anon in generate_anonymised_cluster_prefixes(cluster_prefixes).items():
        contents = contents.replace(cluster_prefix + b'-', cluster_prefix_anon + b'-')

    # For the scontrol dump, let's remove other fields containing possibly sensitive information (e.g. kernel versions).
    if file == SCONTROL_FILE:
        contents = b'\n'.join([b' '.join(groups) for groups in re.findall(rb'(NodeName=\S+) .* (CfgTRES=\S+) .*', contents)])

    # For sacct, we also remove the name of the job.
    if file == SACCT_FILE:
        sacct_lines = contents.strip().split(b'\n')
        sacct_lines_anon = []
        for line in sacct_lines:
            columns = line.split(SACCT_SEPARATOR)
            if columns[SACCT_JOBNAME_COLUMN] and columns[SACCT_JOBNAME_COLUMN] != b'batch':
                columns[SACCT_JOBNAME_COLUMN] = random_job_name()
            sacct_lines_anon.append(SACCT_SEPARATOR.join(columns))
        contents = b'\n'.join(sacct_lines_anon)

    # Rename the original file...
    os.rename(file, file + '.orig')

    # and write the new file with anonymised contents.
    with open(file, 'wb') as file_handle:
        file_handle.write(contents)


def main():
    '''Main function that calls the anonymize function for all our files.'''
    cluster_prefixes = find_cluster_prefixes()
    usernames = find_usernames()

    for file in [SACCT_FILE, SSTAT_FILE, SCONTROL_FILE, SQUEUE_FILE]:
        anonymise(file, usernames, cluster_prefixes)


if __name__ == '__main__':
    main()
