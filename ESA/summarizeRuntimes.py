import math
import numpy
import os
import sys
import csvHelper
import latexHelper

def calStatistic( list, statistic ):
    if statistic.lower() == "mean":
        return numpy.mean( list )
    if statistic.lower() == "median":
        statistic = "q50"
    if statistic[0].lower() == "q":
        percent = float( statistic[1:] )
        if percent<1:
            percent *= 100

        list = sorted(list)
        I = len(list)*(percent/100.0) - 1
        #Check if I is an integer
        if(int(I) - I == 0):
           return (list[int(I)] + list[int(I+1)])/2
        else:
           return list[int(math.ceil(I))]

        #YP: The original code here used to always return a lower-bound on
        #the quantiles. I have changed this..
        #This is what Zongxu used to have: 
        #return sorted(list)[ int(len(list)*percent/100)-1 ]
    print('[Error]: Invalid summary statistic input: ' + statistic)
    raise Exception('Invalid summary statistic input.')

def calStatisticIntervals( list, statistic, numInsts ):
    if statistic == "mean" or len(list) == numInsts:
        return [ calStatistic( list, statistic ) for i in range(0,2) ]
    else:
        return [ calStatistic( list+[ 0 for i in range(0, numInsts-len(list)) ], statistic ), calStatistic( list+[ float('inf') for i in range(0, numInsts-len(list)) ], statistic ) ]

def getRuntimesFromFile(dirName, filename, numRunsPerInstance):
    #YP: Added a warning count.
    numWarning = 0
    sizes = []
    runtimes = []
    numInsts = []
    sizeRuntimes = {}
    sizeNumInsts = {}
    header = True
    with open(dirName+"/"+filename, 'r') as runtimesFile:
        for line in runtimesFile:
            if line.strip()[0] == '#':
                if line.strip()[1:10] == 'instances':#YP: I suspect that this entire if statement (and the following one I marked) are not used in practice, but where originally intended for debugging purposes...
                    #YP: Actually, based on a paper I have just read, I now believe that this is used for handling instances with unknown optimal solution qualities, and hence, lower bounds on median running times. 
                    #YP: TODO: Investigate this further. 
                    terms = line.split(",")
                    sizeNumInsts[ int(terms[1]) ] = int(terms[2])
                continue
            terms = line.split(",")
            #YP: added float() before int() for terms[1] in three spots that follow
            if int(float(terms[1])) not in sizeRuntimes:
                sizeRuntimes[ int(float(terms[1])) ] = []
            #YP: Added loop and error message
            instRuntimes = []
            for i in range(2,len(terms)):
                try:
                    runtime = float(terms[i])
                except:
                    runtime = float('inf')
                if runtime < 0:
                    runtime = float('inf')
                instRuntimes.append(runtime)
            if(numRunsPerInstance > 0 and not len(instRuntimes) == numRunsPerInstance):
                numWarning += 1
                if(numWarning <= 10):
                    print('[Warning]: Instance ' + terms[0] + ' has ' + str(len(instRuntimes)) + ' running times and not the specified ' + str(numRunsPerInstance) + ' running times.')
            
            sizeRuntimes[ int(float(terms[1])) ].append( instRuntimes )
    
    if(numWarning - 10 > 0):
        print('[Warning]: ' + str(numWarning - 10) + ' similar warnings suppressed.')

    for size in sorted( sizeRuntimes ):
        sizes.append(size)
        runtimes.append( sizeRuntimes[size] )
        numInsts.append( len( sizeRuntimes[size] ) )
        if size in sizeNumInsts.keys():#YP: See comment above.
            numInsts[-1] = sizeNumInsts[size]
#            if header == True:
#                terms = line.split(",")
#                for term in terms:
#                    sizes.append( int(term) )
#                    runtimes.append( [] )
#                header = False
#            else:
#                stIdx = 0
#                terms = line.split(",")
#                if len(terms) == len(sizes)+1:
#                    stIdx = 1
#                for i in range(stIdx, len(terms)):
#                    if terms[i].strip() == "":
#                        continue
#                    runtimes[ i-stIdx ].append( float(terms[i]) )
#    print(sizes)
#    for i in range(0,len(runtimes)):
#        for j in range(0,len(runtimes[i])):
#        print(len(runtimes[i]))
    #print(sizeRuntimes)
    #print(numInsts)
    return (sizes, runtimes, numInsts)

