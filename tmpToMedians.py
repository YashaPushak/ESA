import os
import sys

tmpFile = open("tmp.txt", "r")
outFile = open("bootstrap"+sys.argv[1]+"Q.txt", "a")
runtimes = []
for line in tmpFile:
    terms = line.split()
    runtimes.append( terms[1] )
print >>outFile, runtimes[0] + " " + runtimes[1]# + " " + runtimes[2] + " " + runtimes[3] + " " + runtimes[4]
tmpFile.close()
outFile.close()
