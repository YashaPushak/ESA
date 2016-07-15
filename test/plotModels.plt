
#!/gnuplot
set print "fit-models.log"
FIT_LIMIT = 1e-9
EXP_p0 = 0.0001 
EXP_p1 = 1.01 
EXP(x) = EXP_p0*EXP_p1**x
fit EXP(x) "gnuplotTrainFile.txt" via EXP_p0,EXP_p1
pr "EXP fit: ", EXP_p0, " ", EXP_p1, " "
Poly_p0 = 1e-08 
Poly_p1 = 2 
Poly(x) = Poly_p0*x**Poly_p1
fit Poly(x) "gnuplotTrainFile.txt" via Poly_p0,Poly_p1
pr "Poly fit: ", Poly_p0, " ", Poly_p1, " "
SQRTEXP_p0 = 0.0001 
SQRTEXP_p1 = 1.01 
SQRTEXP(x) = SQRTEXP_p0*SQRTEXP_p1**(x**(0.5))
fit SQRTEXP(x) "gnuplotTrainFile.txt" via SQRTEXP_p0,SQRTEXP_p1
pr "SQRTEXP fit: ", SQRTEXP_p0, " ", SQRTEXP_p1, " "

#!/gnuplot

set terminal pdfcairo dashed fontscale 0.5
set termopt enhanced
#YP: Changed set logscale to set log x and set log y to avoid setting colour axis to log.
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

set output 'fittedModels.pdf'
plot [250:3250]\
    'gnuplotTrainFile.txt' title 'Support data', \
    EXP(x) w l lt 2 lc 3 title 'EXP. model', \
    Poly(x) w l lt 2 lc 4 title 'Poly. model', \
    SQRTEXP(x) w l lt 2 lc 5 title 'SQRTEXP. model', \
    'gnuplotTestFile.txt' using 1:7:8 with filledcurves lc 3 title 'EXP. model bootstrap intervals', \
    'gnuplotTestFile.txt' using 1:9:10 with filledcurves lc 4 title 'Poly. model bootstrap intervals', \
    'gnuplotTestFile.txt' using 1:11:12 with filledcurves lc 5 title 'SQRTEXP. model bootstrap intervals', \
    'gnuplotTestFile.txt' using 1:3:5:6:4 title 'Challenge data (with confidence intervals)' lc 1 ps 0.3 with candlesticks whiskerbars fs solid 1.0     #yerrorbars
