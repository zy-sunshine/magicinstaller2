from miutils import printer
### -------- TestColorPrinter ----------

def TestColorPrinter():
    printer.i('Info test message\n')
    printer.d('Debug test message\n')
    printer.w('Warning test message\n')
    printer.e('Error test message\n')
    try:
        t = 1/0
    except:
        printer.exception('Exception test message\n')
        printer.beep()
    
if __name__ == '__main__':
    TestColorPrinter()
    