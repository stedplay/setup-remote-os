import re
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
  # Show execution date.
  run('date')
  # Show usage.
  if len(sys.argv) != 5:
    sys.exit(f'Stop setup. \nUsage: python {sys.argv[0]} user_name@host_name:ssh_port new_ssh_port mail_address')

  # Arguments.
  print(f'sys.argv={sys.argv}')
  ssh_user_name, host_fqdn, ssh_port = re.split('[@:]', sys.argv[1])
  new_ssh_user_name = sys.argv[2]
  new_ssh_port = int(sys.argv[3])
  mail_address = sys.argv[4]
  ssh_user_password = getpass(f"{ssh_user_name}@{host_fqdn}'s password?: ")

  # Create connection.
  c = connect(ssh_user_name, host_fqdn, ssh_port, ssh_user_password)
  # Check OS.
  is_ubuntu = bool(int(c.run('cat /etc/os-release | grep -c "Ubuntu 18.04"', warn=True).stdout.strip()))
  if not is_ubuntu:
    sys.exit('Stop setup. OS is not Ubuntu.')

  return c, new_ssh_user_name, new_ssh_port, mail_address

@print_time
def connect(ssh_user_name, host_fqdn, ssh_port, ssh_user_password):
  # Create connection.
  config = Config(overrides={'sudo': {'password': ssh_user_password, 'prompt': '[sudo] password: \n'}, 'run': {'echo': True}})
  c = Connection(host=host_fqdn, user=ssh_user_name, port=ssh_port, connect_kwargs={"password": ssh_user_password}, config=config)
  # Check connection.
  c.run('echo "Login user is $(whoami)"')
  return c

@print_time
def setup(c, new_ssh_user_name, new_ssh_port, mail_address):
  c_ = add_user(c, new_ssh_user_name)
  key_file_path = create_ssh_key(c_)
  setup_timezone(c_)
  setup_apt(c_)
  setup_sshd(c_, new_ssh_port, key_file_path)
  setup_iptables(c_, new_ssh_port)
  disable_ipv6(c_)
  setup_postfix(c_, mail_address)
  setup_logwatch(c_)
  setup_docker(c_)
  reboot(c_)

@print_time
def add_user(c, new_ssh_user_name):
  if new_ssh_user_name != c.user:
    # Ask new ssh user's password twice.
    while True:
      new_ssh_user_password = getpass(f"{new_ssh_user_name}@{c.host}'s password?: ")
      agein_new_ssh_user_password = getpass(f"Enter same password again: ")
      if new_ssh_user_password == agein_new_ssh_user_password:
        break
      print('Passwords do not match. Try again.')
    # Add user.
    c.sudo(f'useradd -G sudo -m -s /bin/bash {new_ssh_user_name}')
    # Set password of new user.
    c.sudo(f'sh -c "echo {new_ssh_user_name}:{new_ssh_user_password} | chpasswd"', hide=True)
    print(f'sh -c "echo {new_ssh_user_name}:*** | chpasswd"')
    # Disconnect.
    c.close()
    # Create new connection.
    c_ = connect(new_ssh_user_name, c.host, c.port, new_ssh_user_password)
  else:
    print('Not add user.')
    c_ = c
  return c_

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
    sys.exit('Stop setup. Failed to create ssh key.')
  run(f'chmod 600 {key_file_path}.pub', echo=True)
  run(f'ls -l {key_file_path}*', echo=True)
  return key_file_path

@print_time
def setup_timezone(c):
  # Set timezone.
  c.run('timedatectl')
  c.sudo('timedatectl set-timezone Asia/Tokyo')
  c.run('timedatectl')
  # Restart cron to update timezone.
  c.sudo('/etc/init.d/cron restart')

