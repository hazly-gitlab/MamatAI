import pytest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from app.tools.registry import (
    safe_eval,
    is_sql_safe,
    is_url_allowed,
    handle_calculator,
    execute_tool
)

def test_safe_calculator():
    # standard operations
    assert safe_eval("2 + 2") == 4
    assert safe_eval("sin(0)") == 0.0
    assert safe_eval("3 * 5 + 4") == 19

    # test dangerous/forbidden commands
    with pytest.raises(Exception):
        safe_eval("__import__('os').system('ls')")

    with pytest.raises(Exception):
        safe_eval("import os")

def test_sql_safety():
    # Select statements should pass
    assert is_sql_safe("SELECT * FROM users") is True
    assert is_sql_safe("select email, full_name from users where id = 1") is True

    # Modifying statements should fail
    assert is_sql_safe("DELETE FROM users") is False
    assert is_sql_safe("DROP TABLE users") is False
    assert is_sql_safe("UPDATE users SET email = 'hacker@malicious.com'") is False
    assert is_sql_safe("INSERT INTO users (email) VALUES ('hacker@malicious.com')") is False

def test_url_ssrf_protection():
    # Allowed domains (specified in backend/app/core/config.py)
    # Default list includes: "api.weatherapi.com,wttr.in,api.github.com"
    assert is_url_allowed("https://wttr.in/Kuala_Lumpur?format=j1") is True
    assert is_url_allowed("https://api.github.com/repos/fastapi/fastapi") is True
    assert is_url_allowed("https://api.weatherapi.com/v1/current.json") is True

    # Disallowed domains
    assert is_url_allowed("https://malicious-site.com/steal-data") is False
    assert is_url_allowed("http://192.168.1.1/admin-panel") is False
    assert is_url_allowed("http://localhost:8000/api/v1/users") is False
