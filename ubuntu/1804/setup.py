import sys
from getpass import getpass

def prepare():
  # Arguments.
  print(f'sys.argv={sys.argv}')
  host = sys.argv[1]
  new_ssh_port = int(sys.argv[2])
  mail_address = sys.argv[3]
  password = getpass(f"{host.split(':')[0]}'s password? ")

def setup():
  pass

def main():
  # Prepare setup.
  prepare()
  # Start setup.
  setup()

main()
