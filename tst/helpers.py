# import pytest

import os
import os.path
import subprocess
import json

def adjust(*args, stdin=None):
    """run 'adjust' with the current directory set to the dir where this module is found.
    Return a tuple (exitcode, parsed_stdout), the second item will be None if stdout was empty. An exception is raised if the process cannot be run or parsing stdout as json fails. A non-zero exit code from the process does not trigger an exception."""

    if stdin is not None and not isinstance(stdin, bytes):
        stdin = json.dumps(stdin)
        stdin = stdin.encode("UTF-8")

    mydir = os.path.dirname(os.path.abspath(__file__))
    old_dir = os.getcwd()
    try:
        os.chdir(mydir)
        r = subprocess.run(["./adjust"]+list(args), input=stdin, stdout=subprocess.PIPE, check=False)
    finally:
        os.chdir(old_dir)

    # on success, parse the output from the subprocess (if not empty)
    if r.stdout:
        # take only the last line, if there are many (this discards any 'progress' lines)
        stdout = r.stdout.strip().split(b"\n")[-1]
        # return r.returncode, json.loads(stdout) # direct json.loads() of bytes doesn't work before py 3.6
        print(">>>", stdout.decode("UTF-8"), "<<<")
        return r.returncode, json.loads(stdout.decode("UTF-8"))
    else:
        return r.returncode, None

CONFIG="config.yaml"
def setcfg(fname):
    """symlink the given name to config.yaml"""
    mydir = os.path.dirname(os.path.abspath(__file__))
    old_dir = os.getcwd()
    try:
        os.chdir(mydir)
        try:
            os.unlink(CONFIG)
        except FileNotFoundError: # py3.5 and later only
            pass
        os.symlink(fname, CONFIG)
    finally:
        os.chdir(old_dir)

