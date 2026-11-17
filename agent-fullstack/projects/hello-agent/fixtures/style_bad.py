# 风格糟糕但功能正确的例子:该送"风格科"
def Calc(x,y):
    R=x+y
    return R

def PrintResult(Val):
    if Val>100:
        print("big:"+str(Val))
    else:
        print("small:"+str(Val))

Result=Calc(30,50)
PrintResult(Result)
