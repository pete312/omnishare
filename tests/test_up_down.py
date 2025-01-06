import httpx
from pathlib import Path
import json

# functional tests 
def test_up():
    res = httpx.get('http://localhost:2425/list/')
    assert res.status_code == 200
    print("here", json.loads(res.content))

    f1 = Path('/tmp/file1.txt')
    content = 'test this content'
    f1.write_text(content)

    with open(f1, 'rb') as file:
        files = {"file": ("this/file.txt", file, "application/octet-stream")}

        res = httpx.post('http://localhost:2425/files/', files=files )
        assert res.status_code == 200

    res = httpx.get('http://localhost:2425/list/')
    assert res.status_code == 200
    print(res.text)