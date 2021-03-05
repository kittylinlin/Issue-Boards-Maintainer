#!/usr/bin/env python3

import os
from aws_cdk import core
from issue_boards_maintainer.cdk_stack import CDKStack


region = os.environ.get("AWS_REGION")
account = os.environ.get("AWS_ACCOUNT")

app = core.App()
CDKStack(app, "issue-boards-maintainer-cdk", env={'region': region, 'account': account})

app.synth()
