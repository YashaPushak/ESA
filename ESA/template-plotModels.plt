#!/gnuplot

set terminal pdfcairo dashed fontscale 0.5
set termopt enhanced
#set logscale
set log x
set log y
set xlabel 'n'
set ylabel 'CPU time [sec]'
set format y "10^{%T}"
set key top left 
#set key right bottom
set xtics auto
#(100, 200, 500, 1000)
set grid xtics ytics mxtics mytics lc rgb '#999999' lw 1 lt 0
set style fill transparent solid 0.2 noborder
#
#set output 'fittedModels_loglog.pdf'
#plot [100:1100]\
#    'gnuplotTrainFile.txt' title 'Support Data' lc 1, \
#    'gnuplotTestFile.txt' title 'Challenge Data' lc 7, \
#    'gnuplotTestFile.txt' using 1:5:6 with filledcurves lc 3 title 'Exp. Model Bootstrap Intervals', \
#    'gnuplotTestFile.txt' using 1:7:8 with filledcurves lc 4 title 'Poly. Model Bootstrap Intervals', \
#    e(x) w l lt 2 lc 3 title sprintf('Exp. Model: %2.5e {/Symbol \264} %2.5f^n', ae, be), \
#    p(x) w l lt 2 lc 4 title sprintf('Poly. Model: %2.5e {/Symbol \264} n^{%2.5f}', ap, bp)
#
