import os
import hashlib
import sys
import json
import time

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

    @staticmethod
    def loadCashFile(dirName):
        cashFile = CashFile(dirName)
        cash_path = os.path.join(dirName, CASH_FILE_NAME)
        if not os.path.isfile(cash_path):
            return None
        with open(cash_path, 'r') as f:
            cashFile.stats = json.loads(f.read())
        return cashFile

    def writeCashFile(self):
        cash_path = os.path.join(self.dirName, CASH_FILE_NAME)
        with open(cash_path, 'w') as f:
            f.write(json.dumps(self.stats) + '\n')

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
        combinedCashFile.stats['mtime'] = max(maxTime, time.time())
        combinedCashFile.stats['hash'] = m.hexdigest()
        combinedCashFile.stats['namehash'] = mnamehash.hexdigest()
        return combinedCashFile

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
            m.update(cashFile.getNameHash())
        return m.hexdigest()

finalHash = None

for dirName, subdirList, fileList in os.walk(rootDir, topdown=False):
    if shouldClean:
        os.system('rm %s' % os.path.join(dirName, CASH_FILE_NAME))
        continue

    currentCashFile = CashFile.loadCashFile(dirName)
    filteredSubDirList = sorted(filter(lambda x: not x.startswith('.'),
                                       subdirList))
    filteredFileList = sorted(filter(lambda x: not x.startswith('.'), fileList))
    if currentCashFile:
        finalHash = currentCashFile.getHash()
    else:
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
        if os.path.islink(fp):
            continue
        if not os.path.isfile(fp):
            continue
        fpMTime = os.path.getmtime(fp)
        fileCashFile = CashFile(fp, None, fpMTime, fn)
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

    for cashfile in cashFileList:
        cashfile.setHash(CashFile.hashFile(cashfile.dirName))

    currentCashFile = CashFile.combineCashFiles(dirName, totalCashList)
    # Manually set namehash for now
    currentCashFile.setNameHash(newNameHash)
    currentCashFile.writeCashFile()
    finalHash = currentCashFile.getHash()

print finalHash
