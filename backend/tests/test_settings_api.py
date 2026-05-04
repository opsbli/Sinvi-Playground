from pathlib import Path


def test_settings_endpoint_returns_normalized_payload(api_client):
    response = api_client.get("/api/settings")

    assert response.status_code == 200
    payload = response.json()
    assert payload["model_profiles"]
    assert payload["active_model_profile_id"] in {item["id"] for item in payload["model_profiles"]}
    assert isinstance(payload["env_vars"], list)
    assert isinstance(payload["env_path"], str)


def test_settings_endpoint_accepts_round_trip_updates(api_client):
    current = api_client.get("/api/settings").json()
    updated = {
        "model_profiles": [
            {
                "id": "custom",
                "provider": "custom",
                "name": "Custom Profile",
                "api_key": "test-key",
                "base_url": "https://example.invalid/v1",
                "model": "gpt-test",
            }
        ],
        "active_model_profile_id": "custom",
        "env_vars": current["env_vars"],
        "env_path": current["env_path"],
    }

    response = api_client.put("/api/settings", json=updated)

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_model_profile_id"] == "custom"
    assert payload["model_profiles"][0]["name"] == "Custom Profile"
    env_path = Path(payload["env_path"])
    assert env_path.exists()
    env_text = env_path.read_text(encoding="utf-8")
    assert "OPENAI_API_KEY=test-key" in env_text
    assert "OPENAI_BASE_URL=https://example.invalid/v1" in env_text
    assert "OPENAI_MODEL=gpt-test" in env_text
