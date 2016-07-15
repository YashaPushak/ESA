import os

def genCsvRow( data ):
    res = str( data[0] )
    for i in range(1, len(data)):
        res += ","+str(data[i])
    return res

def genCSV( dirName, fileName, headers, items, data):
    with open(dirName+"/"+fileName, "w") as file:
        print >>file, ","+genCsvRow(headers)
        for i in range(0, len(data)):
            print >>file, str(items[i])+","+genCsvRow(data[i])
