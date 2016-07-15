
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

