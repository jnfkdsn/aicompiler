#!/usr/bin/env python3
import argparse
from experiment import Experiment,log_directory
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--stage',choices=['buffer','shape','control','all'],default='buffer')
p.add_argument('--build',action='store_true')
a=p.parse_args();e=Experiment(log_directory(),show=True)
if a.build:e.build()
for name in ['buffer','shape','control'] if a.stage=='all' else [a.stage]:getattr(e,name)()
print(e.out)
if any(not c['passed'] for c in e.checks):raise SystemExit('Some checks failed')
