# slurm-helpers

User-friendly scripts for the Slurm workload manager software

# module files

Example TCL module is included in modulefile, compatible with either [environment modules](http://modules.sourceforge.net/) or [Lmod](https://www.tacc.utexas.edu/research-development/tacc-projects/lmod).  Make sure you change the path to where slurm-helpers is installed.

# Notes

The billing information presented in slurm-about-me and slurm-esitmate-cost is based on a number of assumptions/limitations:

* Charging is done at a node-leve based on weights defined on the partitions containing a homogeneous set of nodes
* Billing is done using based on units that are the price in GBP(£) * 1e8 (10^8)

All of these are fixable but I have no immediate need to do so.  Pull requests welcome!

# Licence and Copyright

Copyright 2020-2021 Laurence Alexander Hurst

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
