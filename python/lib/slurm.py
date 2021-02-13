# Copyright 2020 Laurence Alexander Hurst
#
# This file is part of slurm-helpers.
#
# slurm-helpers is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# slurm-helpers is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with slurm-helpers.  If not, see <https://www.gnu.org/licenses/>.

"""
Provides some functions to interrogate and interact with Slurm.
"""

import subprocess

# Amount to multiply budgets by to get pounds
BUDGET_TO_POUNDS_FACTOR=1.0/1e8

def find_account_budget_and_usage(account):
    """
    Finds the budget and total usage so far for an account.

    args:
        account: account to find details for

    returns tuple of (budget, usage)
    """
    # Get the account, account's minutes budget and the usage
    output = subprocess.run(
        [
            "sshare",
            "-A", account,
            "-P",
            "-n",
            "-o", "account,GrpTRESMins,GrpTRESRaw",
        ],
        capture_output=True,
        encoding='utf-8',
        check=True,
    )
    for line in output.stdout.split('\n'):
        if not line:
            continue # Skip blank lines
        (account, tres_limit, tres_usage) = line.split('|')
        tres_limit_dict = dict([i.split('=') for i in tres_limit.split(',')])
        tres_usage_dict = dict([i.split('=') for i in tres_usage.split(',')])
        return (int(tres_limit_dict['billing']), int(tres_usage_dict['billing']))

def get_partition_info():
    """
    Find information about the slurm partitions from slurm.

    args: None

    returns a dict keyed on partition names to a dict of information
    from slurm.
    """
    # Find the cost/node/minute for all partitions (it is one command,
    # one or all does not matter too much - launching the sub-process
    # is the expensive bit of this operation).
    output = subprocess.run(
        [
            'scontrol',
            'show', 'partition',
            '--oneline',
        ],
        capture_output=True,
        encoding='utf-8',
        check=True
    )
    part_dict = {}
    for line in output.stdout.split('\n'):
        if not line:
            continue # Skip blank lines
        part_info = dict([i.split('=', 1) for i in line.split(' ')])
        part_dict[part_info['PartitionName']] = part_info
    return part_dict
