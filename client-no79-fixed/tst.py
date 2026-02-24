import itertools
import sys
import time

spinner = itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"])

while True:
    sys.stdout.write(f"\rProcessing {next(spinner)}")
    sys.stdout.flush()
    time.sleep(0.08)
