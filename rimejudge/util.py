import random
import string


def generate_random_code():
    return ''.join(random.sample(string.ascii_letters, 4))
