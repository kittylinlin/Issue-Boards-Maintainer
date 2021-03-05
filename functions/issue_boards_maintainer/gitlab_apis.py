import os
import requests
from typing import (
    List,
    Tuple,
    Optional
)

from gitlab_enum import IssueState

gitlab_api_base_url = "https://gitlab.com/api/v4"


def search_project_issues(
    project_id: int,
    labels: Optional[List[str]] = None,
    search: Optional[str] = None
) -> Tuple[List, Exception]:
    """Get a list of a project’s issues.

    Args:
        project_id (int): The ID of the project.
        labels (List[str], optional): Label names of an issue.
        search (str, optional): Search against title and description.

    Returns:
        Tuple[List, Exception]: (list of issues, Exception)

    """
    search_issue_url = gitlab_api_base_url + "/projects/{}/issues".format(project_id)
    headers = {
        "Private-Token": os.environ.get("ACCESS_TOKEN")
    }
    # params = {
    #     "state": IssueState.OPENED.value
    # }
    params = {}
    if labels is not None:
        params["labels"] = ",".join(labels)
    if search is not None:
        params["search"] = search

    try:
        response = requests.get(search_issue_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, e


def create_project_issue(
    project_id: int,
    assignee_id: Optional[int] = None,
    labels: Optional[List[str]] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    milestone_id: Optional[int] = None
) -> Optional[Exception]:
    """Create a new project issue.

    Args:
        project_id (int): The ID of the project.
        assignee_id (int, optional): The ID of a user to assign issue.
        labels (List[str], optional): Label names for an issue.
        title (str, optional): The title of an issue.
        description (str, optional): The description of an issue.
        milestone_id (int, optional): The ID of a milestone to assign issue.

    Returns:
        Exception: None if no error exists.

    """
    create_issue_url = gitlab_api_base_url + "/projects/{}/issues".format(project_id)
    headers = {
        "Private-Token": os.environ.get("ACCESS_TOKEN")
    }
    params = {}
    if assignee_id is not None:
        params["assignee_ids"] = [assignee_id]
    if labels is not None:
        params["labels"] = ",".join(labels)
    if title is not None:
        params["title"] = title
    if description is not None:
        params["description"] = description
    if milestone_id is not None:
        params["milestone_id"] = milestone_id

    try:
        response = requests.post(create_issue_url, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()
        return response_json, None
    except Exception as e:
        return None, e


def update_project_issue(
    project_id: int,
    issue_iid: int,
    labels: Optional[List[str]] = None,
    description: Optional[str] = None,
    state_event: Optional[str] = None,
    milestone_id: Optional[int] = None
) -> Optional[Exception]:
    """Update an existing project issue. This call is also used to mark an issue as closed.

    Args:
        project_id (int): The ID of the project.
        issue_iid (int, optional): The internal ID of a project’s issue.
        labels (List[str], optional): Label names for an issue. Set to an empty string to unassign all labels.
        description (str, optional): The description of an issue.
        state_event (str, optional): The state event of an issue. Set close to "close" the issue and "reopen" to reopen it.
        milestone_id (int, optional): The ID of a milestone to assign the issue to. Set to 0 or provide an empty value to unassign a milestone.

    Returns:
        Exception: None if no error exists.

    """
    update_issue_url = gitlab_api_base_url + "/projects/{}/issues/{}".format(project_id, issue_iid)
    headers = {
        "Private-Token": os.environ.get("ACCESS_TOKEN")
    }
    params = {}
    if labels is not None:
        params["labels"] = ",".join(labels)
    if description is not None:
        params["description"] = description
    if state_event is not None:
        params["state_event"] = state_event
    if milestone_id is not None:
        params["milestone_id"] = milestone_id

    try:
        response = requests.put(update_issue_url, headers=headers, params=params)
        response.raise_for_status()
        return None
    except Exception as e:
        return e


def search_project_milestones(
    project_id: int,
    state: str = "active"
) -> Tuple[List, Exception]:
    """Return a list of project milestones.

    Args:
        project_id (int): The ID of the project.
        state (str, optional): Return only "active" or "closed" milestones.

    Returns:
        Tuple[List, Exception]: (list of milestones, Exception)

    """
    search_milestone_url = gitlab_api_base_url + "/projects/{}/milestones".format(project_id)
    headers = {
        "Private-Token": os.environ.get("ACCESS_TOKEN")
    }
    params = {}
    if state is not None:
        params["state"] = state

    try:
        response = requests.get(search_milestone_url, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()
        return response_json, None
    except Exception as e:
        return None, e


def search_project_merge_requests(
    project_id: int,
    mr_iid: Optional[int] = None
) -> Tuple[List, Exception]:
    """Get all merge requests for this project.

    Args:
        project_id (int): The ID of the project.
        mr_iid (str, optional): Return the request having the given mr_iid.

    Returns:
        Tuple[List, Exception]: (list of merge requests, Exception)

    """
    search_merge_request_url = gitlab_api_base_url + "/projects/{}/merge_requests".format(project_id)
    headers = {
        "Private-Token": os.environ.get("ACCESS_TOKEN")
    }
    params = {}
    if mr_iid is not None:
        params["iids[]"] = mr_iid

    try:
        response = requests.get(search_merge_request_url, headers=headers, params=params)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, e
