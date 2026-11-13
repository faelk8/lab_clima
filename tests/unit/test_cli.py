"""Testes do catálogo da interface."""

from pathlib import Path

from climatewatch.interfaces.cli import load_locations


def test_loads_three_verified_locations() -> None:
    """Carrega IDs estáveis e fusos IANA do catálogo versionado."""
    locations = load_locations(Path("config/locations.json"))
    assert set(locations) == {"br-sp-sao-paulo", "br-pe-recife", "br-am-manaus"}
