# setup-remote-os

Fabric code to setup OS installed in remote machine.

The overview of setup is as follows.

- Create ssh key
- Setup timezone
- Setup apt
- Setup sshd
- Setup iptables
- Setup logwatch
- Setup docker
- Disable ipv6
- Reboot

## Execution environment

- Mac OS

### Required package

- [python (2.7 or 3.4+)](https://docs.python-guide.org/starting/install3/osx/)
- [fabric 2](http://www.fabfile.org/installing.html)

```
$ pip install fabric
$ pip list | grep fabric
fabric (2.4.0)
$
```

### Recommended package to test (not required)

- [vagrant](https://www.vagrantup.com/intro/getting-started/index.html)
- [vagrant-hostsupdater](https://github.com/cogitatio/vagrant-hostsupdater)

```
$ vagrant plugin install vagrant-hostsupdater
$ vagrant plugin list | grep vagrant-hostsupdater
vagrant-hostsupdater (1.1.1.160, global)
$
```

## Basic usage

Run setup.py to the OS immediately after installation.

### Ubuntu 18.04

```
$ cd ./ubuntu/1804
$ python setup.py user_name@host_name:ssh_port new_ssh_port mail_address 2>&1 | tee user_name_$(date +'%Y%m%d_%H%M%S').log
```

#### Example using local test server on vagrant

```
$ cd ./ubuntu/1804
$ vagrant up
$ python setup.py vagrant@ubuntu-1804.local:22 54321 example@gmail.com 2>&1 | tee vagrant_$(date +'%Y%m%d_%H%M%S').log
vagrant@ubuntu-1804.local's password? vagrant
...
Enter passphrase (empty for no passphrase): any_string_passphrase
Enter same passphrase again: any_string_passphrase
...
$
```

##### How to SSH login with new_ssh_port after setup

```
$ ssh -p 54321 -i ~/.ssh/vagrant_ecdsa vagrant@ubuntu-1804.local
Enter passphrase for key '~/.ssh/vagrant_ecdsa': any_string_passphrase
Welcome to Ubuntu 18.04.1 LTS (GNU/Linux 4.15.0-34-generic x86_64)
...
vagrant@ubuntu-1804:~$
```
