import os
from enum import Enum


class ExtendedEnum(Enum):
    @classmethod
    def value_list(cls):
        # List[str]: Convert Enum values to a list
        values = []
        for item in cls:
            values.append(item.value)
        return values


class GitlabEvent(ExtendedEnum):
    PUSH_HOOK = "Push Hook"
    MERGE_REQUEST_HOOK = "Merge Request Hook"


class MRAction(ExtendedEnum):
    OPEN = "open"
    MERGE = "merge"
    CLOSE = "close"


class IssueLabel(Enum):
    # board list
    DOING = "Doing"
    MR_REVIEW = "MR Review"
    DEV = "Dev"
    STAGING = "Staging"
    PRODUCTION = "Production"

    # issue label
    EPIC = "EPIC"
    FEATURE = "feature"
    CHANGE = "change"
    BUG_FIX = "bugfix"

    # project label
    PROJECT_A = "project A"
    PROJECT_B = "project B"


class IssueState(Enum):
    OPENED = "opened"
    CLOSE = "close"
    REOPEN = "reopen"


class Project(ExtendedEnum):
    PROJECT_A = int(os.environ.get("PROJECT_A_PROJECT_ID"))
    PROJECT_B = int(os.environ.get("PROJECT_B_PROJECT_ID"))
