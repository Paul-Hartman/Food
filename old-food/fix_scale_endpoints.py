"""Fix scale endpoints to use get_db() pattern."""

import re

# Read the app.py file
with open('backend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all scale endpoint functions (from @app.route to next @app.route or end)
scale_routes = [
    '/api/scale/measure',
    '/api/scale/measurements',
    '/api/scale/infusions',
    '/api/scale/brew-logs',
    '/api/pantry/inventory',  # The weigh endpoint
]

# Function to fix a scale endpoint
def fix_endpoint(match):
    func_text = match.group(0)

    # Skip if already has db = get_db()
    if 'db = get_db()' in func_text:
        return func_text

    # Add db = get_db() after the docstring or function def
    if '"""' in func_text:
        # After docstring
        func_text = func_text.replace('"""', '"""\n    db = get_db()', 1)
        # Find second occurrence
        second_quote_idx = func_text.find('"""', func_text.find('db = get_db()'))
        if second_quote_idx != -1:
            func_text = func_text[:second_quote_idx+3] + '\n    db = get_db()' + func_text[second_quote_idx+3:]
    else:
        # After function def
        lines = func_text.split('\n')
        for i, line in enumerate(lines):
            if 'def api_' in line and lines[i+1].strip():
                lines.insert(i+1, '    db = get_db()')
                break
        func_text = '\n'.join(lines)

    # Replace cursor.execute with db.execute
    func_text = re.sub(r'\bcursor\.execute\(', 'cursor = db.execute(', func_text)

    # Replace conn.commit with db.commit
    func_text = re.sub(r'\bconn\.commit\(\)', 'db.commit()', func_text)

    return func_text

# Fix each scale endpoint function by finding them with regex
# Match from @app.route to next @app.route or end of file
pattern = r'(@app\.route\("/api/scale/[^"]+.*?\n(?:.*?\n)*?(?=@app\.route|$))'

content = re.sub(pattern, fix_endpoint, content, flags=re.MULTILINE)

# Also fix the pantry weigh endpoint
pattern2 = r'(@app\.route\("/api/pantry/inventory/<int:inventory_id>/weigh".*?\n(?:.*?\n)*?(?=@app\.route|$))'
content = re.sub(pattern2, fix_endpoint, content, flags=re.MULTILINE)

# Write back
with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed all scale endpoints to use db = get_db() pattern!")
