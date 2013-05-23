import os, time
os.system('mi.logging &')
time.sleep(1)
os.system('mi.server &')
time.sleep(1)
os.system('mi.client')

