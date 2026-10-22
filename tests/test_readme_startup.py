from pathlib import Path


def test_readme_has_reproducible_mock_and_persistent_recipes():
    text = Path("README.md").read_text(encoding="utf-8")
    for token in (
        "https://github.com/daycry/music-studio.git",
        "scripts/bootstrap.ps1",
        "scripts/init_env.py",
        "scripts/e2e_stack.py up",
        "scripts/e2e_stack.py down",
        "docker-compose.storage.yml",
        "STUDIO_STORAGE_UUID",
        "ollama ps",
        "WSL2",
    ):
        assert token in text
    assert "<remoto-privado>" not in text
