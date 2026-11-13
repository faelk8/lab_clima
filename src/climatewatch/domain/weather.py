"""Contratos puros para observações horárias de clima."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo


class ContractError(ValueError):
    """Indica payload incompatível com o contrato climático."""


@dataclass(frozen=True, slots=True)
class Location:
    """Localidade de estudo com coordenadas verificadas."""

    location_id: str
    name: str
    latitude: float
    longitude: float
    timezone_name: str


@dataclass(frozen=True, slots=True)
class WeatherRecord:
    """Uma observação horária normalizada; chuva representa acumulado da hora anterior."""

    location_id: str
    measurement_time: datetime
    temperature_c: float | None
    precipitation_mm: float | None
    humidity_pct: float | None
    wind_speed_kmh: float | None
    source: str = "open-meteo"
    model: str = "unspecified"
    ingested_at: datetime | None = None
    quality_flags: tuple[str, ...] = ()
    contract_version: int = 1

    def __post_init__(self) -> None:
        """Valida invariantes independentes da infraestrutura."""
        if not self.location_id:
            raise ContractError("location_id não pode ser vazio")
        if self.measurement_time.tzinfo is None:
            raise ContractError("measurement_time precisa de timezone")
        if self.measurement_time.utcoffset() is None:
            raise ContractError("measurement_time precisa de offset válido")
        if self.precipitation_mm is not None and self.precipitation_mm < 0:
            raise ContractError("precipitation_mm não pode ser negativo")
        if self.humidity_pct is not None and not 0 <= self.humidity_pct <= 100:
            raise ContractError("humidity_pct deve estar entre 0 e 100")
        if self.contract_version != 1:
            raise ContractError("contract_version não suportada")


def parse_hourly_payload(
    payload: dict[str, Any], location: Location, ingested_at: datetime | None = None
) -> list[WeatherRecord]:
    """Converte a resposta hourly do Open-Meteo e rejeita arrays desalinhados."""
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or not isinstance(hourly.get("time"), list):
        raise ContractError("campo hourly.time ausente ou inválido")
    times = hourly["time"]
    columns = {
        "temperature_2m": "temperature_c",
        "precipitation": "precipitation_mm",
        "relative_humidity_2m": "humidity_pct",
        "wind_speed_10m": "wind_speed_kmh",
    }
    for key in columns:
        values = hourly.get(key)
        if not isinstance(values, list) or len(values) != len(times):
            raise ContractError(f"array hourly.{key} ausente ou desalinhado")
    try:
        ingested = ingested_at or datetime.now(timezone.utc)
        records = []
        for index, raw_time in enumerate(times):
            stamp = datetime.fromisoformat(raw_time)
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=ZoneInfo(location.timezone_name))
            stamp = stamp.astimezone(timezone.utc)
            values = {target: hourly[source][index] for source, target in columns.items()}
            records.append(
                WeatherRecord(location.location_id, stamp, **values, ingested_at=ingested)
            )
        return records
    except (TypeError, ValueError) as exc:
        raise ContractError(f"resposta hourly inválida: {exc}") from exc
