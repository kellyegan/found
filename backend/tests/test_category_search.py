"""Tests for GET /api/v1/categories/search?q="""


def _create_categories(client, *names):
    for name in names:
        client.post("/api/v1/categories", json={"name": name, "description": ""})


def _names(response_data):
    return [c["name"] for c in response_data]


def test_search_returns_partial_match(client):
    _create_categories(client, "Architecture", "Brutalism", "Archway")

    result = _names(client.get("/api/v1/categories/search?q=arch").json()["data"])
    assert "Architecture" in result
    assert "Archway" in result
    assert "Brutalism" not in result


def test_search_is_case_insensitive(client):
    _create_categories(client, "Architecture")

    result = _names(client.get("/api/v1/categories/search?q=ARCH").json()["data"])
    assert "Architecture" in result


def test_search_matches_middle_of_word(client):
    # "talis" appears in the middle of "Brutalism" (Bru-talis-m)
    _create_categories(client, "Brutalism", "Photography")

    result = _names(client.get("/api/v1/categories/search?q=talis").json()["data"])
    assert "Brutalism" in result
    assert "Photography" not in result


def test_search_prefix_matches_before_mid_word_matches(client):
    # "ology" is a prefix match for "Ology" but mid-word in "Archaeology" and "Ecology"
    # which would come first alphabetically without prefix-first ordering
    _create_categories(client, "Archaeology", "Ecology", "Ology")

    result = _names(client.get("/api/v1/categories/search?q=ology").json()["data"])
    assert result[0] == "Ology"
    assert set(result[1:]) == {"Archaeology", "Ecology"}


def test_search_alphabetical_within_each_group(client):
    # All start with "U" — should be alphabetical within the prefix group
    _create_categories(client, "Urban", "Underground", "Ultramodern")

    result = _names(client.get("/api/v1/categories/search?q=U").json()["data"])
    assert result == sorted(result)


def test_search_mid_word_group_also_alphabetical(client):
    _create_categories(client, "Minimalism", "Brutalism", "Futurism")

    result = _names(client.get("/api/v1/categories/search?q=ism").json()["data"])
    assert result == sorted(result)


def test_search_returns_empty_list_when_no_match(client):
    _create_categories(client, "Architecture", "Brutalism")

    result = client.get("/api/v1/categories/search?q=zzz").json()["data"]
    assert result == []


def test_search_empty_query_returns_all_categories_alphabetically(client):
    _create_categories(client, "Urban", "Nature", "Architecture")

    result = _names(client.get("/api/v1/categories/search?q=").json()["data"])
    assert set(result) == {"Urban", "Nature", "Architecture"}
    assert result == sorted(result)


def test_search_response_shape(client):
    _create_categories(client, "Architecture")

    response = client.get("/api/v1/categories/search?q=arch")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "id" in data["data"][0]
    assert "name" in data["data"][0]
