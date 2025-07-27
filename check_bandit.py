#!/usr/bin/env python3
import json

with open('bandit-final.json', 'r') as f:
    data = json.load(f)

print('Files scanned:')
for r in data['results'][:10]:
    print(f'  {r["filename"]}')

print(f'\nTotal results: {len(data["results"])}')

# Count by our project files vs others
project_files = [r for r in data['results'] if not r['filename'].startswith('.\\venv\\')]
other_files = [r for r in data['results'] if r['filename'].startswith('.\\venv\\')]

print(f'Project files: {len(project_files)}')
print(f'Virtual env files: {len(other_files)}')

if project_files:
    print('\nProject file issues:')
    for r in project_files[:5]:
        print(f'  {r["filename"]}: {r["test_name"]} - {r["issue_severity"]}')
else:
    print('\n✅ No security issues found in project files!')

# Summary
print(f'\nSkipped tests (nosec): {data["metrics"]["_totals"]["nosec"]}')
print(f'Total skipped tests: {data["metrics"]["_totals"]["skipped_tests"]}')
