import uuid
from pathlib import Path

content = Path('tests/unit/test_repositories.py').read_text(encoding='utf-8')

content = content.replace('"comp-1"', '"11111111-1111-1111-1111-111111111111"')
content = content.replace('"comp-2"', '"22222222-2222-2222-2222-222222222222"')
content = content.replace('"issue-1"', '"33333333-3333-3333-3333-333333333333"')
content = content.replace('"issue-2"', '"44444444-4444-4444-4444-444444444444"')
content = content.replace('"issue-3"', '"55555555-5555-5555-5555-555555555555"')
content = content.replace('"test-1"', '"66666666-6666-6666-6666-666666666666"')
content = content.replace('"nonexistent"', '"00000000-0000-0000-0000-000000000000"')

Path('tests/unit/test_repositories.py').write_text(content, encoding='utf-8')
