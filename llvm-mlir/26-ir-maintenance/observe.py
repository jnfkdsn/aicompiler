#!/usr/bin/env python3
import argparse
from experiment import Experiment,log_directory
p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
e=Experiment(log_directory(),show=True)
if a.build:e.build()
e.observe();print(e.out)
if any(not c['passed'] for c in e.checks):raise SystemExit('Some checks failed')
