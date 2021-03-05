## Issue Boards Maintainer

Maintain issue boards via GitLab webhook and cron job

Apply in 2 projects: project_a and project_b

### Requirements
- python3
- node
- [aws-cdk](https://github.com/aws/aws-cdk)

### GitLab Setup
- Create a [personal access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#creating-a-personal-access-token)
- Webhooks settings in both project_a and project_b
  - URL
  - Trigger
    - Push events
    - Merge request events
- Create Labels in project_a
  #### stage
  - Doing
  - MR Review
  - Dev
  - Staging
  - Production
  #### label
  - EPIC
  - feature
  - change
  - bugfix
  #### project
  - project_a
  - project_b
- Create a milestone when a new sprint start

### Environment Variable
- SECRET_TOKEN
- ACCESS_TOKEN
- AWS_REGION
- AWS_ACCOUNT
- PROJECT_A_PROJECT_ID
- PROJECT_B_PROJECT_ID

### Reference
- [GitLab Webhook](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html)
- [GitLab API](https://docs.gitlab.com/ee/api/api_resources.html)
- [Troubleshoot webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#troubleshoot-webhooks)
