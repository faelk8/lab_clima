# Runbook de ingestão batch

## Coleta de uma janela

```bash
poetry run climatewatch-download --location-id br-sp-sao-paulo \
  --start 2026-10-01 --end 2026-10-07 \
  --variables temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m
```

A saída bruta fica em `data/raw`; cache, manifesto e quarentena ficam no diretório local `data/` e são ignorados pelo Git. Não apague esses diretórios durante recuperação sem revisar o conteúdo.

## Backfill de três localidades

```bash
poetry run python scripts/backfill_weather.py \
  --start 2026-10-01 --end 2026-10-30 --max-days 7 --max-requests 30
```

Cada janela usa datas inclusivas. Limite default 7 dias, no máximo 30 requests na execução incluindo retries. Para simular sem API, use testes com cliente falso; backfill real é opt-in.

## Retomar falhas/interrupções

```bash
poetry run python scripts/resume_batches.py
```

Estados `running` remanescentes de encerramento abrupto e `failed` são reexecutados pelos parâmetros persistidos, incluindo coordenadas e fuso, no manifesto selecionado. O claim com lock por lote serializa retomada e execução ativa; se o processo morrer, o sistema operacional libera o lock e a nova execução pode recuperar o estado. Lotes concluídos são ignorados. Antes de nova tentativa, verifique rede, causa no manifesto e espaço em disco. Não remova raw nem cache para tentar resolver erro de contrato.

Uma execução de retomada compartilha um orçamento de no máximo 30 requests e 100 MiB entre todos os lotes, incluindo retries. Ajuste com `--max-requests` e `--max-total-bytes`; lotes que ficarem sem orçamento permanecem pendentes para outra execução. A leitura do corpo é limitada ao saldo restante mais um byte sentinela, necessário para detectar resposta acima do limite; esse byte também entra na contagem.

## Falhas e recuperação

- HTTP 429: esperar `Retry-After`; o código repete até três tentativas e interrompe no orçamento.
- HTTP 5xx, timeout ou falha de conexão: backoff exponencial limitado; repetir a execução depois de verificar a disponibilidade.
- HTTP 4xx não recuperável: sem retry; revisar intervalo, parâmetros e variáveis.
- JSON válido mas contrato inválido: raw permanece no armazenamento, registro vai para `data/quarantine` e manifesto fica `failed` com referência ao raw. Corrigir código/contrato e retomar o mesmo lote.
- Interrupção de processo: manifesto mostra `running`; o comando de retomada consulta de novo. Escritas JSON usam temporário e rename atômico.
- Cobertura do backfill compara timestamps horários únicos normalizados com o intervalo esperado; duplicatas e horários extras são reportados separadamente e não compensam lacunas.
- Falha de disco: não marcar lote como concluído; libere espaço por procedimento manual, preservando raw existente, depois retome.
- Dados corrigidos pela fonte: `--force-refresh` no downloader ignora lote concluído; se a coleta falhar, a intenção fica no manifesto e a retomada também ignora o cache anterior. Conteúdo com novo hash é acrescentado em `versions`, sem apagar versão anterior.
- Raw removido de lote concluído: a próxima execução detecta a ausência, reabre o lote e consulta a origem ignorando o cache. O payload recuperado é gravado antes de voltar a `succeeded`; hash já registrado não cria uma versão duplicada.

O processo garante idempotência de arquivos com conteúdo igual, não exactly-once transacional entre API, cache, raw e manifesto.

## Reprocessar Bronze, Silver e Gold

```bash
docker compose run --build --rm climatewatch spark-pipelines dry-run --spec /app/spark-pipeline.yml
docker compose run --build --rm climatewatch spark-pipelines run --spec /app/spark-pipeline.yml
```

O catálogo Hive e os dados do SDP persistem em `data/warehouse/f3` e `data/warehouse/sdp`. Preserve esses diretórios durante recuperação. O `run` relê os objetos raw com sidecar, aplica rejeições em `silver_rejected`, resolve revisões por instante de ingestão e recalcula Gold. Examine flags de qualidade antes de tentar corrigir a origem. Uma falha de schema ou de execução não deve levar à remoção dos objetos raw; corrija o dado ou transformação, valide com `dry-run` e repita `run`. O teste opt-in `CLIMATEWATCH_F3_REPLAY=1 poetry run pytest -q tests/integration/test_pipeline_replay.py` verifica replay e correção histórica.
