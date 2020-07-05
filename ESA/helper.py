#Author: Yasha Pushak
#Last updated: July 12th, 2016
#Some general helper functions

import time
import math
import pickle
import string, random
from contextlib import contextmanager
import os
import numpy as np
import glob
import datetime

def generateID(size=6, chars=string.ascii_uppercase + string.digits):
    #generate a random ID for identifying SMAC runs
    return ''.join(random.choice(chars) for _ in range(size))


def isNumber(s):
    #http://stackoverflow.com/questions/354038/how-do-i-check-if-a-string-is-a-number-float-in-python
    try:
        float(s)
        return True
    except ValueError:
        return False
def randSeed():
    return random.randint(0,2147483647)


def mkdir(dir):
    #Author: Yasha Pushak
    #Last updated: January 3rd, 2017
    #An alias for makeDir
    makeDir(dir)


def makeDir(dir):
    #Only creates the specified directory if it does not already exist.
    #At some point it may be worth adding a new feature to this that saves the old directory and makes a new one if one exists.
    if(not os.path.isdir(dir)):
        os.system('mkdir '  + dir)


def isDir(dir):
    #Author: Yasha Pushak
    #last updated: March 21st, 2017
    #Checks if the specified directory exists.
    return os.path.isdir(dir)


def isFile(filename):
    #Author: Yasha Pushak
    #Last updated: March 21st, 2017
    #CHecks if the specified filename is a file.
    return os.path.isfile(filename)


def compressDir(dir,fileName):
    #Author: Yasha Pushak
    #Last updated: March 21st, 2017
    #Compresses the specified directory into a zipped folder and deletes
    #the original folder. 

    with cd(dir + '/../'):
        zipDir = '/'.join(dir.split('/')[-1:])
        zipFile = '/'.join(dir.split('/')[-1:])
        os.system('zip -r ' + zipFile + ' ' + zipDir)
    deleteDir(dir)


def deleteDir(dir):
    #Author: Yasha Pushak
    #Last updated: March 21st, 2017
    #Deletes the specified directory and everything in it.
    os.system('rm -r -f ' + dir)


def uncompressDir(dir,fileName):
    #Author: Yasha Pushak
    #last updated: March 21st, 2017
    #Unzips the directory specified in fileName into dir.

    os.system('unzip ' + fileName + ' -d ' + dir)


def deleteFile(file):
    #Author: Yasha Pushak
    #Last updated: June 19th, 2016

    #clean up
    os.system('rm -f ' + file)



@contextmanager
def cd(newdir):
    #http://stackoverflow.com/questions/431684/how-do-i-cd-in-python/24176022#24176022
    prevdir = os.getcwd()
    os.chdir(os.path.expanduser(newdir))
    try:
        yield
    finally:
        os.chdir(prevdir)



#Code From: http://stackoverflow.com/questions/12418234/logarithmically-spaced-integers
import numpy as np
def genLogSpace(limit, n):
    result = [1]
    if n>1:  # just a check to avoid ZeroDivisionError
        ratio = (float(limit)/result[-1]) ** (1.0/(n-len(result)))
    while len(result)<n:
        next_value = result[-1]*ratio
        if next_value - result[-1] >= 1:
            # safe zone. next_value will be a different integer
            result.append(next_value)
        else:
            # problem! same integer. we need to find next_value by artificially incrementing previous value
            result.append(result[-1]+1)
            # recalculate the ratio so that the remaining values will scale correctly
            ratio = (float(limit)/result[-1]) ** (1.0/(n-len(result)))
    # round, re-adjust to 0 indexing (i.e. minus 1) and return np.uint64 array
    result = map(lambda x: int(round(x)-1), result)
    return result
#return np.array(map(lambda x: round(x)-1, result), dtype=np.uint64)


#Code taken from http://stackoverflow.com/questions/19201290/how-to-save-a-dictionary-to-a-file

def saveObj(dir_, obj, name ):
    with open(dir_ + '/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def loadObj(dir_, name ):
    if isFile(dir_ + '/' + name + '.pkl'):
        filename = dir_ + '/' + name + '.pkl'
    elif isFile(dir_ + '/' + name):
        filename = dir_ + '/' + name 
    elif isFile(name + '.pkl'):
        filename = name + '.pkl'
    elif isFile(name):
        filename = name
    else:
        raise IOError("Could not find file '{}' in '{}' or current working directory with or without a "
                      ".pkl extension.".format(name, dir_))
    with open(filename, 'rb') as f:
        return pickle.load(f)


