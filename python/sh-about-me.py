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

import argparse
import getpass
import grp
import pwd
import subprocess

from lib.slurm import find_account_budget_and_usage, BUDGET_TO_POUNDS_FACTOR

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
      (account_budget[account], account_usage[account]) = find_account_budget_and_usage(account)
  if not len(account_user_usage):
    print("user does not have access to any slurm accounts.")
  else:
    print("slurm accounts you may use:")
    for (account, user_usage) in account_user_usage.items():
      print("%s (you have used £%d(%d%%) of £%d(%d%%) total used, total budget £%d)" % (account, user_usage*BUDGET_TO_POUNDS_FACTOR, user_usage*100/account_budget[account] if account_budget[account] > 0 else 0, account_usage[account]*BUDGET_TO_POUNDS_FACTOR, account_usage[account]*100/account_budget[account] if account_budget[account] > 0 else 0, account_budget[account]*BUDGET_TO_POUNDS_FACTOR))
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description="Display account information about your user.")
  parser.add_argument("--user", "-u", action="store", help="Display information about this user instead.")

  args = parser.parse_args()

  if args.user:
    user = args.user
  else:
    user = getpass.getuser()

  print("Unix user details:")
  print_user_details(user)
  print()
  print_user_accounts(user)

