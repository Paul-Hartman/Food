"""Fix all scale endpoints database calls."""

# Read file
with open('backend/app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Track if we're in a scale endpoint function
in_scale_func = False
func_has_db = False
output_lines = []
i = 0

while i < len(lines):
    line = lines[i]

    # Detect scale endpoint start
    if '@app.route("/api/scale/' in line or '@app.route("/api/pantry/inventory/<int:inventory_id>/weigh"' in line:
        in_scale_func = True
        func_has_db = False
        output_lines.append(line)
        i += 1
        continue

    # Check if function already has db = get_db()
    if in_scale_func and 'db = get_db()' in line:
        func_has_db = True

    # Add db = get_db() after docstring closes
    if in_scale_func and not func_has_db and '"""' in line and output_lines[-2].strip().startswith('"""'):
        output_lines.append(line)
        output_lines.append('    db = get_db()\n')
        func_has_db = True
        i += 1
        continue

    # Or after function def if no docstring
    if in_scale_func and not func_has_db and line.strip() and not line.strip().startswith('def ') and not line.strip().startswith('"""'):
        if len(output_lines) > 0 and 'def api_scale_' in output_lines[-1]:
            output_lines.append('    db = get_db()\n')
            func_has_db = True

    # Fix cursor.execute to db.execute
    if in_scale_func and 'cursor.execute(' in line and 'cursor = db.execute(' not in line:
        line = line.replace('cursor.execute(', 'cursor = db.execute(')

    # Fix conn.commit to db.commit
    if in_scale_func and 'conn.commit()' in line:
        line = line.replace('conn.commit()', 'db.commit()')

    # Detect end of function (next @app.route or class/def at column 0)
    if in_scale_func and (line.startswith('@app.route') or (line.startswith('def ') and i > 0)):
        in_scale_func = False

    output_lines.append(line)
    i += 1

# Write back
with open('backend/app.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("Fixed all scale endpoints!")
