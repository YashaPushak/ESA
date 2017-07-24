
#!/gnuplot
set print "fit-models.log"
#FIT_LIMIT = 1e-9
Exp_p0 = 0.0005 
Exp_p1 = 1.01 
Exp(x) = Exp_p0*Exp_p1**x
fit Exp(x) "gnuplotTrainFile.txt" via Exp_p0,Exp_p1
pr "Exp fit: ", Exp_p0, " ", Exp_p1, " "
RootExp_p0 = 0.0001 
RootExp_p1 = 1.001 
RootExp(x) = RootExp_p0*RootExp_p1**(x**(0.5))
fit RootExp(x) "gnuplotTrainFile.txt" via RootExp_p0,RootExp_p1
pr "RootExp fit: ", RootExp_p0, " ", RootExp_p1, " "
Poly_p0 = 5e-09 
Poly_p1 = 2.5 
Poly(x) = Poly_p0*x**Poly_p1
fit Poly(x) "gnuplotTrainFile.txt" via Poly_p0,Poly_p1
pr "Poly fit: ", Poly_p0, " ", Poly_p1, " "

