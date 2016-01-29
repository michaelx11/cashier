#!/usr/bin/env python

import os
import hashlib
import sys
import json
import time

################################################################################
# Overview
################################################################################
# Cashier hashes a directory. Any modification to file contents, or directory
# structure is reflected in the hash (SHA1).
#
# Cashier produces .cash_file json files in sub-directories with contents:
#   - modification time
#   - hash of subdirectory contents
#   - namehash of subdirectory structure (file names)
#
# These files allow for quick iterative hashing.
#
# The final produced hash is SHA1(namehash + hash) of the root directory.
#
########################################
# Usage
########################################
# $ cashier.py path_to_root_directory [clean]
#   - where the clean option removes all .cash_file's
#
########################################
# Algorithm
########################################
#
# Let cash_i be a tuple where:
#   i = a directory or file
#   cash_i_mtime = latest modification time in subdirectory
#   cash_i_hash = hash of all contents of subdirectory
#   cash_i_namehash = hash of (dir/filename + namehash) for all subdirectories
#
# As a convention: cash_i where i is a file becomes:
#   cash_i_mtime = latest modification time of file
#   cash_i_hash = SHA1(contents of file)
#   cash_i_namehash = SHA1(filename)
#
# Then we compute cash_i with the following recurrence given subdir(i) is
# a list of immediate children of i sorted lexicographically.
#
#   cash_i_mtime = max(cash_u_mtime for all u in subdir(i))
#   cash_i_hash = SHA1(concat(cash_u_hash for all u in subdir(i)))
#   cash_i_namehash = SHA1(concat(u_name+cash_u_namehash for all u in subdir(i)))
#
# Then output = SHA1(cash_r_namehash + cash_r_hash) where r is the root dir
#
# Efficiency comes from pruning of subdirs using modification time for
# detection. Only subdirs containing a newer mod time or a differing namehash
# require recomputation of content hashes.
#
################################################################################

if len(sys.argv) < 2:
    print 'Usage: cashier.py path_to_root_dir [clean]'
    sys.exit(0)

rootDir = sys.argv[1]
if not os.path.exists(rootDir):
    print 'Error: %s does not exist.' % rootDir
    sys.exit(0)

shouldClean = False
if len(sys.argv) > 2 and sys.argv[2] == 'clean':
    shouldClean = True

CASH_FILE_NAME = ".cash_file"
FILE_DIRNAME_PLACEHOLDER = "FILE"

class CashFile:

    def __init__(self, dirName, hash=None, mtime=None, namehash=None):
        self.stats = {}
        self.dirName = dirName
        self.stats['hash'] = hash
        self.stats['mtime'] = mtime
        self.stats['namehash'] = namehash

    def writeCashFile(self):
        cash_path = os.path.join(self.dirName, CASH_FILE_NAME)
        with open(cash_path, 'w') as f:
            f.write(json.dumps(self.stats) + '\n')

    def setHash(self, hashValue):
        self.stats['hash'] = hashValue

    def getHash(self):
        return self.stats['hash']

    def setMTime(self, mtime):
        self.stats['mtime'] = mtime

    def getMTime(self):
        return self.stats['mtime']

    def setNameHash(self, nameHashValue):
        self.stats['namehash'] = nameHashValue

    def getNameHash(self):
        return self.stats['namehash']

    @staticmethod
    def loadCashFile(dirName):
        cashFile = CashFile(dirName)
        cash_path = os.path.join(dirName, CASH_FILE_NAME)
        if not os.path.isfile(cash_path):
            return None
        with open(cash_path, 'r') as f:
            cashFile.stats = json.loads(f.read())
        return cashFile

    @staticmethod
    def combineCashFiles(dirName, listCashFiles):
        combinedCashFile = CashFile(dirName)
        maxTime = 0
        m = hashlib.sha1()
        mnamehash = hashlib.sha1()
        for cashFile in listCashFiles:
            m.update(cashFile.getHash())
            mnamehash.update(cashFile.getNameHash())
            maxTime = max(maxTime, cashFile.getMTime())
        combinedCashFile.stats['mtime'] = maxTime
        combinedCashFile.stats['hash'] = m.hexdigest()
        combinedCashFile.stats['namehash'] = mnamehash.hexdigest()
        return combinedCashFile

    @staticmethod
    def hashFile(filePath):
        if not os.path.isfile(filePath):
            return None
        m = hashlib.sha1()
        with open(filePath, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    @staticmethod
    def hashNames(listCashFiles):
        m = hashlib.sha1()
        for cashFile in listCashFiles:
            m.update(os.path.basename(cashFile.dirName).lower()) # file or dir name
            m.update(cashFile.getNameHash()) # subdir name hash
        return m.hexdigest()

currentCashFile = None

for dirName, subdirList, fileList in os.walk(rootDir, topdown=False):
    if shouldClean:
        os.system('rm %s' % os.path.join(dirName, CASH_FILE_NAME))
        continue

    currentCashFile = CashFile.loadCashFile(dirName)
    filteredSubDirList = sorted(filter(lambda x: not x.startswith('.'),
                                       subdirList))
    filteredFileList = sorted(filter(lambda x: not x.startswith('.'), fileList))
    if not currentCashFile:
        currentCashFile = CashFile(dirName, "", 0)

    # Directories first
    cashDirList = []
    for subdir in filteredSubDirList:
        subdirPath = os.path.join(dirName, subdir)
        if os.path.islink(subdirPath):
            continue
        tempCashFile = CashFile.loadCashFile(subdirPath)
        if tempCashFile:
            cashDirList.append(tempCashFile)
        else:
            sys.stderr.write('Error! Sub-directory [%s] contains no files.\n' %
                             subdirPath)

    cashFileList = []
    # Then files (ignores hidden files)
    for fn in filteredFileList:
        fp = os.path.join(dirName, fn)
        if os.path.islink(fp) or not os.path.isfile(fp):
            continue
        fpMTime = os.path.getmtime(fp)
        fileCashFile = CashFile(fp, None, fpMTime, fn.lower())
        cashFileList.append(fileCashFile)

    totalCashList = cashDirList + cashFileList

    # Check if we need to update
    needsUpdate = False
    for cashFile in totalCashList:
        if cashFile.getMTime() > currentCashFile.getMTime():
            needsUpdate = True
            break

    newNameHash = CashFile.hashNames(totalCashList)
    if newNameHash != currentCashFile.getNameHash():
        needsUpdate = True

    # No update needed, keep on going
    if not needsUpdate:
        continue

    # Populate file content hashes
    for cashfile in cashFileList:
        cashfile.setHash(CashFile.hashFile(cashfile.dirName))

    currentCashFile = CashFile.combineCashFiles(dirName, totalCashList)
    # Manually set namehash for now
    currentCashFile.setNameHash(newNameHash)
    currentCashFile.writeCashFile()

# Final combined hash(namehash + contents hash)
print hashlib.sha1(currentCashFile.getNameHash() +
                   currentCashFile.getHash()).hexdigest()
