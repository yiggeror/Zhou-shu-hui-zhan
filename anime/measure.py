"""Run a command and report its wall time and peak memory (largest resident set of any child process).
usage: python3 anime/measure.py CMD [ARGS...]"""
import resource
import subprocess
import sys
import time

t0 = time.time()
rc = subprocess.run(sys.argv[1:]).returncode
peak = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024 / 1024     # Linux: kB -> GB
print(f'MEASURE rc={rc} elapsed={time.time() - t0:.0f} s peak_rss={peak:.2f} GB', file=sys.stderr)
sys.exit(rc)
