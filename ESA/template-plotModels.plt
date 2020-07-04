
set terminal pdfcairo dashed fontscale 0.5
set termoption enhanced
#set terminal qt font "Helvetica,24"
set log x
set log y
set format y "10^{%T}"
set format x "10^{%T}"
set grid xtics ytics mxtics mytics lc rgb '#999999' lw 1 lt 0
#set xtics add (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000)
set xtics (1,10,100,1000,10000,100000,1000000,10000000,100000000,1000000000)
set xrange[@@minSize@@/1.1:@@maxSize@@*1.1]
set yrange[@@minTime@@/10:@@maxTime@@*10]
set key bottom right spacing 0.95

#set format x "%2.0tx10^{%L}"
#set format y "%2.0tx10^{%L}"

set ytics (0.0001, 0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 1000000)
#set ytics add ("Censored" @@minNonZero@@/10.0, "Censored" @@cutoff@@)

set ylabel "CPU time [sec]"
set xlabel "n"

set style fill transparent solid 0.3 noborder

set arrow from @@thresholdSize@@,graph 0 to @@thresholdSize@@,graph 1 nohead lc 'black' dt 3 lw 2 
