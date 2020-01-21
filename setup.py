from setuptools import setup


setup(
    name='cldfbench_easterdaysyllablestructure',
    py_modules=['cldfbench_easterdaysyllablestructure'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'easterdaysyllablestructure=cldfbench_easterdaysyllablestructure:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
