# Test Sample


## Request first project

```md
source .venv/bin/activate && python3 scripts/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request "Add product management with CRUD endpoints"
```

## Request add new feature -  user authentication

```md
python3 scripts/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request "Add user authentication with password and email validation"
```

## Request add new feature - shipping

```md
source .venv/bin/activate && python3 scripts/feature_by_request_agent_v3.py --codebase-path dataset/codes/springboot-demo --feature-request "Add shipping feature with order tracking and delivery status updates"
```