import re
import json
from typing import (
    Dict,
    List,
    Optional
)


def response_message_body(
    status_code: int,
    body: Optional[Dict[str, str]]
) -> Dict[str, str]:
    """Construct a HTTP response object for lambda function.

    Args:
        status_code (int): The status code of the response.
        body (Dict[str, str], optional): The body of the response.

    Returns:
        Dict[str, str]

    """
    response = {
        "statusCode": status_code
    }
    if body is not None:
        response["body"] = json.dumps(body)
    return response


def get_id_from_text_description(description: str) -> Optional[int]:
    """Parse id from text in the description.

    Args:
        description (str): The description of the merge request.
                           eg. xxx\n\nSee merge request xxx/xxx/xxx!30\n\n(cherry picked from commit 79b5be87)\n\nxxx

    Returns:
        int

    """
    description_regex = re.compile("^(.|\n)*!([0-9]*)(.|\n)*$")
    try:
        (_, mr_id, _) = description_regex.match(description).groups()
        return int(mr_id)
    except Exception:
        return None


def get_ids_from_url_description(description: str) -> List[int]:
    """Parse all ids from url in the description.

    Args:
        description (str): The description of the issue.
                           eg. Related Issue URL: https://gitlab.com/engenius_cloud/project_a/issue_boards_test/-/issues/20\n\nRelated Issue URL: https://gitlab.com/engenius_cloud/project_a/issue_boards_test/-/issues/21

    Returns:
        List[int]

    """
    description_regex = re.compile("^.*/([0-9]*)$")
    description_lines = description.split("\n\n")
    issue_iids = []
    for line in description_lines:
        try:
            issue_iid = description_regex.match(line).groups()[0]
            issue_iids.append(int(issue_iid))
        except Exception:
            pass
    return issue_iids


def is_cherry_pick_branch(branch_name: str) -> bool:
    """Return True if the branch is created by cherry-pick

    Args:
        branch_name (str): The name of the branch.

    Returns:
        bool

    """
    branch_regex = re.compile("^(cherry-pick).*$")
    regex_result = branch_regex.match(branch_name)
    if regex_result is None:
        return False
    return True


def is_dev_branch(branch_name: str) -> bool:
    """Return True if branch name is "dev"

    Args:
        branch_name (str): The name of the branch.

    Returns:
        bool

    """
    branch_regex = re.compile("^(.+/)*(dev)$")
    regex_result = branch_regex.match(branch_name)
    if regex_result is None:
        return False
    return True


def is_staging_branch(branch_name: str) -> bool:
    """Return True if branch name is "staging"

    Args:
        branch_name (str): The name of the branch.

    Returns:
        bool

    """
    branch_regex = re.compile("^(.+/)*(staging)$")
    regex_result = branch_regex.match(branch_name)
    if regex_result is None:
        return False
    return True


def is_master_branch(branch_name: str) -> bool:
    """Return True if branch name is "master"

    Args:
        branch_name (str): The name of the branch.

    Returns:
        bool

    """
    branch_regex = re.compile("^(.+/)*(master)$")
    regex_result = branch_regex.match(branch_name)
    if regex_result is None:
        return False
    return True