@print_time
def setup_apt(c):
  # Update package list.
  c.sudo('apt update')
  # Install basic package.
  c.sudo('apt -y install curl git jq')
  # Stop automatic updates other than Ubuntu security updates.
  ## Create 20auto-upgrades
  c.sudo('apt -y install unattended-upgrades')
  c.sudo(r'sh -c "echo \"unattended-upgrades unattended-upgrades/enable_auto_updates boolean true\" | debconf-set-selections"')
  c.sudo('dpkg-reconfigure --frontend noninteractive --priority=low unattended-upgrades')
  ## Edit 20auto-upgrades
  c.sudo('cp -p /etc/apt/apt.conf.d/20auto-upgrades /etc/apt/apt.conf.d/20auto-upgrades_org')
  c.sudo("sed -i 's/^APT::Periodic::Update-Package-Lists \"1\";$/APT::Periodic::Update-Package-Lists \"0\";/' /etc/apt/apt.conf.d/20auto-upgrades")
  c.sudo("sed -i 's/^APT::Periodic::Unattended-Upgrade \"1\";$/APT::Periodic::Unattended-Upgrade \"0\";/' /etc/apt/apt.conf.d/20auto-upgrades")
  c.run('diff /etc/apt/apt.conf.d/20auto-upgrades /etc/apt/apt.conf.d/20auto-upgrades_org', warn=True)

@print_time
def setup_sshd(c, ssh_port, key_file_path):
  # Edit sshd_config.
  c.sudo('cp -p /etc/ssh/sshd_config /etc/ssh/sshd_config_org')
  # Change ssh port number.
  c.sudo(fr'sed -i "s/^#\?Port.*$/Port {ssh_port}/" /etc/ssh/sshd_config')
  # Prohibit ssh login as root user.
  c.sudo(r'sed -i "s/^#\?PermitRootLogin.*$/PermitRootLogin no/" /etc/ssh/sshd_config')
  # Enable public key authentication.
  c.sudo(r'sed -i "s/^#\?PubkeyAuthentication.*$/PubkeyAuthentication yes/" /etc/ssh/sshd_config')
  # Prohibit ssh login with password.
  c.sudo(r'sed -i "s/^#\?PasswordAuthentication.*$/PasswordAuthentication no/" /etc/ssh/sshd_config')
  # Set to send packets every 5 minutes so that ssh connection is not disconnected.
  c.sudo(r'sed -i "s/^#\?ClientAliveInterval.*$/ClientAliveInterval 300/" /etc/ssh/sshd_config')
  # Specify the user who is allowed ssh login.
  c.sudo(f'sh -c "echo \'AllowUsers {c.user}\' >> /etc/ssh/sshd_config"')
  c.run('diff /etc/ssh/sshd_config /etc/ssh/sshd_config_org', warn=True)

  # Create remote user's .ssh directory.
  ssh_dir = f'/home/{c.user}/.ssh/'
  c.sudo(f'mkdir -p {ssh_dir}', user=c.user)
  c.sudo(f'chmod 700 {ssh_dir}')
  # Upload public key of ssh.
  ## Get full path of key file with the tilde(~) expanded.
  key_file_full_path = run(f'echo {key_file_path}', hide=True).stdout.strip()
  pub_key_string = run(f'cat {key_file_full_path}.pub', hide=True).stdout.strip()
  c.run(f'echo {pub_key_string} >> {ssh_dir}authorized_keys')
  c.run('ls -la ~/.ssh/')

  # Check the validity of the configuration file and sanity of the keys.
  c.sudo('sshd -t')
  # Restart sshd
  c.sudo('/etc/init.d/ssh restart', warn=True)

@print_time
def setup_iptables(c, ssh_port):
  # Accept connected packet.
  c.sudo('iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT')
  # Accept icmp packet.
  c.sudo('iptables -A INPUT -p icmp -j ACCEPT')
  # Accept the packet whose destination is local loopback address.
  c.sudo('iptables -A INPUT -i lo -j ACCEPT')
  # Accept ssh packet whose destination is ssh_port.
  c.sudo(f'iptables -A INPUT -m state --state NEW -m tcp -p tcp --dport {ssh_port} -j ACCEPT')

  # Log INPUT or FORWARD packet.
  c.sudo('iptables -A INPUT -j LOG --log-prefix "INPUT_DROP:"')
  c.sudo('iptables -A FORWARD -j LOG --log-prefix "FORWARD_DROP:"')
  # Set default policy.
  c.sudo("iptables -P INPUT DROP")
  c.sudo("iptables -P FORWARD DROP")
  c.sudo("iptables -P OUTPUT ACCEPT")

  # Show current setting.
  c.sudo("iptables -L -nv --line-numbers")
  # Prevent apt from showing dialogs during installation of iptables-persistent.
  # https://askubuntu.com/questions/339790/how-can-i-prevent-apt-get-aptitude-from-showing-dialogs-during-installation
  c.sudo('sh -c "echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections"')
  c.sudo('sh -c "echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections"')
  # Install iptables-persistent to save setting of iptables.
  c.sudo('apt -y install iptables-persistent')

