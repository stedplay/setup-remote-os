import sys
import time
from fabric import Connection, Config
from getpass import getpass
from invoke import run

def print_time(func):
  """
  Decorator to print execution time of function.
  """
  def _print_time(*args, **keyword):
    func_name = func.__name__
    print(f'Begin {func_name}()')
    begin_at = time.time()
    result = func(*args, **keyword)
    measured_time = time.time() - begin_at
    print(f'End {func_name}() {measured_time} second.')
    return result
  return _print_time

@print_time
def prepare():
  # Show usage.
  if len(sys.argv) != 4:
    sys.exit(f'Stop setup. \nUsage: python {sys.argv[0]} user_name@host_name:ssh_port new_ssh_port mail_address')

  # Arguments.
  print(f'sys.argv={sys.argv}')
  host = sys.argv[1]
  new_ssh_port = int(sys.argv[2])
  mail_address = sys.argv[3]
  password = getpass(f"{host.split(':')[0]}'s password? ")

  # Create connection.
  config = Config(overrides={'sudo': {'password': password, 'prompt': '[sudo] password: \n'}, 'run': {'echo': True}})
  c = Connection(host, connect_kwargs={"password": password}, config=config)
  # Check connection.
  c.run('date')

  # Check OS.
  is_ubuntu = bool(int(c.run('cat /etc/os-release | grep -c "Ubuntu 18.04"', warn=True).stdout.strip()))
  if not is_ubuntu:
    sys.exit('Stop setup. OS is not Ubuntu.')

  # Create ssh key.
  key_file_path = create_ssh_key(c)
  if key_file_path is None:
    sys.exit('Stop setup. Failed to create ssh key.')

  return c, new_ssh_port, key_file_path, mail_address

@print_time
def create_ssh_key(c):
  # Parameters of ssh key.
  key_type = 'ecdsa'
  key_bits = 256
  key_file_path = f'~/.ssh/{c.user}_{key_type}'         # <Remote user_name>_<key_type>
  comment = run('uname -n', hide=True).stdout.strip()   # Local hostname
  print(f"ssh-key's comment={comment}")
  # Create ssh-key in local machine.
  result = run(f'ssh-keygen -t {key_type} -b {key_bits} -f {key_file_path} -C {comment}', pty=True, echo=True, warn=True)
  if result.failed:
    return None
  run(f'chmod 600 {key_file_path}.pub', echo=True)
  run(f'ls -l {key_file_path}*', echo=True)
  return key_file_path

@print_time
def setup(c, new_ssh_port, key_file_path, mail_address):
  setup_timezone(c)

@print_time
def setup_timezone(c):
  # Set timezone.
  c.run('timedatectl')
  c.sudo('timedatectl set-timezone Asia/Tokyo')
  c.run('timedatectl')
  # Restart cron to update timezone.
  c.sudo('/etc/init.d/cron restart')


def main():
  # Prepare setup.
  c, new_ssh_port, key_file_path, mail_address = prepare()
  # Start setup.
  setup(c, new_ssh_port, key_file_path, mail_address)

main()
