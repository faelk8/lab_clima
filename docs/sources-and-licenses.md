# Fontes, licenças e localidades

Consulta de geocoding executada em 13/11/2026. Coordenadas e timezone retornaram da API, filtrada por país BR; IDs são GeoNames/Open-Meteo.

| ID | Localidade | Latitude | Longitude | Fuso | ID geocoding |
|---|---|---:|---:|---|---:|
| br-sp-sao-paulo | São Paulo/SP | -23.5475 | -46.63611 | America/Sao_Paulo | 3448439 |
| br-pe-recife | Recife/PE | -8.05389 | -34.88111 | America/Recife | 3390760 |
| br-am-manaus | Manaus/AM | -3.10194 | -60.025 | America/Manaus | 3663517 |

Fonte de coordenadas: [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api), endpoint `https://geocoding-api.open-meteo.com/v1/search`, com consulta por nome, `countryCode=BR`, `count=1`, `language=pt`. Coordenadas representam o ponto de geocoding da localidade, não uma estação meteorológica.

Histórico climático: [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api), `https://archive-api.open-meteo.com/v1/archive`. A documentação informa produtos de reanálise/modelos com diferentes grades e períodos. Nunca rotular esses dados como observação direta em estação. O payload pode incluir metadados de modelo; se não vierem, `model` permanece `unspecified` até a camada de parsing determinar origem.

Termos consultados: [Open-Meteo Terms](https://open-meteo.com/en/terms). O acesso gratuito é para uso não comercial e exige atribuição CC BY 4.0, sujeito aos limites e termos atuais. Revisar antes de uso promocional/comercial e antes de distribuir dados derivados. INMET fica fora da Fase 1.

Dados climáticos ainda não foram baixados. As fixtures em `data/fixtures` são sintéticas e não representam medições.
