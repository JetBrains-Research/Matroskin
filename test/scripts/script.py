from package1 import fun0, fun1, fun2, fun3
from package2 import tmp1, tmp2, tmp3; from package3 import tmp4
import package
import new_package as p2

# Comment line1
# Comment line2
# Comment line3
class A:
    def __init__(self):
        self.a = 0
        self.arr = []

    def method1(self):
        self.method3(1, 1, 1)

    def method2(self):
        self.method3(2, 2, 2)
        self.arr.append(2)

    def method3(self, param1, param2, param3):
        self.b = 2
        self.a = 3

        # Comment line4
        def inner_method():
            self.c = 3
            self.a = 4

    def __private(self, p1):
        package.p_function4(1, self.method3(2, 2, 2), 3, 4)

    def _protected1(self, p1):
        pass

    def _protected2(self, p1, p2):
        # Comment line5
        pass


var1, var2, var3 = 1, 2, 3
var4 = []
var5 = (1, 2, [3, 4, 5])
var6 = fun1(fun2()), fun3(var5)
var7, var8 = fun3(2), 2

def foo(f1):
    goo()
    goo()
    print('foo')


def goo(g1, g2):
    foo()
    doo()
    doo()
    print('goo')


def doo(d1, d2, d3):
    goo()
    package.p_function3(1, 2, 3)
    goo()
    print('doo')


foo(1)
foo(1)
foo(1)
foo(1)
foo(1)
b = goo(1)
c = doo(1); d = foo(1)
fun0()
fun0()
fun0()
a = fun0()**fun1() - fun3()
package.p_function1(1,2)
var9 = package.p_function2(fun0(), 2)
var10, var11 = p2.new_function()

var12 = A.method2()
A.method2()
loo(10)
var13 = kek.lol()

'''
Comments count = 5 (5)
Blank lines count = 17 (17)
Classes = 1 (1)
classes_comments = 5 (5)
mean new methods = 7 (7)
mean attributes count = 4 (4)
coupling between functions = 7 (5) !!!
coupling between methods = 0 (2) !!!
Api functions count = 4 (2)
defined functions_count = 10 (10)
api functions uses = 5 (9)
defined functions uses = 8 (11)
defined functions = doo _protected1 foo method2 __init__ _protected2 method1 method3 goo __private
unused imports count = 4 (4)
variables = a var5 var4 b var6 d c

'''