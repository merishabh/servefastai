import subprocess

def test_local(self):
    # TODO: Handle exit condition gracefully by forking the process
    subprocess.call('cd ' + self.deploy_dir + ' && python server.py', shell=True)