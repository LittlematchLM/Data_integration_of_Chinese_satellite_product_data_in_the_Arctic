import re

def sort_key(s):
    if s:

        c = s.split('\\')[-1].split('_')[7]
        return c
