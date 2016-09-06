from distutils.core import setup

setup(
    name='vk_community',
    version='1.0.0',
    packages=['tests', 'utils', 'services'],
    url='https://github.com/lycantropos/VKCommunity',
    license='GNU GPL',
    author='ace',
    author_email='azatibrakov@gmail.com',
    install_requires=[
        'requests',
        'mysqlclient',
        'numpy',
        'scikit-image',
        'Pillow'
    ],
    dependency_links=['https://github.com/lycantropos/VKApp.git#egg=vk_app'],
    description="Simple package for creating application"
                "which parses VK communities' data and posts objects in administrated communities(post bot)"
)
