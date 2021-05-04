import sys
if sys.version[0] == 3:
    import pandas

    print('/'.join(pandas.__file__.replace('\\', '/').split('/')[:-2]))
else:
    import openpyxl
    print('/'.join(openpyxl.__file__.replace('\\', '/').split('/')[:-2]))