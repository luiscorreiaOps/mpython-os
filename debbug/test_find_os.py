import pytest
from find_os import parse_beacon, check_web_interface

class TestParseBeacon:
    def test_valid_beacon(self):
        # Beacon
        data = b'{"name": "luisos", "ip": "192.168.1.100"}'
        result = parse_beacon(data)
        assert result == {"name": "luisos", "ip": "192.168.1.100"}
    
    def test_invalid_json(self):
        # JSON
        data = b'invalid json'
        result = parse_beacon(data)
        assert result is None
    
    def test_wrong_name(self):
        # Beacon nome errado
        data = b'{"name": "other", "ip": "192.168.1.100"}'
        result = parse_beacon(data)
        assert result is None
    
    def test_missing_name(self):
        # Beacon sem 'name'
        data = b'{"ip": "192.168.1.100"}'
        result = parse_beacon(data)
        assert result is None

class TestCheckWebInterface:
    @pytest.fixture
    def mock_requests_success(self, monkeypatch):
    # Mock requests.get ok
        class MockResponse:
            status_code = 200
            def json(self):
                return {"motd": "Bem-vindo ao LuisOS"}
        
        def mock_get(*args, **kwargs):
            return MockResponse()
        
        monkeypatch.setattr("requests.get", mock_get)
    
    @pytest.fixture
    def mock_requests_failure(self, monkeypatch):
     # Mock para requests.get com falha
        def mock_get(*args, **kwargs):
            raise requests.exceptions.ConnectTimeout("Timeout")
        
        monkeypatch.setattr("requests.get", mock_get)
    
    def test_check_web_interface_success(self, mock_requests_success):
        success, response_time, motd = check_web_interface("192.168.1.100")
        assert success is True
        assert response_time >= 0
        assert motd == "Bem-vindo ao OS"
    
    def test_check_web_interface_failure(self, mock_requests_failure):
        success, response_time, error = check_web_interface("192.168.1.100")
        assert success is False
        assert "Timeout" in error