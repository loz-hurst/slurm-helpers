#!/usr/bin/env python3

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

# Disable module-name and module doc-string checks - this is a script,
# not a module
#pylint: disable=C0103
#pylint: disable=C0111

import argparse
import inspect
import os
import sys

def expand_nodelist(nodelist):
    """
    Takes a slurm node list and retuns a python list with all nodes.

    Slurm node list might be of the form:
        node1[01-10,15],node2[1-5],node05

    Args:
        nodelist: single string containing the slurm node list

    Returns python list of strings, one per node, with the node names
    """
    nodes = []

    # Nodes are separated by commas but there might also be commas
    # within the square braces.  Nothing for it, have to go char-by-char
    in_brace = False
    prefix = ''
    suffix = ''
    ranges = ''
    def __generate_list(prefix, ranges, suffix):
        """
        Takes a prefix, range and suffix and generates a list of all
        node names in that range.
        """
        if ranges:
            # multiple nodes to add
            result = []
            for range_ in ranges.split(','):
                if '-' in range_:
                    (start, end) = range_.split('-')
                    length = len(start)
                    if len(start) != len(end):
                        raise RuntimeError(
                            "This script assumes that ranges start and end"
                            " with the same length string - not the case"
                            " with %s" % range_
                        )
                    format_ = "%s%%0%dd%s" % (prefix, length, suffix)
                    for i in range(int(start), int(end)+1):
                        result.append(format_ % i)
                else:
                    # Simple substitution
                    result.append(''.join((prefix, range_, suffix)))
            return result

        if suffix:
            raise RuntimeError(
                "No range but seperate prefix and suffix - this is not"
                " a valid state."
            )
        return [prefix]

    for ch in nodelist:
        if in_brace:
            if ch == ']':
                in_brace = False
            elif ch == '-' or ch == ',' or int(ch) is not None:
                ranges += ch
            else:
                raise RuntimeError(
                    "Unrecognised character %s in range brace" % ch
                )
        else:
            if ch == '[':
                if ranges:
                    raise RuntimeError(
                        "Cannot cope with multiple ranges per node, yet (but I"
                        " do not think slurm ever does that anyway).  Node"
                        " list was: %s" % nodelist
                    )
                in_brace = True
            elif ch == ',':  # End of this node set
                nodes.extend(__generate_list(prefix, ranges, suffix))
                # Reset for next set
                prefix = ''
                ranges = ''
                suffix = ''
            else:
                prefix += ch
    # End of list, add final set.
    nodes.extend(__generate_list(prefix, ranges, suffix))
    return nodes

def expand_task_counts(tasklist):
    """
    Takes a slurm task/cpu count and retuns a python list with all nodes.

    Slurm task/cpu counts might be of the form 1(x2),5
    I am unclear if Slurm combines the '(xN)' and ',' forms but it is
    easy enough to support the combined form.

    Args:
        tasklist: single string containing the slurm task/cpu list

    Returns python list of strings list the tasks/cpus per node in order
    """
    counts = []
    for part in tasklist.split(','):
        if '(x' in part:
            base = part[:part.find('(')]
            number = part[part.find('(')+2:part.find(')')]
            for _ in range(int(number)):
                counts.append(int(base))
        else:
            counts.append(int(part))
    return counts

def find_formatters():
    """
    Find a list of supported formatters.

    Returns python dict containing the string name of the formatter
    mapped to the method implementing it.
    """
    result = {}
    # Currently this enumerates all methods looking for those starting
    # format_.  The next bit is taken to be the name of formatter.
    prefix = 'format_'
    for potential_method in inspect.getmembers(sys.modules[__name__]):
        if potential_method[0].startswith(prefix):
            result[potential_method[0][len(prefix):]] = potential_method[1]

    return result

def format_HP_MPI(nodes, tasks):
    """
    Returns the list of nodes/tasks formatter for HP_MPI.

    Format is nodename:task_count for each node

    Args:
        nodes: list of nodes to take
        tasks: list of corresponding task counts for each node

    Return python list of strings containing the formatted list of nodes
    """
    result = []
    for (node, count) in zip(nodes, tasks):
        result.append("%s:%d" % (node, count))
    return result

def test():
    """
    Very simple test - should be more complete unit test using the
    python framework.
    """
    assert expand_nodelist('node1[01-10,15],node2[1-5],node05') == [
        'node101', 'node102', 'node103', 'node104', 'node105', 'node106',
        'node107', 'node108', 'node109', 'node110', 'node115', 'node21',
        'node22', 'node23', 'node24', 'node25', 'node05',
    ], "Node expansion works correctly test failed"
    assert expand_task_counts('1(x2),50') == [1, 1, 50], \
        "Task count expension works correctly test failed"
    assert 'HP_MPI' in find_formatters(), \
        "Find formatters finds HP_MPI formatter test failed"
    assert format_HP_MPI(['node01', 'node02', 'node05'], [1, 5, 2]) == [
        'node01:1', 'node02:5', 'node05:2',
    ], "HP_MPI formatter test failed"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Convert Slurm's node list to various formats.\nNodelist"
                    " will be read from the environment, formatted list will"
                    " be printed on STDOUT.",
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run test suite and exit",
    )
    parser.add_argument(
        "--list-formatters", "-l",
        action="store_true",
        help="List all supported output formats and exit",
    )
    parser.add_argument(
        "--formatter", "-f",
        action="store",
        help="Specify the output format required",
    )

    args = parser.parse_args()
    if args.test:
        print("Running test suite...")
        test()
        print("All tests passed.")
        sys.exit(0)

    formatters = find_formatters()
    if args.list_formatters:
        print("All supported formatters:")
        for formatter in formatters:
            print(formatter)
        sys.exit(0)

    if not args.formatter:
        print(
            "Error: No output format selected - please tell me which style of"
            " node list you would like",
            file=sys.stderr,
        )
        parser.print_help()
        sys.exit(1)
    else:
        if args.formatter not in formatters:
            print(
                "Error: Unrecognised formatter specified (they are case"
                " sensitive). Please check you have selected a supported"
                " formatter.",
                file=sys.stderr,
            )
            sys.exit(1)
        else:
            job_nodelist = os.environ.get("SLURM_JOB_NODELIST")
            # Should this be SLURM_TASKS_PER_NODE?
            job_tasklist = os.environ.get("SLURM_JOB_CPUS_PER_NODE")
            if job_nodelist is None or job_tasklist is None:
                print(
                    "Error: Unable to get node or task list from Slurm."
                    " Are you running this inside a multi-core HPC job?",
                    file=sys.stderr,
                )
                sys.exit(1)
            expanded_nodes = expand_nodelist(job_nodelist)
            expanded_tasks = expand_task_counts(job_tasklist)
            for output_line in formatters[args.formatter](
                expanded_nodes,
                expanded_tasks,
            ):
                print(output_line)
