import math

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

def getSizesStr(sizes, stIdx, edIdx):
#    res = str(sizes[stIdx])
#    for i in range(stIdx+1, edIdx):
#        res += ","+str(sizes[i])
    return "%d\\leq n\\leq %d" % (sizes[stIdx], sizes[edIdx-1])

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
    res += "\\hline \n"
    for i in range(0, len(modelNames)):
        if i == 0:
            res += "\\multirow{%d}{*}{%s}" % (len(modelNames), escapeNonAlNumChars( algName ) )
        res += prepareTableRow(" & %s." % (modelNames[i]), [genInterval(numToTex(paraLos[i][j], 5), numToTex(paraUps[i][j], 5)) for j in range(0, len(paraLos[i])) ])
    res += "\\hline \n"
    res += "\\end{tabular} \n"
    with open(texFileName, "w") as texFile:
        print >>texFile, res
    
def genTexTableBootstrap(algName, modelNames, sizes, stIdx, edIdx, predLos, predUps, statIntervals, obsvLos, obsvUps, texFileName):
    res = ""
    for k in range(0, len(modelNames)):
        res += '''\\begin{tabular}{ccccc}
\\hline 
\\multirow{2}{*}{Solver} & \multirow{2}{*}{$n$} & Predicted confidence intervals & \\multicolumn{2}{c}{Observed median run-time}\\tabularnewline
 &  & %s. model  & Point estimates  & Confidence intervals\\tabularnewline
\\hline 
\\hline 
''' % (modelNames[k])
        for i in range(stIdx, edIdx):
            if i == stIdx:
                res += "\\multirow{%d}{*}{%s}" % (edIdx-stIdx, escapeNonAlNumChars( algName ) )
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

def genTexFile(fileDir, algName, instName, sizes, counts, numInsts, threshold, modelNames, modelReps, modelNumParas, numBootstrapSamples, statistic, numRunsPerInstance, perInstanceStatistic, numPerInstanceBootstrapSamples, tableDetailsSupportFileName, tableDetailsChallengeFileName, tableFittedModelsFileName, tableBootstrapIntervalsParaFileName, tableBootstrapIntervalsSupportFileName, tableBootstrapIntervalsChallengeFileName, tableBootstrapModelRMSEFileName, winnerSelectRule, figureCdfsFileName, figureFittedModelsFileName, figureFittedResiduesFileName, analysisSummary, latexTemplate):
    #Author: Zongxu Mu, Yasha Pushak
    #Last modified: March 21st, 2017
    modelsStr = "\\begin{itemize} \n"
    for i in range(0, len(modelNames)):
        modelsStr += "\\item $%s\\left[%s\\right]\\left(n\\right)=%s$ \quad{}(%d-parameter %s)" % (escapeNonAlNumChars(modelNames[i]), genParaStr(modelNumParas[i]), removeSubstrs(modelReps[i], '@@'), modelNumParas[i], modelNames[i])
    modelsStr += "\\end{itemize} \n"
    
    customCommands = ''
    for i in range(0, len(counts)):
        if counts[i]<numInsts[i]:
            customCommands += '\\renewcommand{\\medianInterval}[1]{\orange{#1}} \n'
            break
    #YP: Added a new command.
    if(not numRunsPerInstance == 1):
        customCommands += '\\renewcommand{\\randomizedAlgorithm}[1]{\yp{#1}} \n'

    #YP: added perInstanceStatistic, numRunsPerInstance, and numPerInstanceBootstrapSamples
    contents = {"customCommands":customCommands, "algName":escapeNonAlNumChars(algName), "instName":escapeNonAlNumChars(instName), "models":modelsStr, "numSizes":len(sizes), "largestSupportSize":sizes[threshold-1], "numBootstrapSamples":"%d" % numBootstrapSamples, "statistic":statistic, "table-Details-dataset-support":"\\input{%s}" % tableDetailsSupportFileName, "table-Details-dataset-challenge":"\\input{%s}" % tableDetailsChallengeFileName, "table-Fitted-models":"\\input{%s}" % tableFittedModelsFileName, "table-Bootstrap-intervals-of-parameters":"\\input{%s}" % tableBootstrapIntervalsParaFileName, "table-Bootstrap-intervals-support":"\\input{%s}" % tableBootstrapIntervalsSupportFileName, "table-Bootstrap-intervals-challenge":"\\input{%s}" % tableBootstrapIntervalsChallengeFileName, "figure-cdfs":"\\includegraphics[width=0.8\\textwidth]{%s}" % figureCdfsFileName, "figure-fittedModels":"\\includegraphics[width=0.8\\textwidth]{%s}" % (figureFittedModelsFileName), "figure-fittedResidues":"\\includegraphics[width=0.8\\textwidth]{%s}" % (figureFittedResiduesFileName), "supportSizes":getSizesStr(sizes, 0, threshold), "challengeSizes":getSizesStr(sizes, threshold, len(sizes)), "analysisSummary":analysisSummary[0], "analysisSummaryExplaination":analysisSummary[1], "perInstanceStatistic":perInstanceStatistic, "numRunsPerInstance":numRunsPerInstance, "numPerInstanceBootstrapSamples":numPerInstanceBootstrapSamples, "table-Bootstrap-model-RMSE":"\\input{%s}:" % tableBootstrapModelRMSEFileName, "winnerSelectRule": winnerSelectRule}
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

