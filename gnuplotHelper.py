import os
import numpy
import summarizeRuntimes

def addModelNameToP( md, mn ):
    idx = md.find( 'p', 0 )
    while idx>-1:
        if idx+1<len(md) and md[idx+1].isdigit():
            md = md[0:idx] + mn + "_" + md[idx:]
        idx = md.find( 'p', idx+len(mn)+2)
    return md
    
def genGnuplotScripts( modelNames, modelDefs, modelNumParas, modelParaDefaults, dirName, sizes, modelPlotTemplate, residuePlotTemplate ):
    fitCmd = '''
#!/gnuplot
set print "fit-models.log"
FIT_LIMIT = 1e-9
'''
    for i in range(0, len(modelNames)):
        paraListStr = ''
        for j in range(0, modelNumParas[i]):
            fitCmd += '%s_p%d = %g \n' % (modelNames[i], j, modelParaDefaults[i][j])
            if j>0:
                paraListStr += ','
            paraListStr += '%s_p%d' % (modelNames[i], j)
        fitCmd += '%s(x) = %s\n' % (modelNames[i], addModelNameToP( modelDefs[i], modelNames[i] ))
        fitCmd += 'fit %s(x) "gnuplotTrainFile.txt" via %s\n' % (modelNames[i], paraListStr)  #'%s_p0'%modelNames[i])
        fitCmd += 'pr "%s fit: "' % modelNames[i]
        for j in range(0, modelNumParas[i]):
            fitCmd += ', %s_p%d, " "' % (modelNames[i], j)
        fitCmd += '\n'

    with open( dirName + "/fitModels.plt", "w" ) as fitScriptFile:
        print >>fitScriptFile, fitCmd
    try:
        os.mkdir( dirName + "/bootstrap" )
    except:
        pass
    os.system( "cp %s/fitModels.plt %s/bootstrap/bootstrap-fit.plt" % (dirName, dirName))

    os.system( "cp %s/fitModels.plt %s/plotModels.plt" % (dirName, dirName))
    os.system( "cat %s/%s >>%s/plotModels.plt" % (dirName, modelPlotTemplate, dirName))
    plotCmd = """
set output '%s'
plot [%d:%d]\\
    'gnuplotTrainFile.txt' title 'Support data'""" % ("fittedModels.pdf", max(1, sizes[0]-(sizes[1]-sizes[0])/2), sizes[-1]+(sizes[-1]-sizes[-2])/2)
    for i in range(0, len(modelNames)):
        plotCmd += """, \\
    %s(x) w l lt 2 lc %d title '%s. model'""" % (modelNames[i], 3+i, modelNames[i])
    for i in range(0, len(modelNames)):
        plotCmd += """, \\
    'gnuplotTestFile.txt' using 1:%d:%d with filledcurves lc %d title '%s. model bootstrap intervals'""" % (7+2*i, 8+2*i, 3+i, modelNames[i])
    plotCmd += """, \\
    'gnuplotTestFile.txt' using 1:3:5:6:4 title 'Challenge data (with confidence intervals)' lc 1 ps 0.3 with candlesticks whiskerbars fs solid 1.0     #yerrorbars"""
    with open( dirName + "/plotModels.plt", "a" ) as plotScriptFile:
        print >>plotScriptFile, plotCmd

    os.system( "cat %s/%s >>%s/plotResidues.plt" % (dirName, residuePlotTemplate, dirName))
    plotCmd = """
set output '%s'
plot [%d:%d]\\""" % ("fittedResidues.pdf", max(1, sizes[0]-(sizes[1]-sizes[0])/2), sizes[-1]+(sizes[-1]-sizes[-2])/2)
    for i in range(0, len(modelNames)):
        plotCmd += """
'residueFile.txt' using 1:%d w l lc %d title '%s. Model Residues', \\""" % (2+i, 3+i, modelNames[i])
    for i in range(0, len(modelNames)):
        plotCmd += """
'residueTrainFile.txt' using 1:%d lc %d pt 1 %s, \\""" % (2+i, 3+i, "title 'Support Data'" if i==0 else "notitle")
    for i in range(0, len(modelNames)):
        plotCmd += """
'residueTestFile.txt' using 1:%d lc %d pt 2 %s, \\""" % (2+i, 3+i, "title 'Challenge Data'" if i==0 else "notitle")
    plotCmd += """
0 w l lc 7 lt 1 notitle"""
    with open( dirName + "/plotResidues.plt", "a" ) as plotScriptFile:
        print >>plotScriptFile, plotCmd

def genGnuplotFiles(dirName, sizes, runtimes, statIntervals, obsvLos, obsvUps, predLos, predUps, threshold, statistic):
    dirName = "."
    with open(dirName+"/gnuplotTrainFile.txt", 'w') as gnuplotFile: 
        for i in range(0, threshold):
            gnuplotFileLine = "%d %f %f %f" % (sizes[i], runtimes[i], obsvLos[i], obsvUps[i])
            for j in range(0, len(predLos)):
                gnuplotFileLine += " %f %f" % (predLos[j][i], predUps[j][i])
            print >>gnuplotFile, gnuplotFileLine
    with open(dirName+"/gnuplotTestFile.txt", 'w') as gnuplotFile: 
        for i in range(threshold, len(sizes)):
            gnuplotFileLine = "%d %f %f %f %f %f" % (sizes[i], runtimes[i], statIntervals[i][0], statIntervals[i][1], obsvLos[i], obsvUps[i])
            for j in range(0, len(predLos)):
                gnuplotFileLine += " %f %f" % (predLos[j][i], predUps[j][i])
            print >>gnuplotFile, gnuplotFileLine

