import random


def generate_veriify_code() -> str:
    verify_code = ""
    for _i in range(4):
        verify_code += str(random.randint(0, 9))
    return verify_code
