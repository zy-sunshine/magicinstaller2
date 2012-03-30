import sys
import time
import traceback

'''colors, for nice output'''

class color_default:
    def __init__(self):
        self.name = 'default'
        self.black =    '\x1b[0;30m'
        self.red =  '\x1b[0;31m'
        self.green =    '\x1b[0;32m'
        self.yellow =   '\x1b[0;33m'
        self.blue = '\x1b[0;34m'
        self.magenta =  '\x1b[0;35m'
        self.cyan = '\x1b[0;36m'
        self.white =    '\x1b[0;37m'
        self.normal =   '\x1b[0m'
        self.bold = '\x1b[1m'
        self.clear =    '\x1b[J'

class color_bw:
    def __init__(self):
        self.name = 'bw'
        self.black =    '\x1b[0;30m'
        self.red =  '\x1b[0m'
        self.green =    '\x1b[0m'
        self.yellow =   '\x1b[0m'
        self.blue = '\x1b[0m'
        self.magenta =  '\x1b[0m'
        self.cyan = '\x1b[0m'
        self.white =    '\x1b[0m'
        self.normal =   '\x1b[0m'
        self.bold = '\x1b[0m'
        self.clear =    '\x1b[J'

### different useful prints
color_classes = {
    'default':  color_default,
    'bw':       color_bw
}
c = color_classes['default']()    

def printl(line, color = c.normal, bold = 0):
    "Prints a line with a color"
    out = ''
    if line and line[0] == '\r':
        clear_line()
    if bold:
        out = c.bold
    out = color + out + line + c.normal
    safe_write(out)
    safe_flush()
    
def i(line):
    "Prints an infor"
    out = ''
    out += c.green + c.bold + line + c.normal
    safe_write(out)
    safe_flush()
    
def d(line):
    "Prints an debug"
    out = ''
    out += c.blue + c.bold + line + c.normal
    safe_write(out)
    safe_flush()

def w(line):
    "Prints an warning"
    out = ''
    out += c.yellow + c.bold + line + c.normal + '\a'
    safe_write(out)
    safe_flush()
    
def e(line):
    "Prints an error"
    out = ''
    out += c.red + c.bold + line + c.normal + '\a'
    safe_write(out)
    safe_flush()

def exception(line):
    '''Prints an exception, but sometime it will only print one layer exception message, 
        so it will make debug from exception information hardly
        and better not use it in exception to print exception information'''
    out = '\n'
    out += ( c.cyan + c.bold + '! ' + c.normal ) * 3
    safe_write(out)
    safe_write(c.bold + line)
    safe_flush()
    traceback.print_exc()
    safe_write(c.normal)
    safe_write('\n')
    safe_flush()
    beep()

def beep(q = 0):
    "Beeps unless it's told to be quiet"
    if not q:
        printl('\a')


def safe_flush():
    """Safely flushes stdout. It fixes a strange issue with flush and
    nonblocking io, when flushing too fast."""
    c = 0
    while c < 100:
        try:
            sys.stdout.flush()
            return
        except IOError:
            c +=1
            time.sleep(0.01 * c)
    raise Exception, 'flushed too many times, giving up. Please report!'

def safe_write(text):
    """Safely writes to stdout. It fixes the same issue that safe_flush,
    that is, writing too fast raises errors due to nonblocking fd."""
    c = 1
    while c:
        try:
            sys.stdout.write(text)
            return
        except IOError:
            c += 1
            time.sleep(0.01 * c)
    raise Exception, 'wrote too many times, giving up. Please report!'
