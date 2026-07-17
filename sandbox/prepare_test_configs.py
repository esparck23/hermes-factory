import yaml
import os

projects_path = r'C:\Users\Agent\dev\hermes-factory\projects.yaml'
active_path = r'C:\Users\Agent\dev\hermes-factory\active.yaml'

# Fix projects.yaml
with open(projects_path, 'r') as f:
    projects_data = yaml.safe_load(f)

for project in projects_data['projects']:
    if project['name'] == 'test-project':
        project['root'] = r'C:\Users\Agent\dev\hermes-factory\sandbox\test-project'

with open(projects_path, 'w') as f:
    yaml.dump(projects_data, f)

# Fix active.yaml
active_data = {
    'active_projects': ['test-project']
}

with open(active_path, 'w') as f:
    yaml.dump(active_data, f)

print("Configs prepared for test-project.")
