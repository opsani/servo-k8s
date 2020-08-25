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
        # print(">>>", stdout.decode("UTF-8"), "<<<")
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

def run(cmd):
    """basic execution of a command, stdout and stderr are not redirected (end up in py.test logs), raise exception on errors"""
    # nosec below as test suite is not intended to run in production environment, invocations all use static input
    return subprocess.check_output(cmd, shell=True)

def silent(cmd):
    """run a command and ignore stdout/stderr and non-zero exit status"""
    # nosec below as test suite is not intended to run in production environment, invocations all use static input
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False) # nosec

# === 
import shutil
import tempfile
import yaml


def setup_deployment(dep):
    cleanup_deployment(dep)
    cmd = 'kubectl create -f -'
    # nosec below as test suite is not intended to run in production environment, invocations all use static input
    subprocess.run(cmd, input=bytearray(dep.encode('utf-8')), shell=True, check=True, # nosec
                   stdout=subprocess.DEVNULL)


def cleanup_deployment(dep):
    dep = yaml.safe_load(dep)
    cmd = 'kubectl delete deployment {dep}'.format(dep=dep['metadata']['name'])
    # nosec below as test suite is not intended to run in production environment, invocations all use static input
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) # nosec
    if proc.stderr and 'not found' in str(proc.stderr, encoding='utf-8'):
        return
    proc.check_returncode()

def k_get(qry):
    """run kubectl get and return parsed json output"""
    if not isinstance(qry, list):
        qry = [qry]
    # this will raise exception if it fails:
    output = subprocess.check_output(['kubectl', 'get', '--output=json'] + qry)
    output = output.decode('utf-8')
    output = json.loads(output)
    return output


def copy_driver_files(tmpdirname, cfg):
    curpath = os.path.dirname(os.path.abspath(__file__))
    # Copy adjust.py
    adjust_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'adjust.py'))
    adjust_dst = os.path.join(tmpdirname, 'adjust.py')
    shutil.copyfile(adjust_src, adjust_dst, follow_symlinks=True)
    # Create encoders folder
    os.mkdir(os.path.join(tmpdirname, 'encoders'))
    try:
        # Copy encoders/base.py
        base_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encoders', 'base.py'))
        base_dst = os.path.join(tmpdirname, 'encoders', 'base.py')
        shutil.copyfile(base_src, base_dst, follow_symlinks=True)
        # Copy encoders/base.py
        jvm_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encoders', 'jvm.py'))
        jvm_dst = os.path.join(tmpdirname, 'encoders', 'jvm.py')
        shutil.copyfile(jvm_src, jvm_dst, follow_symlinks=True)
    except:
        pass
    # Copy adjust
    adjust_drv_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'adjust'))
    adjust_drv_dst = os.path.join(tmpdirname, 'adjust')
    shutil.copyfile(adjust_drv_src, adjust_drv_dst, follow_symlinks=True)
    shutil.copymode(adjust_drv_src, adjust_drv_dst, follow_symlinks=True)
    # Create config.yaml
    config_dst = os.path.join(tmpdirname, 'config.yaml')
    with open(config_dst, 'w') as f:
        f.write(cfg)


def run_driver(params, input=None):
    cmd = './adjust {}'.format(params)
    # nosec below as test suite is not intended to run in production environment, invocations all use static input
    try:
        proc = subprocess.run(cmd, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True) # nosec
    except subprocess.CalledProcessError as cpe:
        raise Exception('Command "{}" returned exit status {} \n\nSTDOUT: {}\n\nSTDERR: {}'.format(cmd, cpe.returncode, cpe.stdout, cpe.stderr))
    assert proc.stdout
    # Driver output debug
    # print(proc.stdout)
    stdout = json.loads(str(proc.stdout.strip(), encoding='utf-8').split('\n')[-1])
    return stdout, str(proc.stderr, encoding='utf-8'), proc.returncode


def query_dep(cfg):
    with tempfile.TemporaryDirectory() as dirname:
        copy_driver_files(dirname, cfg)
        prevcwd = os.getcwd()
        os.chdir(dirname)
        try:
            result, _, _ = run_driver('--query default')
        finally:
            os.chdir(prevcwd)
        return result


def adjust_dep(cfg, driver_input):
    with tempfile.TemporaryDirectory() as dirname:
        copy_driver_files(dirname, cfg)
        prevcwd = os.getcwd()
        os.chdir(dirname)
        try:
            result, stderr, retcode = run_driver('default', input=bytearray(json.dumps(driver_input).encode('utf-8')))
            assert result.get('status') == 'ok', \
                'Error running ./adjust default.\nGot on stdout: {}\n' \
                'Got on stderr: {}\nReturn code: {}'.format(result, stderr, retcode)
        finally:
            os.chdir(prevcwd)
        return result
