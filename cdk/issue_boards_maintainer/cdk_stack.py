import os
from aws_cdk import (
    core,
    aws_lambda,
    aws_apigateway
)


class CDKStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # lambda function
        issue_boards_maintainer = aws_lambda.Function(
            self, "issue_boards_maintainer",
            function_name="issue_boards_maintainer",
            code=aws_lambda.Code.asset("../functions/issue_boards_maintainer"),
            handler="lambda_function.issue_boards_maintainer",
            timeout=core.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_7,
            memory_size=1024,
            environment={
                "SECRET_TOKEN": os.environ.get("SECRET_TOKEN"),
                "ACCESS_TOKEN": os.environ.get("ACCESS_TOKEN"),
                "PROJECT_A_PROJECT_ID": os.environ.get("PROJECT_A_PROJECT_ID"),
                "PROJECT_B_PROJECT_ID": os.environ.get("PROJECT_B_PROJECT_ID")
            }
        )

        # api gateway
        rest_api = aws_apigateway.RestApi(self,
                                          'issue_boards_webhook',
                                          rest_api_name='issue_boards_webhook')

        resource_entity = rest_api.root.add_resource('webhook')
        lambda_integration_entity = aws_apigateway.LambdaIntegration(issue_boards_maintainer, proxy=True)
        resource_entity.add_method('POST', lambda_integration_entity)
