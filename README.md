# cashier
fast iterative hashing in one file

Generates SHA1 hash of a directory. Subsequent runs are speed up by
utilizing modification times and local subdirectory hash data files.

Usage:

$ python cashier.py [root directory]

Clean: removes cashier data files *.cash_file

$ python cashier.py [root directory] clean

