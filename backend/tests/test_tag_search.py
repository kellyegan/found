"""Tests for GET /api/v1/tags/search?q="""


def _create_tags(client, *names):
    for name in names:
        client.post("/api/v1/tags", json={"name": name})


def _names(response_data):
    return [t["name"] for t in response_data]


def test_search_returns_partial_match(client):
    _create_tags(client, "architecture", "brutalism", "archway")

    result = _names(client.get("/api/v1/tags/search?q=arch").json()["data"])
    assert "architecture" in result
    assert "archway" in result
    assert "brutalism" not in result


def test_search_is_case_insensitive(client):
    _create_tags(client, "architecture")

    result = _names(client.get("/api/v1/tags/search?q=ARCH").json()["data"])
    assert "architecture" in result


def test_search_matches_middle_of_word(client):
    # "talis" is in the middle of "brutalism" (bru-talis-m)
    _create_tags(client, "brutalism", "photography")

    result = _names(client.get("/api/v1/tags/search?q=talis").json()["data"])
    assert "brutalism" in result
    assert "photography" not in result


def test_search_results_ordered_alphabetically(client):
    _create_tags(client, "urban", "underground", "ultramodern")

    result = _names(client.get("/api/v1/tags/search?q=u").json()["data"])
    assert result == sorted(result)


def test_search_returns_empty_list_when_no_match(client):
    _create_tags(client, "architecture", "brutalism")

    result = client.get("/api/v1/tags/search?q=zzz").json()["data"]
    assert result == []


def test_search_empty_query_returns_all_tags_alphabetically(client):
    _create_tags(client, "urban", "nature", "architecture")

    result = _names(client.get("/api/v1/tags/search?q=").json()["data"])
    assert set(result) == {"urban", "nature", "architecture"}
    assert result == sorted(result)


def test_search_response_shape(client):
    _create_tags(client, "architecture")

    response = client.get("/api/v1/tags/search?q=arch")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"][0]
    assert "name" in data["data"][0]
