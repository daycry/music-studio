from pathlib import Path


def test_persistent_compose_requires_storage_uuid_for_all_consumers():
    text = Path("docker-compose.storage.yml").read_text(encoding="utf-8")
    expected = "STUDIO_STORAGE_UUID: ${STUDIO_STORAGE_UUID:?Falta UUID ext4 acreditado}"
    assert text.count(expected) == 4
    for service in ("server:", "engine-mock:", "engine-analysis:", "engine-acestep:"):
        start = text.index(f"  {service}")
        next_service = min(
            (
                pos
                for pos in (
                    text.find(f"\n  {candidate}", start + 3)
                    for candidate in (
                        "server:",
                        "engine-mock:",
                        "engine-analysis:",
                        "engine-acestep:",
                    )
                )
                if pos != -1
            ),
            default=-1,
        )
        block = text[start:] if next_service == -1 else text[start:next_service]
        assert expected in block
