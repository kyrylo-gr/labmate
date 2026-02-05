def abc(p):
    return p * 2


d1 = 2
d2 = d1
d3 = abc(d1)


def local_switch(param):
    if param == "a":
        return "param_a"
    return "param_b"


str_1 = "a"
str_2 = local_switch(str_1)

boolean = True
