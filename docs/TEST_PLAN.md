# Unit Test Plan

**Goal:** keep testing simple but make it automatic

## Stack

* Test runner: **pytest** (+ **pytest‑cov** for coverage)
* HTML checks: **beautifulsoup4**
* CI: **GitHub Actions**

## Layout

```
tests/
  test_routes.py
  test_models.py
  test_requirements.py
```

## Local use

```bash
pip install pytest pytest-cov beautifulsoup4
pytest -q --cov=. --cov-report=term-missing
```

## CI (automatic on every push/PR)

Create **.github/workflows/ci.yml**

```yaml
name: CI (Python only)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-cov beautifulsoup4 Flask Flask-SQLAlchemy Flask-Migrate
      - name: Run tests
        env:
          PYTHONPATH: .
        run: pytest -q --cov=. --cov-report=term-missing --cov-fail-under=70
```

## Sample environment

```python
# tests/conftest.py
import pytest
from app import create_app
from models.models import db

@pytest.fixture()
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.app_context():
        db.drop_all(); db.create_all()
        try:
            from seed_courses import seed
            seed(db.session)
            db.session.commit()
        except Exception:
            db.session.rollback()
        yield app.test_client()
```

## Sample tests

```python
# tests/test_routes.py

def test_semesters_list(client):
    r = client.get('/api/semesters')
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)


def test_add_class_limits(client):
    sems = client.get('/api/semesters').get_json()
    sem_id = sems[0]['id']
    import json
    for code in ['CSCI 135','CSCI 145','CSCI 220','CSCI 330','MATH 160']:
        res = client.get(f"/api/courses?q={code}&unassigned=0").get_json()
        cid = next((c['id'] for c in res if c['code'] == code), None)
        assert cid is not None
        r = client.post('/api/classes', data=json.dumps({'course_id': cid, 'semester_id': sem_id}), headers={'Content-Type':'application/json'})
        if r.status_code == 409:
            assert 'credit' in r.get_data(as_text=True).lower()
            break
```

```python
# tests/test_requirements.py

def test_prereq_anchor_rules(client):
    r = client.get('/api/requirements?current_term=FALL')
    assert r.status_code == 200
    data = r.get_json()
    assert 'groups' in data and len(data['groups']) > 0
```
