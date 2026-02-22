#!/usr/bin/env python3

import signal
import time

class TimeoutException(Exception):
    pass

def handler(signum, frame):
    raise TimeoutException('Total timeout for download exceeded')

signal.signal(signal.SIGALRM, handler)
signal.alarm(10)

# use "signal.alarm(0)" to disable timeout after critical section

try:
    time.sleep(20)
except TimeoutException:
    print('reached total timeout')
