#!/gnuplot

set terminal pdfcairo dashed fontscale 0.5
set termopt enhanced
set print "plot-residues.log"

#set logscale y
set xlabel 'n'
set ylabel 'Residue [sec]'
set xtics auto  # (100, 200, 500, 1000)
# set format x "%2.0t{/Symbol \264}10^{%T}"
# set format y "10^{%T}"
set key left bottom
set grid xtics ytics mxtics mytics lc rgb '#999999' lw 1 lt 0
set style fill transparent solid 0.2 noborder

set arrow from @@thresholdSize@@,graph 0 to @@thresholdSize@@,graph 1 nohead lc 'black' dt 3

#set output 'fittedModels_residues.pdf'
#plot [100:1100]\
#    'residueFile.txt' using 1:2 w l lc 3 title 'Exp. Model Residues', \
#    'residueFile.txt' using 1:3 w l lc 4 title 'Poly. Model Residues', \
#
