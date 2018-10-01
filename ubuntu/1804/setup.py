import sys
from fabric import Connection, Config
from getpass import getpass

def prepare():
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

def setup():
  pass

def main():
  # Prepare setup.
  prepare()
  # Start setup.
  setup()

main()
