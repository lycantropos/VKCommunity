## Installing the package on Ubuntu 14.04

### Installing required environment

Install relational database management system `MySQL`
and `libmysqlclient-dev` package for `mysql-config` command support
(`mysqlclient` package requirement)
```bash
sudo apt-get install -y mysql-server
sudo apt-get install -y libmysqlclient-dev
```

Add repository and install `Python 3.5` with `python3.5-dev` package
(`mysqlclient` and `numpy` packages' requirement):

```bash
sudo add-apt-repository ppa:fkrull/deadsnakes
sudo apt-get update
sudo apt-get install -y python3.5 python3.5-dev
```

Install `Python 3.5` package manager - `pip` and upgrade it

```bash
sudo apt-get install -y python3-pip
sudo python3.5 -m pip install --upgrade pip
```

Install version control system - `git`:

```bash
sudo apt-get install -y git
```

### Installing the package
Install manually using `pip` and `git`

```bash
sudo python3.5 -m pip install git+https://github.com/lycantropos/VKCommunity.git#egg=vk_community
```
or add next line to `requirements.txt`
```bash
git+https://github.com/lycantropos/VKCommunity.git#egg=vk_community
```
