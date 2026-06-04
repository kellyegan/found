import importlib.metadata


def get_app_metadata() -> dict[str, str]:
    meta = importlib.metadata.metadata("found")
    return {
        "version": meta["Version"] or "",
        "license": meta["License"] or "",
    }
