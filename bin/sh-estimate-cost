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

import argparse
import getpass
import grp
import pwd
import re
import subprocess
import sys

# Amount to multiply budgets by to get pounds
BUDGET_TO_POUNDS_FACTOR=1.0/1e8

def print_user_details(username):
	"""
	Print information about the user.

	args:
		username: user to print information about

	returns nothing
	"""
	usr_pwd = pwd.getpwnam(username)
	print("user: %s uid: %d" % (usr_pwd.pw_name, usr_pwd.pw_uid))
	print("home: %s shell: %s" % (usr_pwd.pw_dir, usr_pwd.pw_shell))
	primary_group = grp.getgrgid(usr_pwd.pw_gid)
	print("primary group: %s(%d)" % (primary_group.gr_name, primary_group.gr_gid))
	print("other groups: %s" % ', '.join(["%s(%d)" % (g.gr_name, g.gr_gid) for g in grp.getgrall() if username in g.gr_mem]))

def _find_account_budget_and_usage(account):
	"""
	Finds the budget and total usage so far for an account.

	args:
		account: account to find details for

	returns tuple of (budget, usage)
	"""
	# Get the account, account's minutes budget and the usage
	output = subprocess.run(["sshare", "-A", account, "-P", "-n", "-o", "account,GrpTRESMins,GrpTRESRaw"], capture_output=True, encoding='utf-8')
	for line in output.stdout.split('\n'):
		if not len(line):
			continue # Skip blank lines
		(account, tres_limit, tres_usage) = line.split('|')
		tres_limit_dict = dict([i.split('=') for i in tres_limit.split(',')])
		tres_usage_dict = dict([i.split('=') for i in tres_usage.split(',')])
		return (int(tres_limit_dict['billing']), int(tres_usage_dict['billing']))

def print_user_accounts(username):
	"""
	Print information about the user's slurm accounts.

	args:
		username: user to print accounts for
	
	returns nothing
	"""
	output = subprocess.run(["sshare", "-U", "-u", username, "-P", "-n", "-o", "user,account,GrpTRESMins,GrpTRESRaw"], capture_output=True, encoding='utf-8')
	account_user_usage = {} # This users usage
	account_usage = {} # The total usage where budget is inherited
	account_budget = {} # The total budget
	for line in output.stdout.split('\n'):
		if not len(line):
			continue # Skip blank lines
		(user, account, user_budget, user_tres) = line.split('|')
		tres = dict([i.split('=') for i in user_tres.split(',')])
		account_user_usage[account] = int(tres['billing'])
		if len(user_budget):  # User has their own budget
			user_budget_dict = dict([i.split('=') for i in user_budget.split(',')])
			account_usage[account] = int(tres['billing'])
			account_budget[account] = int(user_budget_dict['billing'])
	for account in account_user_usage.keys():
		if account not in account_budget:
			(account_budget[account], account_usage[account]) = _find_account_budget_and_usage(account)
	if not len(account_user_usage):
		print("user does not have access to any slurm accounts.")
	else:
		print("slurm accounts you may use:")
		for (account, user_usage) in account_user_usage.items():
			print("%s (you have used £%d(%d%%) of £%d(%d%%) total used, total budget £%d)" % (account, user_usage*BUDGET_TO_POUNDS_FACTOR, user_usage*100/account_budget[account] if account_budget[account] > 0 else 0, account_usage[account]*BUDGET_TO_POUNDS_FACTOR, account_usage[account]*100/account_budget[account] if account_budget[account] > 0 else 0, account_budget[account]*BUDGET_TO_POUNDS_FACTOR))

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
	output = subprocess.run(['scontrol', 'show', 'partition', '--oneline'], capture_output=True, encoding='utf-8')
	part_dict = {}
	for line in output.stdout.split('\n'):
		if not len(line):
			continue # Skip blank lines
		part_info = dict([i.split('=', 1) for i in line.split(' ')])
		part_dict[part_info['PartitionName']] = part_info
	return part_dict

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

