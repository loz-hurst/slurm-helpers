#!/usr/bin/env python3

# Copyright 2021 Laurence Alexander Hurst
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

# Disable module-name and module doc-string checks - this is a script,
# not a module
#pylint: disable=C0103
#pylint: disable=C0111

import argparse
import getpass
import grp
import pwd
import re
import subprocess
import sys

from lib.slurm import get_partition_info, BUDGET_TO_POUNDS_FACTOR


def print_cost(nodes, duration, partitions=None):
    """
    Prints the estimated cost for a job.

    args:
        nodes: number of nodes being used
        duration: estimated duration in minutes
        partition: partition to print the cost for, prints all
                     partitions if not specified or set to None
    """
    part_info = get_partition_info()
    if partitions is None:
        print_partitions = part_info.keys()
    else:
        print_partitions = partitions

    for partition in print_partitions:
        days = int(duration / 1440)
        rem = duration - days*1440
        hours = int(rem / 60)
        minutes = rem - 60*hours
        billing_weights = dict([i.split('=') for i in part_info[partition]['TRESBillingWeights'].split(',')])
        cost = int(billing_weights['Node']) * nodes * duration * BUDGET_TO_POUNDS_FACTOR
        print("Running a %d node job in %s for %dd%02d:%02d will cost approx £%0.2f" %(nodes, partition, days, hours, minutes, cost))
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Display estimated cost for your job.")
    parser.add_argument("--partition", "-p", action="append", help="Partition you wish to use (may be specified multiple times for more than 1 partition, default: show price for all partitions).")
    parser.add_argument("--nodes", "-n", action="store", type=int, default=1, help="Number of nodes you wish to use (default: 1).")
    parser.add_argument("--duration", "-d", action="store", default='1', help="Estimated duration of your job (format: [Dd]H[:M], e.g. 5d2:26 for 5 days, 2 hours and 26 minutes, default: 1 (= 1 hour)).")

    args = parser.parse_args()

    time_regx = re.compile(r'^(:?(?P<days>[0-9]+)d)?(?P<hours>[0-9]+)(:?:(?P<minutes>[0-9]+))?$')
    match = time_regx.match(args.duration)
    if not match:
        print("Error parsing duration, please check it is in the right format.", file=sys.stderr)
        parser.print_help(file=sys.stderr)
        sys.exit(1)
    else:
        # Hours are mandatory, so start with that value
        duration = 60 * int(match['hours'])
        # ...plus days
        if match['days'] is not None:
            duration += 1440 * int(match['days'])  # 1,440 = 24 hours * 60 minutes
        # ...plus minutes
        if match['minutes'] is not None:
            duration += int(match['minutes'])

    print_cost(args.nodes, duration, args.partition)