@print_time
def disable_ipv6(c):
  # Disable IPv6 in OS immediately.
  c.run('ip a')
  c.sudo('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
  c.run('ip a')
  # Disable IPv6 in OS permanently.
  c.sudo('cp -p /etc/default/grub /etc/default/grub_org')
  c.sudo(r'sed -i "s/^GRUB_CMDLINE_LINUX=\"\(.*\)\"$/GRUB_CMDLINE_LINUX=\"ipv6.disable=1 \1\"/" /etc/default/grub')
  c.run('diff /etc/default/grub /etc/default/grub_org', warn=True)
  c.sudo('update-grub')

@print_time
def setup_postfix(c, mail_address):
  # Prevent apt from showing dialogs during installation of postfix.
  # https://serverfault.com/questions/143968/automate-the-installation-of-postfix-on-ubuntu
  c.sudo(r'sh -c "echo postfix postfix/main_mailer_type string \"Internet Site\" | debconf-set-selections"')
  c.sudo(f'sh -c "echo postfix postfix/mailname string $(uname -n) | debconf-set-selections"')
  # Install postfix.
  c.sudo('apt -y install postfix')

  # Forward mail addressed to root to mail_address.
  c.sudo('cp -p /etc/aliases /etc/aliases_org')
  c.sudo(fr'sh -c "echo \"root: {mail_address}\" >> /etc/aliases"')
  c.run('diff /etc/aliases /etc/aliases_org', warn=True)
  c.sudo('postalias /etc/aliases')

  # Edit config.
  c.sudo('cp -p /etc/postfix/main.cf /etc/postfix/main.cf_org')
  ## Disable IPv6 in postfix.
  c.sudo('sed -i "s/^inet_protocols = all$/inet_protocols = ipv4/" /etc/postfix/main.cf')
  ## Encrypt mail.
  c.sudo(f'sh -c "echo \'smtp_tls_security_level = may\' >> /etc/postfix/main.cf"')
  c.run('diff /etc/postfix/main.cf /etc/postfix/main.cf_org', warn=True)
  c.sudo('/etc/init.d/postfix restart')

@print_time
def setup_logwatch(c):
  # Install logwatch.
  c.sudo('apt -y install logwatch')

  # Edit config.
  c.sudo('cp -p /usr/share/logwatch/default.conf/logwatch.conf /etc/logwatch/conf/',)
  ## Output result in more detail.
  c.sudo(f'sed -i "s/^Detail = Low$/Detail = High/" /etc/logwatch/conf/logwatch.conf',)
  c.run('diff /usr/share/logwatch/default.conf/logwatch.conf /etc/logwatch/conf/', warn=True)
  # Execute logwatch.
  c.sudo('mkdir -p /var/cache/logwatch')
  c.sudo('logwatch --output stdout')

@print_time
def setup_docker(c):
  # Install docker.
  c.sudo(f'sh -c "curl https://get.docker.com | sh"')
  c.sudo(f'usermod -aG docker {c.user}')
  # Install docker-compose.
  docker_compose_version = c.run('curl https://api.github.com/repos/docker/compose/releases/latest | jq .name -r').stdout.strip()
  c.sudo(f'curl -L "https://github.com/docker/compose/releases/download/{docker_compose_version}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose')
  c.sudo('chmod +x /usr/local/bin/docker-compose')

@print_time
def reboot(c):
  # Reboot OS.
  c.sudo('reboot', warn=True)

def main():
  # Prepare setup.
  c, new_ssh_user_name, new_ssh_port, mail_address = prepare()
  # Start setup.
  setup(c, new_ssh_user_name, new_ssh_port, mail_address)

main()