def prepareRuntimesTexTable(st, ed, sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s):
    res = ""
    res += "\\begin{tabular}{c|" + "c"*len(sizes[st:ed]) + "} \n"
    res += "\\hline \n"
    res += latexHelper.prepareTableRow("$n$", sizes[st:ed])
    res += "\\hline \n"
    res += latexHelper.prepareTableRow("\\# instances", numInsts[st:ed])
    res += latexHelper.prepareTableRow("\\# running times", counts[st:ed])
    res += latexHelper.prepareTableRow("mean", [ ("$%s$" % latexHelper.numToTex(means[i], 4) if counts[i]==numInsts[i] else "N/A" ) for i in range(st,ed) ] )
    res += latexHelper.prepareTableRow("coefficient of variation", [ ("$%s$" % latexHelper.numToTex(coeffVars[i], 4) if counts[i]==numInsts[i] else "N/A" ) for i in range(st,ed) ] )
    res += latexHelper.prepareTableRow("Q(0.1)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q10s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.25)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q25s[st:ed] ])
    res += latexHelper.prepareTableRow("median",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in medians[st: ed]])
    res += latexHelper.prepareTableRow("Q(0.75)", [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q75s[st:ed] ])
    res += latexHelper.prepareTableRow("Q(0.9)",  [ ( "$%s$" % latexHelper.numToTex(v[0],4) if v[0]==v[1] else latexHelper.genInterval(latexHelper.numToTex(v[0], 3), latexHelper.numToTex(v[1], 4) ) ) for v in q90s[st:ed] ])
    res += "\\hline \n"
    res += "\\end{tabular} \n"
    res += "\\medskip{} \n"
    return res

def prepareRuntimesTexTables(sizes, runtimes, numInsts, threshold, dirName, supportTexFileName="table_Details-dataset-support.tex", challengeTexFileName="table_Details-dataset-challenge.tex"):
    #TODO: We're going to need to add the numRunsPerInstance here sometime.
    counts = []
    means = []
    coeffVars = []
    q10s = []
    q25s = []
    medians = []
    q75s = []
    q90s = []
    for i in range(0, len(sizes)):
        counts.append( len(runtimes[i]) )
        means.append( calStatistic(runtimes[i], "mean") )
        coeffVars.append( numpy.std(runtimes[i])/means[i] )
        medians.append( calStatisticIntervals( runtimes[i], "median", numInsts[i] ) )
        q10s.append(    calStatisticIntervals( runtimes[i], "q10"   , numInsts[i] ) )
        q25s.append(    calStatisticIntervals( runtimes[i], "q25"   , numInsts[i] ) )
        q75s.append(    calStatisticIntervals( runtimes[i], "q75"   , numInsts[i] ) )
        q90s.append(    calStatisticIntervals( runtimes[i], "q90"   , numInsts[i] ) )
    csvHelper.genCSV(".", "table_Details-dataset.csv", sizes, ["# instances", "# running times", "mean", "coefficient of variation", "Q(0.1)", "Q(0.25)", "median", "Q(0.75)", "Q(0.9)"], [numInsts, counts, means, coeffVars, q10s, q25s, medians, q75s, q90s])

    maxColsPerTable = 4
    with open(dirName+"/"+supportTexFileName, "w") as texFile:
        numTables = (threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(i*numCols, min((i+1)*numCols, threshold), sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s)
    with open(dirName+"/"+challengeTexFileName, "w") as texFile:
        numTables = (len(sizes)-threshold+maxColsPerTable-1)/maxColsPerTable
        numCols = (len(sizes)-threshold+numTables-1)/numTables
        for i in range(0, numTables):
            print >>texFile, prepareRuntimesTexTable(threshold+i*numCols, min(threshold+(i+1)*numCols, len(sizes)), sizes, counts, numInsts, means, coeffVars, q10s, q25s, medians, q75s, q90s)
    return counts
    
def genGnuplotFiles(dirName, sizes, stats, threshold, statistic):
    dirName = "."
    with open(dirName+"/gnuplotTrainFile.txt", 'w') as gnuplotFile: 
        for i in range(0, threshold):
            print >>gnuplotFile, "%d %f" % (sizes[i], stats[i])
    with open(dirName+"/gnuplotTestFile.txt", 'w') as gnuplotFile: 
        for i in range(threshold, len(sizes)):
            print >>gnuplotFile, "%d %f" % (sizes[i], stats[i])

def summarizeRuntimes(sizes, runtimes, numInsts, algName, dirName, statistic, perInstanceStatistic, threshold=0):
    #YP: Removed what I believe were old debugging messages.
    #print len(runtimes)
    #print len(runtimes[0])
    if threshold<=0 or threshold>=len(sizes):
        threshold = (3*len(sizes)+2)/5
    
    #YP: Calculate the per-instance statistics and use them in place of what used to be the running times.    
    runtimeStatistics = [ [calStatistic(runtimes[i][j], perInstanceStatistic) for j in range(0,len(runtimes[i]))] for i in range(0,len(sizes)) ]

    with open('runtime-file.log','w') as f_out:
        f_out.write('runtimeStatistics = ' + str(runtimeStatistics))

    counts = prepareRuntimesTexTables( sizes, runtimeStatistics, numInsts, threshold, dirName )
    
    stats = [ calStatistic( runtimeStatistics[i], statistic ) for i in range(0, len(sizes)) ]
    #print(stats)
    statIntervals = [ calStatisticIntervals( runtimeStatistics[i], statistic, numInsts[i] ) for i in range(0, len(sizes)) ]
    genGnuplotFiles( dirName, sizes, stats, threshold, statistic )
    return (counts, stats, statIntervals, threshold)

