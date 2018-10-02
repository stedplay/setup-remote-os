import sys
from fabric import Connection, Config
from getpass import getpass

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

def setup():
  pass

def main():
  # Prepare setup.
  prepare()
  # Start setup.
  setup()

main()
