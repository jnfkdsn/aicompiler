#!/usr/bin/env python3
from experiment import Experiment,log_directory
e=Experiment(log_directory(),show=True);e.observe();print(e.out)
if any(not c['passed'] for c in e.checks):raise SystemExit('Some checks failed')
