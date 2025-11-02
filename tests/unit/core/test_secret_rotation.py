from datetime import datetime, timedelta, UTC
from platform.security.secret_rotation import register, promote, retire_previous, get_current, get_previous, previous_available, validate_grace

def test_register_and_promote():
    register('api_key', 'API_KEY:v1', activated_at=datetime.now(UTC) - timedelta(hours=2))
    assert get_current('api_key') == 'API_KEY:v1'
    assert get_previous('api_key') is None
    promote('api_key', 'API_KEY:v2')
    assert get_current('api_key') == 'API_KEY:v2'
    assert get_previous('api_key') == 'API_KEY:v1'

def test_previous_available_and_retire_blocked():
    register('svc', 'SVC:v1')
    promote('svc', 'SVC:v2')
    assert previous_available('svc') is True
    assert retire_previous('svc') is False
    assert retire_previous('svc', ignore_grace=True) is True
    assert get_previous('svc') is None

def test_validate_grace_violation():
    past = datetime.now(UTC) - timedelta(hours=30)
    register('rotate_me', 'ROTATE:v1', activated_at=past)
    promote('rotate_me', 'ROTATE:v2')
    assert validate_grace('rotate_me') is True