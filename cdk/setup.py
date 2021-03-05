import setuptools


with open("README.md") as fp:
    long_description = fp.read()


setuptools.setup(
    name="issue-boards-maintainer-cdk",
    version="0.0.1",

    description="GitLab Issue Boards maintainer CDK",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="kitty lin",

    package_dir={"": "issue_boards_maintainer"},
    packages=setuptools.find_packages(where="issue_boards_maintainer"),

    install_requires=[
        "aws-cdk.core",
        "aws-cdk.aws-lambda",
        "aws-cdk.aws-apigateway"
    ],

    python_requires=">=3.6",

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",

        "License :: OSI Approved :: Apache Software License",

        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",

        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",

        "Typing :: Typed",
    ],
)
