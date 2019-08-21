import os
import shutil
import subprocess
import json
import tempfile

import yaml


def setup_deployment(dep):
    cleanup_deployment(dep)
    cmd = 'kubectl create -f -'
    subprocess.run(cmd, input=bytearray(dep.encode('utf-8')), shell=True, check=True,
                   stdout=subprocess.DEVNULL)


def cleanup_deployment(dep):
    dep = yaml.load(dep)
    cmd = 'kubectl delete deployment {dep}'.format(dep=dep['metadata']['name'])
    proc = subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if proc.stderr and 'not found' in str(proc.stderr, encoding='utf-8'):
        return
    proc.check_returncode()


def copy_driver_files(tmpdirname, cfg):
    curpath = os.path.dirname(os.path.abspath(__file__))
    # Copy adjust.py
    adjust_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'adjust.py'))
    adjust_dst = os.path.join(tmpdirname, 'adjust.py')
    shutil.copyfile(adjust_src, adjust_dst, follow_symlinks=True)
    # Create encoders folder
    os.mkdir(os.path.join(tmpdirname, 'encoders'))
    # Copy encoders/base.py
    base_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encoders', 'base.py'))
    base_dst = os.path.join(tmpdirname, 'encoders', 'base.py')
    shutil.copyfile(base_src, base_dst, follow_symlinks=True)
    # Copy encoders/base.py
    jvm_src = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encoders', 'jvm.py'))
    jvm_dst = os.path.join(tmpdirname, 'encoders', 'jvm.py')
    shutil.copyfile(jvm_src, jvm_dst, follow_symlinks=True)
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
    proc = subprocess.run(cmd, input=input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, check=True)
    assert proc.stdout
    stdout = json.loads(str(proc.stdout.strip(), encoding='utf-8').split('\n')[-1])
    return stdout, str(proc.stderr, encoding='utf-8'), proc.returncode


def query_dep(cfg):
    with tempfile.TemporaryDirectory() as dirname:
        copy_driver_files(dirname, cfg)
        prevcwd = os.getcwd()
        os.chdir(dirname)
        result, _, _ = run_driver('--query default')
        os.chdir(prevcwd)
        return result


def adjust_dep(cfg, driver_input):
    with tempfile.TemporaryDirectory() as dirname:
        copy_driver_files(dirname, cfg)
        prevcwd = os.getcwd()
        os.chdir(dirname)
        result, stderr, retcode = run_driver('default', input=bytearray(json.dumps(driver_input).encode('utf-8')))
        assert result.get('status') == 'ok', \
            'Error running ./adjust default.\nGot on stdout: {}\n' \
            'Got on stderr: {}\nReturn code: {}'.format(result, stderr, retcode)
        os.chdir(prevcwd)
        return result
