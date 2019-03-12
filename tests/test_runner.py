import json
import os
import shutil
import subprocess
import sys

CASHIER_PATH = "../cashier.py"

def invokeCashier(rootDir):
    try:
        return subprocess.check_output(['python', CASHIER_PATH, rootDir]).strip()
    except:
        return ""

def loadTestCase(testFilePath):
    with open(testFilePath, 'r') as f:
        try:
            jsonObj = json.loads(f.read())
            jsonObj['name'] = os.path.basename(testFilePath).split('.')[0]
            return jsonObj
        except:
            return None
    return None

def executeTest(testConfig):
    name = testConfig['name']
    testDir = testConfig['test_dir']
    print('Running test: ' + name)
    # Setup
    os.system('mkdir scratch')

    originalDirPath = os.path.join('test_dirs', testDir)

    # Test and Judge copies
    testCopyPath = os.path.join('scratch', 'TEST')
    shutil.copytree(originalDirPath, testCopyPath)

    judgeCopyPath = os.path.join('scratch', 'JUDGE')
    shutil.copytree(originalDirPath, judgeCopyPath)

    unused = invokeCashier(testCopyPath)
    for directory in [testCopyPath, judgeCopyPath]:
        for cmd in testConfig['test_cmds']:
            cmd = 'cd ' + directory + '; ' + cmd
            os.system(cmd)

    testHash = invokeCashier(testCopyPath)
    judgeHash = invokeCashier(judgeCopyPath)

    if testHash != judgeHash:
        print('\nFailure!\nexpected: %s\ngot: %s\n' % (judgeHash, testHash))
    else:
        print('\nSuccess!\nexp: %s\ngot: %s\n' % (judgeHash, testHash))
    # Teardown
    os.system('rm -rf scratch')

# Clean directory
os.system('rm -rf scratch')

for testFile in os.listdir('test_cases'):
    if testFile.startswith('.'):
        continue
    testConfig = loadTestCase(os.path.join('test_cases', testFile))
    if testConfig:
        executeTest(testConfig)
    else:
        print('Error loading test: %s' % testFile)
