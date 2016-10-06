from setuptools import setup, find_packages

setup(
    name='VKCommunity',
    version='0.0.1',
    packages=find_packages(exclude=["tests"]),
    url='https://github.com/lycantropos/VKCommunity',
    license='GNU GPL',
    author='lycantropos',
    author_email='azatibrakov@gmail.com',
    description='Simple application for VK community content administrating by using `vk_app` module',
    install_requires=[
        'click==6.6',
        'SQLAlchemy==1.1.0',
        'requests==2.11.1',
        'numpy==1.11.1',
        'scikit-image==0.12.3',
        'Pillow==3.4.0',
    ],
    dependency_links=[
        'git+https://github.com/lycantropos/VKApp.git#egg=vk_app'
    ]
)
