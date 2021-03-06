# setup-remote-os

Fabric code to setup OS installed in remote machine.

The overview of setup is as follows.

- Add user to connect by ssh
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
$ python setup.py ssh_user_name@host_fqdn:ssh_port new_ssh_user_name new_ssh_port mail_address 2>&1 | tee new_ssh_user_name_$(date +'%Y%m%d_%H%M%S').log
```

#### Example using local test server on vagrant

##### How to setup

###### Start vagrant environment

```
$ cd ./ubuntu/1804
$ vagrant up
```

###### Case: add ssh user

Set arguments as `ssh_user_name != new_ssh_user_name`

```
$ python setup.py vagrant@ubuntu-1804.local:22 testuser 54321 example@gmail.com 2>&1 | tee testuser_$(date +'%Y%m%d_%H%M%S').log
vagrant@ubuntu-1804.local's password? vagrant
...
testuser@ubuntu-1804.local's password?: any_string_password
Enter same password again: any_string_password
...
Enter passphrase (empty for no passphrase): any_string_passphrase
Enter same passphrase again: any_string_passphrase
...
$
```

###### Case: not add ssh user

Set arguments as `ssh_user_name == new_ssh_user_name`

```
$ python setup.py vagrant@ubuntu-1804.local:22 vagrant 54321 example@gmail.com 2>&1 | tee vagrant_$(date +'%Y%m%d_%H%M%S').log
vagrant@ubuntu-1804.local's password? vagrant
...
Not add user.
...
Enter passphrase (empty for no passphrase): any_string_passphrase
Enter same passphrase again: any_string_passphrase
...
$
```

##### How to SSH login with new_ssh_user_name & new_ssh_port after setup

```
$ ssh -p 54321 -i ~/.ssh/testuser_ecdsa testuser@ubuntu-1804.local
Enter passphrase for key '~/.ssh/testuser_ecdsa': any_string_passphrase
Welcome to Ubuntu 18.04.1 LTS (GNU/Linux 4.15.0-34-generic x86_64)
...
testuser@ubuntu-1804:~$
```
