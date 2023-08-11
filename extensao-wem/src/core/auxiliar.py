global x
x = []
def setData(attributes):
    global x
    x = attributes

def getData():
    global x    
    return x[3],x[6],x[11]
#
def printData():
    global x
    print(x)
