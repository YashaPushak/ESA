import math
import csvHelper

def fillModelRepsWValues( modelRep, valueTuple ):
    while modelRep.find("@@") > -1:
        stIdx = modelRep.find("@@")
        edIdx = modelRep.find("@@", stIdx+2)+2
        if edIdx<2:
            break
        elif edIdx!=stIdx+5:
            #print modelRep
            raise Exception
        id = modelRep[stIdx+2]
        modelRep = modelRep[0:stIdx] + valueTuple[ord(id)-ord('a')] + modelRep[edIdx:]
    return modelRep


def prepareTableRow(rowname, contents):
    res = rowname
    for c in contents:
        res += " & " + str(c)
    res += " \\tabularnewline \n"
    return res

def bold(string, math=False):
    if math == True:
        if("\\text{N/A}" in string):
            string = string.replace('\\text{N/A}','\\text{\\textbf{N/A}}')
        if string.find('$') > -1:
            return "$\\mathbf{"+string[string.find('$')+1:string.rfind('$')]+"}$"
        else:
            return "$\\mathbf{"+string+"}$"
    else:
        return "\\textbf{"+string+"}"
    
def numToTex(num, precision, scientific=False):
    if math.isnan(num):
        return "\\text{N/A}"
    if num==float('inf'):
        return "\\infty "
    if -num==float('inf'):
        return "-\\infty "
    strNum = ""
    if scientific == True:
        strNum = "%.*e" % (precision, num)
    else:
        strNum = "%.*g" % (precision, num)
    terms = strNum.split('e')
    if len(terms) > 1:
        terms[0] = terms[0].strip()
        return "%s\\times10^{%d}" % (terms[0], int(terms[1]))
#        length = len(terms[0])
#        if terms[0].find('.')>-1:
#            length = min(len(terms[0]), terms[0].find('.')+1+precision)
#        return "%s\\times10^{%d}" % (terms[0][0:length], int(terms[1]))
    else:
        return strNum.strip()
#        strNum = strNum.strip()
#        length = len(strNum)
#        if strNum.find('.')>-1:
#            length = min(len(strNum), strNum.find('.')+1+precision)
#        return strNum[0:length]

def genInterval(lo, up, level=0):
    res = "$\\left[%s,%s\\right]$" % (lo, up)
    if level>0:
        res = bold(res, True)
        if level == 4:
            res += bold('*')
        elif level == 3:
            res += bold('\\#')
        elif level == 2:
            res += bold('+')
    return res

def getSizesStr(sizesTrain, sizesTest, sizesThreshold, train):
#    res = str(sizes[stIdx])
#    for i in range(stIdx+1, edIdx):
#        res += ","+str(sizes[i])
    if(train):
        return "%d\\leq n\\leq %d" % (min(sizesTrain), sizesThreshold)
    else:
        return "%d< n \\leq %d" % (sizesThreshold,max(sizesTest))

def calConsistencyLevel(predLo, predUp, statIntervals, obsvLo, obsvUp):
    if predLo<=obsvLo and obsvUp<=predUp:
        return 4    # Fully Contained, i.e., the new Strongly Consistent
        #elif (predLo<=statIntervals[0] and statIntervals[1]<=predUp):
        #    return 3    # Strongly Consistent
        #elif max(predLo, statIntervals[0]) <= min(predUp, statIntervals[1]):
        #    return 2    # Consistent
    elif max(predLo, obsvLo) <= min(predUp, obsvUp):
        return 1    # Weakly Consistent
    else:
        return 0

def genTexTableBootstrapParas(algName, modelNames, modelNumParas, paraLos, paraUps, texFileName="table_Bootstrap-intervals-of-parameters.tex"):
    res = ""
    res += "\\begin{tabular}{cc|cc} \n"
    res += "\\hline \n"
    res += "Solver  & Model "
    for i in range(0, max(modelNumParas)):
        res += " & Confidence interval of $" + chr( ord('a')+i ) + "$ "
    res += "\\tabularnewline \n"
    res += "\\hline \n"*2
    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), escapeNonAlNumChars( algName ) )
        res += prepareTableRow(" & %s." % (modelNames[i]), [genInterval(numToTex(paraLos[i][j], 7), numToTex(paraUps[i][j], 7)) for j in range(0, len(paraLos[i])) ])
    res += "\\hline \n"
    res += "\\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res
    
