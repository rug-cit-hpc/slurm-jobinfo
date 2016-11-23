# jobinfo
The `jobinfo` script tries to collect information for a full job combining
information from the SLURM accounting system and live stats from `sstat` if the
job is still running.

Example output:

    [aeh@fe1 ~]$ jobinfo 11983512
    Name                : bash
    User                : aeh
    Partition           : normal
    Nodes               : s02n[45-48,51-53]
    Cores               : 50
    State               : FAILED
    Submit              : 2015-10-12T21:21:18
    Start               : 2015-10-12T21:21:23
    End                 : 2015-10-12T21:24:14
    Reserved walltime   : 2-00:00:00
    Used walltime       :   00:02:51
    Used CPU time       :   00:00:59
    % User (Computation): 83.22%
    % System (I/O)      : 16.78%
    Mem reserved        : 100M/node
    Max Mem used        : 25.18M (s02n45,s02n47,s02n48,s02n51,s02n53)
    Max Disk Write      : 16.00M (s02n45)
    Max Disk Read       : 2.00M (s02n45)

It has mostly been tested on batch jobs without any sub-steps so please send
feedback.
