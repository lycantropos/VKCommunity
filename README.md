[![Build Status](https://travis-ci.org/lycantropos/VKCommunity.svg?branch=master)](https://travis-ci.org/lycantropos/VKCommunity)
# VKCommunity
Simple application for VK community content administrating by using [vk_app](https://github.com/lycantropos/VKApp "Simple application for working with `VK API`") module

# Setting up environment
Install `Python 3.5` and `python3-dev`:
```bash
add-apt-repository ppa:fkrull/deadsnakes
apt-get update
apt-get install -y python3.5 python3-dev
```

Install `matplotlib` requirements:
```bash
apt-get install -y libpng-dev libfreetype6-dev
```

Install `SciPy` requirements:
```bash
apt-get install -y libopenblas-dev gfortran
```

Install `Pillow` requirements:
```bash
apt-get install -y libjpeg8-dev
```

Sometimes `scikit-image` package installs before `numpy`, so install `numpy` first:
```bash
python3.5 -m pip install numpy==1.11.1
```