def genTexTableBootstrap(algName, modelNames, sizes, predLos, predUps, statIntervals, obsvLos, obsvUps, texFileName, statistic):
    #Authors: ZM, YP
    #Last udpated: 2019-01-07
    res = ""
    for k in range(0, len(modelNames)):
        res += '''\\begin{tabular}{ccccc}
\\hline 
\\multirow{2}{*}{Solver} & \multirow{2}{*}{$n$} & Predicted confidence intervals & \\multicolumn{2}{c}{Observed ''' + statistic + '''  run-time}\\tabularnewline
 &  & %s. model  & Point estimates  & Confidence intervals\\tabularnewline
\\hline 
\\hline 
''' % (modelNames[k])
        for i in range(0, len(sizes)):
            if i == 0:
                res += "\\multirow{%d}{*}{%s}" % (i, escapeNonAlNumChars( algName ) )
            res += prepareTableRow(" & %d" % sizes[i], \
                 [ genInterval( numToTex(predLos[k][i], 4), numToTex(predUps[k][i], 4), calConsistencyLevel( predLos[k][i], predUps[k][i], statIntervals[i], obsvLos[i], obsvUps[i] ) ) ] + \
                 [ ("$%s$" % numToTex(statIntervals[i][0], 4)) if statIntervals[i][0]==statIntervals[i][1] else ( genInterval( numToTex(statIntervals[i][0], 4), numToTex(statIntervals[i][1], 4) ) ), genInterval( numToTex(obsvLos[i], 4), numToTex(obsvUps[i], 4) ) ] )
        res += "\\hline \n"
        res += "\\end{tabular} \n\n"

    with open(texFileName, "w") as texFile:
        print >>texFile, res

def genParaStr( numPara ):
    res = "a"
    for i in range(1, numPara):
        res += "," + chr( ord('a')+i )
    return res

def removeSubstrs( instr, substr ):
    idx = instr.find(substr)
    while idx != -1:
        instr = instr[0:idx] + instr[idx+len(substr):]
        idx = instr.find(substr)
    return instr

def escapeNonAlNumChars( instr ):
    dict = '&%$#_{}~^\\'
    res = ''
    for char in instr:
        if dict.find(char) != -1:
            res += '\\'
        if char == '~':
            res += 'textasciitilde '
        elif char == '^':
            res += 'textasciicircum '
        elif char == '\\':
            res += 'textbackslash '
        else:
            res += char
    return res

