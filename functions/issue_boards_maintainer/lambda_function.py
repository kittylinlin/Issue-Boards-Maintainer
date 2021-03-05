import os
import re
import json

from gitlab_apis import (
    create_project_issue,
    update_project_issue,
    search_project_issues,
    search_project_milestones,
    search_project_merge_requests
)
from gitlab_enum import (
    MRAction,
    Project,
    IssueLabel,
    IssueState,
    GitlabEvent
)
from gitlab_lib import (
    is_dev_branch,
    is_master_branch,
    is_staging_branch,
    is_cherry_pick_branch,
    response_message_body,
    get_id_from_text_description,
    get_ids_from_url_description
)


def issue_boards_maintainer(event, context):
    headers = event.get("headers", {})

    # check secret_token in headers
    secret_token = headers.get("X-Gitlab-Token")
    if secret_token != os.environ.get("SECRET_TOKEN"):
        return response_message_body(403, {
            "detailed message": "Invalid Secret Token"
        })

    # check gitlab event in headers, and check request body
    gitlab_event = headers.get("X-Gitlab-Event")
    body = event.get("body")
    if body is None or gitlab_event is None:
        return response_message_body(400, {
            "message": "Invalid Request Body or Header"
        })

    if gitlab_event not in GitlabEvent.value_list():
        return response_message_body(406, {
            "message": "Unsupported GitLab Event"
        })

    # check project_id in body
    body_json = json.loads(body)
    project_id = body_json.get("project", {}).get("id")
    if project_id not in Project.value_list():
        return response_message_body(406, {
            "message": "Unsupported Project"
        })

    # parse project_id to labels
    project_label = IssueLabel[Project(project_id).name].value
    branch_regex = re.compile("^(.+/)*(kitty)/(feature|bugfix|change)/(.+)$")

    # triggered when someone push to the repository
    if gitlab_event == GitlabEvent.PUSH_HOOK.value:
        # push without commit
        if body_json.get("total_commits_count") == 0:
            return response_message_body(200, {
                "message": "Push to a Branch with no Commit"
            })

        branch_name = body_json.get("ref")

        # only create issues for feature branch
        try:
            (_, _, category, title) = branch_regex.match(branch_name).groups()
        except Exception:
            return response_message_body(200, {
                "message": "No Need to Create an Issue"
            })

        issues, error = search_project_issues(Project.PROJECT_A.value,
                                              [project_label, category],
                                              title)
        if error is not None:
            return response_message_body(500, {
                "message": "Search Issue Error",
                "error": str(error)
            })

        # branch with more than 1 issue
        if len(issues) > 1:
            return response_message_body(500, {
                "message": "Multiple Issues"
            })

        # already created an issue, update label and state
        if len(issues) == 1:
            return response_message_body(200, {
                "message": "Issue Has Been Created"
            })

        # has not created any issue
        # assignee_id = body_json.get("user_id")
        _, error = create_project_issue(Project.PROJECT_A.value,
                                        None,
                                        [project_label, category, IssueLabel.DOING.value],
                                        title)
        if error is not None:
            return response_message_body(500, {
                "message": "Create Issue Error",
                "error": str(error)
            })

        return response_message_body(200, {
            "message": "Create Issue Successfully"
        })

    # triggered when a new merge request is created/updated/merged/closed
    mr_attribute = body_json.get("object_attributes", {})
    mr_action = mr_attribute.get("action")
    # assignee_id = mr_attribute.get("author_id")

    # check MR state
    if mr_action not in MRAction.value_list():
        return response_message_body(200, {
            "message": "Unsupported MR Action"
        })

    source_branch = mr_attribute.get("source_branch")
    target_branch = mr_attribute.get("target_branch")
    mr_url = mr_attribute.get("url")

    milestone_id = None
    if is_master_branch(target_branch) or mr_action == MRAction.CLOSE.value:
        milestones, error = search_project_milestones(Project.PROJECT_A.value)
        if error is not None:
            pass
        elif len(milestones) != 0:
            milestone_id = milestones[0].get("id")

    # open a MR
    if mr_action == MRAction.OPEN.value:
        """
        source branch: feature branch
        target branch: dev, topic branch
        => add MR label to the issue
        """
        source_branch_match = branch_regex.match(source_branch)
        if source_branch_match is None or is_staging_branch(target_branch) or is_master_branch(target_branch):
            return response_message_body(200, {
                "message": "No Need to Update the Issue"
            })

        (_, _, category, title) = source_branch_match.groups()
        issues, error = search_project_issues(Project.PROJECT_A.value,
                                              [project_label, category],
                                              title)
        if error is not None:
            return response_message_body(500, {
                "message": "Search Issue Error",
                "error": str(error)
            })

        description = "Related MR URL: {}".format(mr_url)
        if len(issues) == 0:
            _, error = create_project_issue(Project.PROJECT_A.value,
                                            None,
                                            [project_label, category, IssueLabel.MR_REVIEW.value],
                                            title,
                                            description)
            if error is not None:
                return response_message_body(500, {
                    "message": "Create Issue Error",
                    "error": str(error)
                })

            return response_message_body(200, {
                "message": "Create Issue Successfully"
            })

        error = update_project_issue(Project.PROJECT_A.value,
                                     issues[0].get("iid"),
                                     [project_label, category, IssueLabel.MR_REVIEW.value],
                                     description)
        if error is not None:
            return response_message_body(500, {
                "message": "Update Issue Error",
                "error": str(error)
            })
        return response_message_body(200, {
            "message": "Update Issue Successfully"
        })

    # merge a MR
    elif mr_action == MRAction.MERGE.value:
        """
        source branch: feature branch
        target branch: topic branch
        => create a topic issue and close the feature issue
        """
        if not is_dev_branch(target_branch) and not is_staging_branch(target_branch) and not is_master_branch(target_branch):
            try:
                (_, _, category, title) = branch_regex.match(source_branch).groups()
            except Exception:
                return response_message_body(200, {
                    "message": "No Need to Create an Issue"
                })

            issues, error = search_project_issues(Project.PROJECT_A.value,
                                                  [project_label, category],
                                                  title)
            if error is not None:
                return response_message_body(500, {
                    "message": "Search Issue Error",
                    "error": str(error)
                })

            topic_issues, error = search_project_issues(Project.PROJECT_A.value,
                                                        [project_label, IssueLabel.EPIC.value],
                                                        target_branch)
            if error is not None:
                return response_message_body(500, {
                    "message": "Search Topic Issue Error",
                    "error": str(error)
                })

            try:
                new_topic_description = "Related Issue URL: {}".format(issues[0].get("web_url"))
            except Exception:
                new_topic_description = ""

            if len(topic_issues) == 0:
                topic_issue, error = create_project_issue(Project.PROJECT_A.value,
                                                          None,
                                                          [project_label, IssueLabel.EPIC.value, IssueLabel.MR_REVIEW.value],
                                                          target_branch,
                                                          new_topic_description)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Create Topic Issue Error",
                        "error": str(error)
                    })
                topic_issues.append(topic_issue)
            else:
                topic_description = topic_issues[0].get("description") + "\n\n" + new_topic_description
                error = update_project_issue(Project.PROJECT_A.value,
                                             topic_issues[0].get("iid"),
                                             None,
                                             topic_description)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Update Topic Issue Error",
                        "error": str(error)
                    })

            if len(issues) != 0:
                issue_description = issues[0].get("description") + "\n\nRelated Issue URL: {}".format(topic_issues[0].get("web_url"))
                error = update_project_issue(Project.PROJECT_A.value,
                                             issues[0].get("iid"),
                                             [project_label, category],
                                             issue_description,
                                             IssueState.CLOSE.value)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Close Issue Error",
                        "error": str(error)
                    })
            return response_message_body(200, {
                "message": "Create/Update/Close Issue Successfully"
            })

        # ready for merging to dev/staging/master
        target_branch_label = None
        if is_dev_branch(target_branch):
            target_branch_label = IssueLabel.DEV.value
        elif is_staging_branch(target_branch):
            target_branch_label = IssueLabel.STAGING.value
        elif is_master_branch(target_branch):
            target_branch_label = IssueLabel.PRODUCTION.value

        """
        source branch: cherry-pick-xxxxxxxx
        target branch: dev/staging/master
        description: xxx\n\nSee merge request xxx/xxx/xxx!30\n\n(cherry picked from commit 79b5be87)\n\nxxx
        => get mr_id from mr description
        => get original source branch by mr_id
        => add target_branch_label and milestone to the issue
        """
        if is_cherry_pick_branch(source_branch) and target_branch_label is not None:
            mr_id = get_id_from_text_description(mr_attribute.get("description"))
            if mr_id is None:
                return response_message_body(400, {
                    "message": "Cannot Find Original MR Id From MR Description"
                })
            mrs, error = search_project_merge_requests(project_id, mr_id)
            if error is not None:
                return response_message_body(500, {
                    "message": "Search MR Error",
                    "error": str(error)
                })
            if len(mrs) == 0:
                return response_message_body(400, {
                    "message": "Cannot Find Related MR"
                })

            original_source_branch = mrs[0].get("source_branch")
            try:
                (_, _, category, title) = branch_regex.match(original_source_branch).groups()
                issues, error = search_project_issues(Project.PROJECT_A.value,
                                                      [project_label, category],
                                                      title)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Search Issue Error",
                        "error": str(error)
                    })
                if len(issues) == 0:
                    _, error = create_project_issue(Project.PROJECT_A.value,
                                                    None,
                                                    [project_label, category, target_branch_label],
                                                    title,
                                                    None,
                                                    milestone_id)
                    if error is not None:
                        return response_message_body(500, {
                            "message": "Create Issue Error",
                            "error": str(error)
                        })
                    return response_message_body(200, {
                        "message": "Create Issue Successfully"
                    })
                error = update_project_issue(Project.PROJECT_A.value,
                                             issues[0].get("iid"),
                                             [project_label, category, target_branch_label],
                                             None,
                                             None,
                                             milestone_id)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Update Issue Error",
                        "error": str(error)
                    })
                return response_message_body(200, {
                    "message": "Update Issue Successfully"
                })
            except Exception:
                topic_issues, error = search_project_issues(Project.PROJECT_A.value,
                                                            [project_label, IssueLabel.EPIC.value],
                                                            original_source_branch)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Search Topic Issue Error",
                        "error": str(error)
                    })
                if len(topic_issues) == 0:
                    return response_message_body(200, {
                        "message": "No Need to Create a Topic Issue"
                    })
                error = update_project_issue(Project.PROJECT_A.value,
                                             topic_issues[0].get("iid"),
                                             [project_label, IssueLabel.EPIC.value, target_branch_label],
                                             None,
                                             None,
                                             milestone_id)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Update Topic Issue Error",
                        "error": str(error)
                    })
                return response_message_body(200, {
                    "message": "Update Topic Issue Successfully"
                })

        """
        source branch: feature branch/ topic branch
        target branch: dev/staging/master
        => add target_branch_label and milestone to the issue
        """
        if not is_dev_branch(source_branch) and not is_staging_branch(source_branch) and not is_master_branch(source_branch) and target_branch_label is not None:
            try:
                (_, _, category, title) = branch_regex.match(source_branch).groups()
                issues, error = search_project_issues(Project.PROJECT_A.value,
                                                      [project_label, category],
                                                      title)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Search Issue Error",
                        "error": str(error)
                    })
                if len(issues) == 0:
                    _, error = create_project_issue(Project.PROJECT_A.value,
                                                    None,
                                                    [project_label, category, target_branch_label],
                                                    title,
                                                    None,
                                                    milestone_id)
                    if error is not None:
                        return response_message_body(500, {
                            "message": "Create Issue Error",
                            "error": str(error)
                        })
                    return response_message_body(200, {
                        "message": "Create Issue Successfully"
                    })
                error = update_project_issue(Project.PROJECT_A.value,
                                             issues[0].get("iid"),
                                             [project_label, category, target_branch_label],
                                             None,
                                             None,
                                             milestone_id)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Update Issue Error",
                        "error": str(error)
                    })
                return response_message_body(200, {
                    "message": "Update Issue Successfully"
                })
            except Exception:
                topic_issues, error = search_project_issues(Project.PROJECT_A.value,
                                                            [project_label, IssueLabel.EPIC.value],
                                                            source_branch)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Search Topic Issue Error",
                        "error": str(error)
                    })
                if len(topic_issues) == 0:
                    return response_message_body(200, {
                        "message": "No Need to Create a Topic Issue"
                    })

                if milestone_id is not None:
                    related_issue_iids = get_ids_from_url_description(topic_issues[0].get("description", ""))
                    for related_issue_iid in related_issue_iids:
                        error = update_project_issue(Project.PROJECT_A.value,
                                                     related_issue_iid,
                                                     None,
                                                     None,
                                                     IssueState.CLOSE.value,
                                                     milestone_id)
                        if error is not None:
                            print(error)

                error = update_project_issue(Project.PROJECT_A.value,
                                             topic_issues[0].get("iid"),
                                             [project_label, IssueLabel.EPIC.value, target_branch_label],
                                             None,
                                             None,
                                             milestone_id)
                if error is not None:
                    return response_message_body(500, {
                        "message": "Update Topic Issue Error",
                        "error": str(error)
                    })
                return response_message_body(200, {
                    "message": "Update Topic Issue Successfully"
                })

        """
        source branch: staging
        target branch: master
        => add label(Production) and milestone to all issues in staging
        """
        if is_staging_branch(source_branch) and is_master_branch(target_branch):
            issues, error = search_project_issues(Project.PROJECT_A.value,
                                                  [project_label, IssueLabel.STAGING.value])
            if error is not None:
                return response_message_body(500, {
                    "message": "Search Issue Error",
                    "error": str(error)
                })

            if len(issues) == 0:
                return response_message_body(200, {
                    "message": "No Need to Move Issues from Staging to Production"
                })

            error_list = []
            for issue in issues:
                issue_labels = issue.get("labels", [])
                try:
                    issue_labels.remove(IssueLabel.STAGING.value)
                except Exception:
                    pass
                issue_labels.append(target_branch_label)
                error = update_project_issue(Project.PROJECT_A.value,
                                             issue.get("iid"),
                                             issue_labels,
                                             None,
                                             None,
                                             milestone_id)
                if error is not None:
                    error_list.append(str(error))

                # topic issue:
                if IssueLabel.EPIC.value in issue_labels:
                    related_issue_iids = get_ids_from_url_description(issue.get("description", ""))
                    for related_issue_iid in related_issue_iids:
                        error = update_project_issue(Project.PROJECT_A.value,
                                                     related_issue_iid,
                                                     None,
                                                     None,
                                                     None,
                                                     milestone_id)
                        if error is not None:
                            error_list.append(str(error))

            if len(error_list) > 0:
                return response_message_body(500, {
                    "message": "Update Staging Issues Error",
                    "error": str(error_list)
                })
            return response_message_body(200, {
                "message": "Move Issues from Staging to Production Successfully"
            })

        return response_message_body(406, {
            "message": "Unsupported MR"
        })

    # close a MR => close the issue
    issues, error = search_project_issues(Project.PROJECT_A.value,
                                          None,
                                          mr_url)
    if error is not None:
        return response_message_body(500, {
            "message": "Search Issue Error",
            "error": str(error)
        })

    if len(issues) == 0:
        return response_message_body(200, {
            "message": "No Need to Close a Issue"
        })

    error = update_project_issue(Project.PROJECT_A.value,
                                 issues[0].get("iid"),
                                 None,
                                 None,
                                 IssueState.CLOSE.value,
                                 milestone_id)
    if error is not None:
        return response_message_body(500, {
            "message": "Close Issue Error",
            "error": str(error)
        })
    return response_message_body(200, {
        "message": "Close Issue Successfully"
    })
