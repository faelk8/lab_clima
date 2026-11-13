"""Smoke HTTP do dashboard com leitor Gold injetado e sem acesso à rede externa."""

from datetime import date
from http.server import ThreadingHTTPServer
from threading import Thread
from unittest.mock import Mock
from urllib.request import urlopen

from climatewatch.interfaces.dashboard import create_handler, render_dashboard


def test_dashboard_displays_gold_sample_and_units() -> None:
    html = render_dashboard(
        [{"local_date": date(2024, 1, 1), "precipitation_mm": 2.5,
          "temperature_avg_c": 20.0, "observed_hours": 24, "expected_hours": 24}],
        [{"location_id": "sp", "name": "São Paulo"}],
        "sp", date(2024, 1, 1), date(2024, 1, 1),
    )

    assert "São Paulo" in html
    assert "2.5 mm" in html
    assert "20.0 °C" in html
    assert "24/24" in html
    assert "<svg" in html


def test_dashboard_http_smoke_and_empty_period_message() -> None:
    query = Mock()
    query.daily.return_value = []
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0),
        create_handler(query, [{"location_id": "sp", "name": "São Paulo"}]),
    )
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/?location=sp") as response:
            page = response.read().decode()
        assert "Não há dados Gold" in page
        query.daily.assert_called_once_with("sp", date(2024, 1, 1), date(2024, 1, 31))
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