def genTexFile(fileDir, algName, instName, numObsv, sizesTrain, sizesTest, numInstsTrain, numInstsTest, sizeThreshold, modelNames, modelReps, modelNumParas, numBootstrapSamples, statistic, numRunsPerInstance, perInstanceStatistic, numPerInstanceBootstrapSamples, tableDetailsSupportFileName, tableDetailsChallengeFileName, tableFittedModelsFileName, tableBootstrapIntervalsParaFileName, tableBootstrapIntervalsSupportFileName, tableBootstrapIntervalsChallengeFileName, tableBootstrapModelLossFileName, figureCdfsFileName, figureFittedModelsFileName, figureFittedResiduesFileName, analysisSummary, winnerSelectRule, latexTemplate, alpha):
    #Author: Zongxu Mu, Yasha Pushak
    #Last modified: March 21st, 2017
    modelsStr = "\\begin{itemize} \n"
    for i in range(0, len(modelNames)):
        modelsStr += "\\item $%s\\left[%s\\right]\\left(n\\right)=%s$ \quad{}(%d-parameter %s)" % (escapeNonAlNumChars(modelNames[i]), genParaStr(modelNumParas[i]), removeSubstrs(modelReps[i], '@@'), modelNumParas[i], modelNames[i])
    modelsStr += "\\end{itemize} \n"
    
    customCommands = ''

    #YP: Added a new command.
    if(not numRunsPerInstance == 1):
        customCommands += '\\renewcommand{\\randomizedAlgorithm}[1]{#1} \n'
    if(statistic != 'mean'):
        customCommands += '\\renewcommand{\\quantileRegression}[1]{#1} \n'

    #YP: added perInstanceStatistic, numRunsPerInstance, and numPerInstanceBootstrapSamples
    contents = {
        "customCommands":customCommands, 
        "algName":escapeNonAlNumChars(algName), 
        "instName":escapeNonAlNumChars(instName), 
        "models":modelsStr, 
        "numObservations":numObsv,
        "largestSupportSize":sizeThreshold,
        "numBootstrapSamples":"%d" % numBootstrapSamples,
        "statistic":statistic,
        "table-Details-dataset-support":"\\input{%s}" % tableDetailsSupportFileName, 
        "table-Details-dataset-challenge":"\\input{%s}" % tableDetailsChallengeFileName,
        "table-Fitted-models":"\\input{%s}" % tableFittedModelsFileName, 
        "table-Bootstrap-intervals-of-parameters":"\\input{%s}" % tableBootstrapIntervalsParaFileName, 
        "table-Bootstrap-intervals-support":"\\input{%s}" % tableBootstrapIntervalsSupportFileName, 
        "table-Bootstrap-intervals-challenge":"\\input{%s}" % tableBootstrapIntervalsChallengeFileName, 
        "figure-cdfs":"\\includegraphics[width=0.8\\textwidth]{%s}" % figureCdfsFileName, 
        "figure-fittedModels":"\\includegraphics[width=0.8\\textwidth]{%s}" % (figureFittedModelsFileName), 
        "figure-fittedResidues":"\\includegraphics[width=0.8\\textwidth]{%s}" % (figureFittedResiduesFileName), 
        "supportSizes":getSizesStr(sizesTrain, sizesTest, sizeThreshold, True), 
        "challengeSizes":getSizesStr(sizesTrain, sizesTest, sizeThreshold, False), 
        "analysisSummary":analysisSummary[0], 
        "analysisSummaryExplaination":analysisSummary[1], 
        "perInstanceStatistic":perInstanceStatistic, 
        "numRunsPerInstance":numRunsPerInstance, 
        "numPerInstanceBootstrapSamples":numPerInstanceBootstrapSamples, 
        "table-Bootstrap-model-Loss":"\\input{%s}:" % tableBootstrapModelLossFileName, 
        "numInstsTrain": numInstsTrain, 
        "numInstsTest": numInstsTest, 
        "numInsts": numInstsTrain + numInstsTest, 
        "winnerSelectRule": winnerSelectRule,
        "alpha": alpha,
        "errorType": ("mean squared error" if statistic == 'mean'
                      else ("mean absolute error" if statistic == 'median'
                            else "weighted, mean absolute error"))
    }
    with open(latexTemplate, "r") as inFile:
        with open("scaling_%s.tex" % removeSubstrs(algName, '/'), "w") as outFile:
            for line in inFile:
                while line.find("@@") > -1:
                    stIdx = line.find("@@")
                    edIdx = line.find("@@", stIdx+2)+2
                    if edIdx<2:
                        break
                    id = line[stIdx+2:edIdx-2]
                    line = line[0:stIdx] + str(contents[id]) + line[edIdx:]
                print >>outFile, line.strip()


def makeTableFittedModels(fittedModels, lossesTrain, lossesTest, modelReps, modelNames, algName):
    #Author: Yasha Pushak
    #First Created: November 17th, 2016 (Approx.)
    #Last updated: 2019-01-04
    #I pulled the original code for this out of the fitModels function
    #and created a new one here.

    csvHelper.genCSV( ".", "table_Fitted-models.csv", ["Model Parameters", "Support Loss", "Challenge Loss"], \
        [ algName+" "+modelName+". Model" for modelName in modelNames ], \
        [ [ list(fittedModels[k]), lossesTrain[k], lossesTest[k]] for k in range(0, len(modelNames)) ] )

    genFittedModelsTexTable(algName, modelNames, modelReps, fittedModels, lossesTrain, lossesTest)


