# Explicit API functions
from api_functions import api_function1, api_function2
from package3 import api_function3

# API Packages
import package1, package2
import package3
from package4 import api_class1


# Defined functions

def defined_function_1(d_f_arg1, d_f_arg2):
    a = api_function1(d_f_arg1)
    b = (api_function2(d_f_arg2, d_f_arg1), api_function3())


def defined_function_2(d_f_arg1, d_f_arg2, d_f_arg3):
    api_function1()
    package1.p1_function1(d_f_arg1, d_f_arg2, d_f_arg3)
    a, b = api_class1.cl1_function1(1, 2, '3')


def defined_function_3():
    package1.p1_function1()
    package3.p3_function1()