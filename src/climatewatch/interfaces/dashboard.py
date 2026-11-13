"""Dashboard local, sem chamadas de rede, para explorar as tabelas Gold."""

from __future__ import annotations

import argparse
import html
import json
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from climatewatch.application.query_gold import QueryGold
from climatewatch.infrastructure.gold_reader import GoldReader

LOCATIONS_PATH = Path("config/locations.json")


def render_dashboard(
    rows: list[dict[str, Any]],
    locations: list[dict[str, str]],
    selected_location: str,
    start: date,
    end: date,
) -> str:
    """Renderiza controles, métricas e gráfico SVG com conteúdo escapado."""
    options = "".join(
        '<option value="{}" {}>{}</option>'.format(
            html.escape(item["location_id"], quote=True),
            "selected" if item["location_id"] == selected_location else "",
            html.escape(item["name"]),
        )
        for item in locations
    )
    if not rows:
        visualization = '<p role="status">Não há dados Gold para este local e período.</p>'
    else:
        values = [
            float(row["precipitation_mm"])
            for row in rows
            if row.get("precipitation_mm") is not None
        ]
        maximum = max(values, default=0.0) or 1.0
        bars = []
        for index, row in enumerate(rows):
            value = row.get("precipitation_mm")
            if value is None:
                continue
            height = max(1, round(float(value) / maximum * 140))
            x = 50 + index * 42
            label = html.escape(str(row["local_date"]))
            bars.append(
                f'<rect x="{x}" y="{170-height}" width="26" height="{height}" fill="#2878b5">'
                f'<title>{label}: {float(value):.1f} mm</title></rect>'
            )
        visualization = (
            '<svg role="img" aria-label="Precipitação diária em milímetros" '
            'viewBox="0 0 900 200" preserveAspectRatio="xMinYMin meet">'
            + "".join(bars)
            + '<text x="10" y="18">Precipitação (mm)</text></svg>'
        )
    map_markup = _render_location_map(locations, selected_location)
    table_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(row.get('local_date', '')))}</td>"
        f"<td>{_format(row.get('precipitation_mm'), 'mm')}</td>"
        f"<td>{_format(row.get('temperature_avg_c'), '°C')}</td>"
        f"<td>{row.get('observed_hours', 0)}/{row.get('expected_hours', 0)}</td>"
        "</tr>"
        for row in rows
    )
    return f"""<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>ClimateWatch — painel Gold</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:2rem auto;padding:0 1rem;color:#17324d}}
form{{display:flex;gap:1rem;align-items:end;flex-wrap:wrap}}label{{display:grid;gap:.3rem}}
button{{padding:.5rem 1rem}}svg{{width:100%;height:220px;background:#f3f8fc}}
table{{border-collapse:collapse;width:100%}}
th,td{{padding:.6rem;border-bottom:1px solid #ccd8e2;text-align:left}}</style>
<h1>ClimateWatch</h1><p>Séries históricas locais das tabelas Gold.</p>
<form method="get"><label>Local<select name="location">{options}</select></label>
<label>De<input type="date" name="start" value="{start.isoformat()}" required></label>
<label>Até<input type="date" name="end" value="{end.isoformat()}" required></label>
<button type="submit">Consultar Gold</button></form><section>{visualization}</section>
<section><h2>Localidades verificadas</h2>
<p>Mapa esquemático local, usado como alternativa offline sem mapa externo.</p>
<p>Legenda: <span style="color:#d1495b">● vermelho: local selecionado</span>;
<span style="color:#2878b5">● azul: demais localidades</span>.</p>
{map_markup}
<p>Coordenadas do catálogo local; dados históricos modelados, sem valor de alerta ou risco oficial.
</p><p>Coordenadas e nomes: <a href="https://open-meteo.com/en/docs/geocoding-api">
Open-Meteo Geocoding API</a>. Clima:
<a href="https://open-meteo.com/en/docs/historical-weather-api">
Open-Meteo Historical Weather API</a>.
Agregação diária civil por fuso local; cobertura horária indicada na tabela.</p></section>
<table><thead><tr><th>Data local</th><th>Chuva</th><th>Temperatura média</th>
<th>Cobertura</th></tr></thead>
<tbody>{table_rows}</tbody></table></html>"""


def _format(value: Any, unit: str) -> str:
    return "—" if value is None else f"{float(value):.1f} {unit}"


def _render_location_map(locations: list[dict[str, Any]], selected: str) -> str:
    """Renderiza pontos relativos às coordenadas do catálogo, sem mapa remoto."""
    if not locations or any(
        "latitude" not in item or "longitude" not in item for item in locations
    ):
        return "<p role=\"status\">Mapa indisponível: coordenadas locais ausentes.</p>"
    latitudes = [float(item["latitude"]) for item in locations]
    longitudes = [float(item["longitude"]) for item in locations]
    min_lat, max_lat = min(latitudes), max(latitudes)
    min_lon, max_lon = min(longitudes), max(longitudes)
    lat_span, lon_span = max(max_lat - min_lat, 0.1), max(max_lon - min_lon, 0.1)
    points = []
    for item in locations:
        x = 40 + (float(item["longitude"]) - min_lon) / lon_span * 320
        y = 30 + (max_lat - float(item["latitude"])) / lat_span * 180
        color = "#d1495b" if item["location_id"] == selected else "#2878b5"
        label = html.escape(item["name"])
        points.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}">'
            f"<title>{label}</title></circle>"
            f"<text x=\"{x + 12:.1f}\" y=\"{y + 4:.1f}\">{label}</text>"
        )
    return ('<svg role="img" aria-label="Mapa esquemático de localidades verificadas" '
            'viewBox="0 0 700 250">' + "".join(points) + "</svg>")


def create_handler(
    query: QueryGold, locations: list[dict[str, str]]
) -> type[BaseHTTPRequestHandler]:
    """Cria handler injetável para teste, sem disparar ingestão ou rede externa."""

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            location = params.get("location", [locations[0]["location_id"]])[0]
            if location not in {item["location_id"] for item in locations}:
                self.send_error(400, "Localidade inválida")
                return
            try:
                start = date.fromisoformat(params.get("start", ["2024-01-01"])[0])
                end = date.fromisoformat(params.get("end", ["2024-01-31"])[0])
                rows = query.daily(location, start, end)
            except ValueError as exc:
                self.send_error(400, str(exc))
                return
            content = render_dashboard(rows, locations, location, start, end).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format_string: str, *args: object) -> None:
            return

    return DashboardHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Painel local de dados climáticos Gold")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    locations_data = json.loads(LOCATIONS_PATH.read_text(encoding="utf-8"))
    locations = [
        {"location_id": item["location_id"], "name": item["name"],
         "latitude": item["latitude"], "longitude": item["longitude"]}
        for item in locations_data["locations"]
    ]
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.master("local[*]")
        .config("spark.sql.catalogImplementation", "hive")
        .config("spark.sql.warehouse.dir", "data/warehouse/f3/warehouse")
        .enableHiveSupport()
        .getOrCreate()
    )
    handler = create_handler(QueryGold(GoldReader(spark)), locations)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"ClimateWatch disponível em http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        spark.stop()


if __name__ == "__main__":
    main()