def genFittedModelsTexTable(algName, modelNames, modelReps, fittedModels, lossesTrain, lossesTest, texFileName="table_Fitted-models.tex"):
    res = ""
    res += "\\begin{tabular}{ccccc} \n"
    res += "\\hline \n"
    res += " &  & \multirow{2}{*}{Model} & Support & Challenge\\tabularnewline \n"
    res += " &  &  & loss  & loss\\tabularnewline \n"
    res += "\\hline \n"
    res += "\\hline \n"
    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), escapeNonAlNumChars( algName ) )
        if lossesTest[i] == min(lossesTest):
            modelParasTuple = ()
            for k in range(0, len(fittedModels[i])):
                modelParasTuple += ( numToTex(fittedModels[i][k], 7), )
            res += prepareTableRow(" & %s. Model" % modelNames[i], \
                [ bold( fillModelRepsWValues( modelReps[i], modelParasTuple ), True ), \
                bold( numToTex(lossesTrain[i], 5), True ), \
                bold( numToTex(lossesTest[i], 5), True )] )
        else:
            modelParasTuple = ()
            for k in range(0, len(fittedModels[i])):
                modelParasTuple += ( numToTex(fittedModels[i][k], 7) ,)
            res += prepareTableRow(" & %s. Model" % modelNames[i], \
                [ "$%s$" % fillModelRepsWValues( modelReps[i], modelParasTuple ), \
                "$%s$" % numToTex( lossesTrain[i] , 5 ), \
                "$%s$" % numToTex( lossesTest[i], 5 )] )
        #    " & $6.89157\\times10^{-4}\\text{\\ensuremath{\\times}}1.00798{}^{n}$  & 0.0008564  & 0.7600")
    res += "\\hline \n"
    res += "\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res



def makeTableBootstrapModelLosses(ilossTrain, ilossTest, modelNames, algName):
    #Author: Yasha Pushak
    #First Created: March 21st, 2017
    #Last updated: 2019-01-04

    tableName = 'table_Bootstrap-model-loss'

    csvHelper.genCSV( ".", tableName + ".csv", ["Support Loss Confidence Interval", "Challenge Loss Confidence Interval"], \
        [ algName+" "+modelName+". Model" for modelName in modelNames ], \
        [ [ilossTrain[k], ilossTest[k]] for k in range(0, len(modelNames)) ] )

    winnerSelectRule = genBootstrapModelRMSETexTable(algName, modelNames, ilossTrain, ilossTest, tableName + '.tex')

    return tableName, winnerSelectRule


def genBootstrapModelRMSETexTable(algName, modelNames, ilossTrain, ilossTest, texFileName="table_Bootstrap-model-loss.tex"):
    #Author: YP
    #Created: 2017-03-21
    #Last Updated: 2019-01-04
    res = ""
    res += "\\begin{tabular}{cc|c|c} \n"
    res += "\\hline \n"
    res += " Solver & Model & Support Loss  & Challenge Loss \\tabularnewline"
    res += "\\hline \n"
    res += "\\hline \n"

    #We highlight "winners" only if there are models with non-overlapping challenge intervals. 
    #Then, we select only those models that overlap with the smallest upperbound.
    winners = []
    smallestUp = float('inf')
    for iloss in ilossTest:
        smallestUp = min(smallestUp,iloss[1])
    for i in range(0,len(ilossTest)):
        if(ilossTest[i][0] <= smallestUp):
            winners.append(i)
    if(len(winners) == len(modelNames)):
        winners = []        

    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), escapeNonAlNumChars( algName ) )
        if i in winners:
            #passing 1 to genInterval makes it bold.
            res += prepareTableRow(" & %s." % modelNames[i], \
                [genInterval( numToTex(ilossTrain[i][0], 5), numToTex(ilossTrain[i][1], 5), 1), \
                genInterval( numToTex(ilossTest[i][0], 5), numToTex(ilossTest[i][1], 5), 1), \
                ] )
        else:
            res += prepareTableRow(" & %s." % modelNames[i], \
                [genInterval( numToTex(ilossTrain[i][0], 5), numToTex(ilossTrain[i][1], 5) ), \
                genInterval( numToTex(ilossTest[i][0], 5), numToTex(ilossTest[i][1], 5) ), \
                ] )
        #    " & $6.89157\\times10^{-4}\\text{\\ensuremath{\\times}}1.00798{}^{n}$  & 0.0008564  & 0.7600")
    res += "\\hline \n"
    res += "\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res

    if(len(winners) > 0):
        winnerSelectRule = "The model with the smallest lower bound is shown in boldface, as well as any models with overlapping intervals."
    else:
        winnerSelectRule = ''

    return winnerSelectRule

