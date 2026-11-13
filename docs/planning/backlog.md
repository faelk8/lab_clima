# Backlog local — ClimateWatch

[Plano](../plan.md) · [Guia do executor](execution-guide.md)

Todas as tarefas F1–F5 estão **PLANEJADAS**. Modelo: `gpt-6-luna`; esforço: `medium`. P/M são esforço relativo, sem promessa de prazo. A ordem abaixo é sequencial; além das dependências explícitas, a tarefa anterior da fase deve estar validada. Cada fase exige comando do usuário. Toda tarefa inclui testes próprios, evidência por ID, atualização documental pertinente e conferência do coordenador.

F0-01: auditoria local; F0-02: pesquisa documental; F0-03: plano e backlog. Entregas locais desta conversa; PoCs de execução não realizadas.

## Fase 1 — Fonte, contratos e protótipo mínimo

| ID | Entrega | Esforço | Dependências |
|---|---|---|---|
| F1-01 | Base Python e ferramentas | P | F0-03 |
| F1-02 | PoC isolada do runtime SDP e Docker | M | F1-01 |
| F1-03 | Catálogo de localidades e fontes | P | F1-01 |
| F1-04 | Fixtures horárias pequenas | P | F1-03 |
| F1-05 | Contrato v1 e invariantes | M | F1-04 |
| F1-06 | HTTP mínimo com timeouts | P | F1-05 |
| F1-07 | Persistência raw atômica | P | F1-05 |
| F1-08 | Caso de uso e CLI do downloader | M | F1-06, F1-07 |
| F1-09 | Smoke online curto e fechamento da fase | P | F1-02, F1-08 |

### F1-01 — Base Python e ferramentas

- **Entrada:** F0-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** pyproject.toml, uv.lock, Makefile. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Criar pacote mínimo e grupos de dependências; fixar ferramentas de qualidade.
- **Aceite:** Instalação limpa, import climatewatch, Ruff e mypy executados. Não adicionar dependências opcionais.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-01.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-02 — PoC isolada do runtime SDP e Docker

- **Entrada:** F1-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** Dockerfile, docker-compose.yml, tests/integration/test_sdp_smoke.py, docs/adr/0002-*.md e 0003-*.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Inventariar recursos; selecionar versões oficiais compatíveis; executar uma tabela mínima em diretório temporário.
- **Aceite:** Import dp, CLI --help, dry-run, run e leitura de valor conhecido persistido passam; registrar versões e consumo. Dividir diagnóstico e integração se necessário.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-02.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-03 — Catálogo de localidades e fontes

- **Entrada:** F1-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** config/locations.json, docs/sources-and-licenses.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Verificar três localidades brasileiras, coordenadas e timezone; registrar fontes, termos e política de atribuição.
- **Aceite:** Três entradas sem ambiguidades de país/UF, evidência de geocoding e URLs/datas; sem coordenadas presumidas.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-03.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-04 — Fixtures horárias pequenas

- **Entrada:** F1-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** data/fixtures/, tests/contracts/test_fixtures.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Criar casos sintéticos identificados: regular, nulos, arrays inconsistentes e limites de dia.
- **Aceite:** Fixtures têm manifesto, hash e resultados esperados independentes; não há dependência de rede.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-04.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-05 — Contrato v1 e invariantes

- **Entrada:** F1-04 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** contracts/, src/climatewatch/domain/, docs/data-contracts.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Definir tipos, unidades, chave, intervalo da chuva, proveniência e erros; documentar ADR temporal.
- **Aceite:** Exemplos válidos/inválidos, limites de umidade/precipitação e datas são testados; domínio não importa Spark/HTTP.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-05.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-06 — HTTP mínimo com timeouts

- **Entrada:** F1-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/infrastructure/weather_http.py, tests/unit/test_weather_http.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Implementar request parametrizado com timeout e tradução explícita de erros, sem retry nesta tarefa.
- **Aceite:** Mock valida parâmetros e cobre 200, timeout, JSON inválido e 4xx; nenhuma chamada HTTP em decorator SDP.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-06.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-07 — Persistência raw atômica

- **Entrada:** F1-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/infrastructure/raw_store.py, tests/unit/test_raw_store.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Salvar payload íntegro e metadados com hash e escrita temporária atômica.
- **Aceite:** Bytes iguais à origem; falha de escrita não publica objeto parcial; segredos não aparecem em metadados.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-07.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-08 — Caso de uso e CLI do downloader

- **Entrada:** F1-06, F1-07 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/application/download.py, src/climatewatch/interfaces/cli.py, scripts/download_weather.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Conectar portas mínimas e flags --location-id, --start, --end, --variables; validar limites antes de HTTP.
- **Aceite:** CLI rejeita intervalo invertido, local desconhecido e variável inválida; cenário offline gera raw e metadados.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-08.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F1-09 — Smoke online curto e fechamento da fase

- **Entrada:** F1-02, F1-08 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** tests/integration/test_weather_online.py, docs/evidence/F1-09.md, docs/linkedin/01.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Executar consulta pequena opt-in; catalogar amostra autorizada e preparar rascunho 1/5.
- **Aceite:** Online e offline reportados separadamente; nenhuma métrica sem log; contratos compatíveis com resposta. Sem rede: gate online pendente.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F1-09.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

## Fase 2 — Incrementalidade e resiliência batch

| ID | Entrega | Esforço | Dependências |
|---|---|---|---|
| F2-01 | Planejamento de intervalos | P | F1-09 |
| F2-02 | Cache, retry e rate limit | M | F2-01 |
| F2-03 | Manifesto e idempotência de coleta | M | F2-02 |
| F2-04 | Retomada e quarentena de ingestão | M | F2-03 |
| F2-05 | Falhas controladas e runbook inicial | P | F2-04 |
| F2-06 | Backfill real de 30 dias | M | F2-05 |
| F2-07 | Evidência e post 2/5 | P | F2-06 |

### F2-01 — Planejamento de intervalos

- **Entrada:** F1-09 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/application/windows.py, tests/unit/test_windows.py, docs/adr/0001-batch.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Dividir período em janelas e definir limites; justificar batch sem Kafka.
- **Aceite:** Meses/anos bissextos e fronteiras não perdem nem duplicam horas; volume previsto cabe no orçamento.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-01.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-02 — Cache, retry e rate limit

- **Entrada:** F2-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/infrastructure/http_policy.py, tests/unit/test_http_policy.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Adicionar cache por parâmetros normalizados, TTL, Retry-After, backoff e orçamento global.
- **Aceite:** Relógio/espera simulados; 429/5xx recuperam dentro do teto, 4xx definitivo não repete; expiração e cache hit comprovados.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-02.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-03 — Manifesto e idempotência de coleta

- **Entrada:** F2-02 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/infrastructure/batch_manifest.py, tests/unit/test_batch_manifest.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Registrar planejado/em andamento/concluído/falhou; um escritor; detectar hash repetido e conteúdo corrigido.
- **Aceite:** Segundo processamento reutiliza payload idêntico; conteúdo alterado preserva duas versões; manifesto nunca afirma sucesso antes da persistência.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-03.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-04 — Retomada e quarentena de ingestão

- **Entrada:** F2-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/application/resume.py, tests/integration/test_resume.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Recuperar lote interrompido e registrar rejeições com motivo e referência raw.
- **Aceite:** Interromper entre raw e manifesto, reiniciar e reconciliar; JSON/campos inválidos não desaparecem nem derrubam silenciosamente demais lotes.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-04.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-05 — Falhas controladas e runbook inicial

- **Entrada:** F2-04 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** tests/integration/test_ingestion_failures.py, docs/runbook.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Simular timeout, disco indisponível, atraso e reexecução; documentar recuperação segura.
- **Aceite:** Nenhum raw anterior perdido; contagens conciliadas, comandos e saída registrados; sem apagar checkpoints automaticamente.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-05.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-06 — Backfill real de 30 dias

- **Entrada:** F2-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/data-catalog.md, docs/evidence/F2-06.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Escolher intervalo histórico fechado disponível e coletar três localidades dentro dos limites; guardar dados fora do Git.
- **Aceite:** Cobertura por local, horas faltantes, bytes, requests, hashes e duração medidos; repetir intervalo e comparar. Não declarar cobertura completa quando houver lacunas.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-06.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F2-07 — Evidência e post 2/5

- **Entrada:** F2-06 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/linkedin/02.md, docs/learning-notes.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Explicar falha/recuperação, batch e qualidade com números dos relatórios.
- **Aceite:** Texto rastreável, rascunho sem publicação e gate da fase documentado.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F2-07.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

## Fase 3 — Spark Declarative Pipelines

| ID | Entrega | Esforço | Dependências |
|---|---|---|---|
| F3-01 | Configuração SDP definitiva | P | F2-07 |
| F3-02 | Bronze e proveniência | M | F3-01 |
| F3-03 | Silver: schema, unidades e qualidade | M | F3-02 |
| F3-04 | Silver: tempo e deduplicação | M | F3-03 |
| F3-05 | Gold diária | M | F3-04 |
| F3-06 | Gold: janelas e ranking | M | F3-05 |
| F3-07 | Replay, atraso e schema drift | M | F3-06 |
| F3-08 | Aceite SDP e comparação didática | P | F3-07 |

### F3-01 — Configuração SDP definitiva

- **Entrada:** F2-07 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** spark-pipeline.yml, src/climatewatch/pipelines/__init__.py, Makefile. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Promover configuração da PoC; isolar warehouse de teste e definir comandos reais.
- **Aceite:** dry-run funciona na imagem fixada e não acessa HTTP; catálogo e caminhos não colidem com outros projetos.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-01.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-02 — Bronze e proveniência

- **Entrada:** F3-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/pipelines/bronze.py, tests/integration/test_bronze.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Ler raw e metadados preservando payload e linhagem; não repetir downloader.
- **Aceite:** run persiste Bronze; hash/origem/lote conciliam com fixture; leitura da tabela confirma conteúdo.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-02.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-03 — Silver: schema, unidades e qualidade

- **Entrada:** F3-02 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/pipelines/silver.py, tests/integration/test_silver.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Expandir arrays, aplicar schema/unidades, quality_flags e separar inválidos.
- **Aceite:** Arrays desalinhados, nulos, unidade inesperada e campo obrigatório ausente testados; contagens aceitas/rejeitadas conciliam.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-03.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-04 — Silver: tempo e deduplicação

- **Entrada:** F3-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/pipelines/silver.py, tests/integration/test_silver_time.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Normalizar UTC, chave e precedência determinística; derivar dia local conforme intervalo de acumulação.
- **Aceite:** Duplicata idêntica, revisão posterior, empate, virada de dia e DST 23/25h têm resultados previstos explicitamente.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-04.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-05 — Gold diária

- **Entrada:** F3-04 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/pipelines/gold_daily.py, tests/integration/test_gold_daily.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Calcular chuva diária, temperatura média/máxima e cobertura por local/fonte/modelo.
- **Aceite:** Valores comparados a cálculo manual; nulo não vira zero, dia incompleto sinalizado, duas fontes não são somadas.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-05.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-06 — Gold: janelas e ranking

- **Entrada:** F3-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/pipelines/gold_indicators.py, tests/integration/test_gold_indicators.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Calcular janela de 24h e séries móveis; ranking de localidades por período/cobertura equivalente.
- **Aceite:** Janela temporal não equivale a últimas 24 linhas; lacunas, fronteira do período, empate e cobertura insuficiente testados.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-06.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-07 — Replay, atraso e schema drift

- **Entrada:** F3-06 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** tests/integration/test_pipeline_replay.py, docs/evidence/F3-07.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Executar conjunto completo duas vezes; inserir correção histórica e mudança controlada de schema.
- **Aceite:** Unicidade e valores iguais no replay; correção recalcula dias/janelas; campo opcional tolerado e incompatível rejeitado; estado de falha documentado.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-07.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F3-08 — Aceite SDP e comparação didática

- **Entrada:** F3-07 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/architecture.md, docs/adr/0002-*.md, docs/linkedin/03.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Registrar DAG, schemas e consultas; comparar pequena transformação equivalente PySpark imperativa.
- **Aceite:** dry-run e run completos com saída persistida e conferida; explicar responsabilidades sem benchmark inventado; post 3/5 rastreável.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F3-08.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

## Fase 4 — Produto, indicadores e demonstração

| ID | Entrega | Esforço | Dependências |
|---|---|---|---|
| F4-01 | Leitor Gold com filtros | P | F3-08 |
| F4-02 | Dashboard básico e séries | M | F4-01 |
| F4-03 | Mapa, créditos e interpretação | P | F4-02 |
| F4-04 | Limiares experimentais locais | P | F4-03 |
| F4-05 | Métricas e diagnóstico | M | F4-04 |
| F4-06 | E2E offline e regressão | M | F4-05 |
| F4-07 | Demo e post 4/5 | P | F4-06 |

### F4-01 — Leitor Gold com filtros

- **Entrada:** F3-08 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/application/query_gold.py, src/climatewatch/infrastructure/gold_reader.py, tests/unit/test_query_gold.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Ler somente Gold, limitar linhas e validar local/período.
- **Aceite:** Filtros corretos, intervalo vazio e dados ausentes tratados; não carregar histórico ilimitado no driver.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-01.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-02 — Dashboard básico e séries

- **Entrada:** F4-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/interfaces/dashboard.py, tests/integration/test_dashboard.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Adicionar seleção de cidade/datas, série temporal, unidades e cobertura.
- **Aceite:** Smoke inicia painel; amostra conhecida mostra valores certos; período sem dados tem mensagem; leitor não faz download implícito.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-02.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-03 — Mapa, créditos e interpretação

- **Entrada:** F4-02 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/interfaces/dashboard.py, docs/evidence/F4-03.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Exibir localidades verificadas e legenda; fonte, resolução, período e natureza modelada visíveis.
- **Aceite:** Inspeção visual documentada; mapa não é apresentado como risco oficial; fallback informa ausência de mapa externo em modo offline.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-03.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-04 — Limiares experimentais locais

- **Entrada:** F4-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/domain/thresholds.py, tests/unit/test_thresholds.py, src/climatewatch/interfaces/dashboard.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Aplicar regra configurável de chuva em 24h com estado inconclusivo para cobertura insuficiente.
- **Aceite:** Abaixo/igual/acima do limiar, nulo e lacunas testados; nenhum envio de mensagem externa; valor é exemplo de demo, não limiar oficial.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-04.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-05 — Métricas e diagnóstico

- **Entrada:** F4-04 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** src/climatewatch/infrastructure/metrics.py, tests/unit/test_metrics.py, docs/runbook.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Consolidar contagens, retries, freshness, retrabalho, duração e consumo medido.
- **Aceite:** Cada métrica informa fórmula/origem; distinguir backfill antigo de atraso operacional; não expor segredos nos logs.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-05.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-06 — E2E offline e regressão

- **Entrada:** F4-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** tests/e2e/test_offline_demo.py, tests/contracts/test_architecture.py. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Rodar fixture → raw → Bronze → Silver → Gold → leitor/UI; verificar dependências entre camadas.
- **Aceite:** Rede bloqueada no fluxo offline, resultado conhecido validado, replay consistente e imports do domínio isolados.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-06.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F4-07 — Demo e post 4/5

- **Entrada:** F4-06 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/demo.md, docs/linkedin/04.md, docs/learning-notes.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Criar roteiro reproduzível e capturas reais quando possível; explicar limite da análise temporal.
- **Aceite:** Demo segue comandos testados; imagens/resultados não são fabricados; post cita evidências.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F4-07.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

## Fase 5 — Hardening, documentação e entrega local

| ID | Entrega | Esforço | Dependências |
|---|---|---|---|
| F5-01 | Configuração e segurança | P | F4-07 |
| F5-02 | Suíte final e reprodutibilidade | M | F5-01 |
| F5-03 | README, arquitetura e runbook finais | P | F5-02 |
| F5-04 | Portal Sphinx | M | F5-03 |
| F5-05 | Revisão editorial e post 5/5 | P | F5-04 |
| F5-06 | Relatório final e pendências | P | F5-05 |
| F5-07 | Conferência de memória e encerramento | P | F5-06 |

### F5-01 — Configuração e segurança

- **Entrada:** F4-07 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** .env.example, .gitignore, docker-compose.yml, docs/evidence/F5-01.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Revisar segredos, licença, usuário de container, volumes e exposição de portas; corrigir achados pequenos por responsabilidade.
- **Aceite:** Downloads fora do Git, nenhuma credencial real, serviço local e permissões justificadas; registrar limitações da auditoria.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-01.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-02 — Suíte final e reprodutibilidade

- **Entrada:** F5-01 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/evidence/F5-02.md, Makefile, .github/workflows/ci.yml. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Executar lint, tipos, unitários, contratos, integração e E2E; preparar workflow somente local; medir cobertura e baseline.
- **Aceite:** Instalação limpa funciona; resultados PASSOU/FALHOU/NÃO EXECUTADO por grupo; workflow remoto NÃO EXECUTADO enquanto sem autorização GitHub.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-02.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-03 — README, arquitetura e runbook finais

- **Entrada:** F5-02 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** README.md, docs/architecture.md, docs/runbook.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Consolidar setup/up/test/lint/run-sdp/down realmente testados, diagramas de contexto/componentes/fluxo e recuperação.
- **Aceite:** Outra execução segue quickstart; comandos destrutivos separados e não executados automaticamente; links e catálogo coerentes.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-03.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-04 — Portal Sphinx

- **Entrada:** F5-03 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/conf.py, docs/index.rst, docs/requirements-documentation.txt, docs/learning-notes.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Montar documentação oficial após código/testes; integrar contratos, ADRs, API/docstrings e aprendizado.
- **Aceite:** Build Sphinx com -W --keep-going passa; links locais e docstrings públicas verificados; dependências fixadas.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-04.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-05 — Revisão editorial e post 5/5

- **Entrada:** F5-04 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/linkedin/01.md a 05.md, docs/linkedin/carrossel.md, docs/demo.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Revisar cinco posts, carrossel de cinco slides e roteiro de vídeo de 30–60s.
- **Aceite:** 600–1400 caracteres aproximados por post, CTA/hashtags e evidências; placeholders não comprovados removidos ou mantidos como pendência; nenhum material publicado.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-05.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-06 — Relatório final e pendências

- **Entrada:** F5-05 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/evidence/final.md, CHANGELOG.md, docs/plan.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Consolidar aceite MVP, limitações científicas/operacionais, testes, custos medidos e extensões.
- **Aceite:** Cada requisito aponta evidência; gate incompleto explicitamente pendente; revisão independente de PR só após futura autorização e código finalizado.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-06.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.

### F5-07 — Conferência de memória e encerramento

- **Entrada:** F5-06 validadas e documentos pertinentes do plano.
- **Caminhos previstos:** docs/evidence/F5-07.md. Testes e relatório da própria tarefa são permitidos.
- **Entrega:** Verificar preferências explícitas no Jota; sincronização ampla dos dados do projeto somente se solicitada.
- **Aceite:** Preferências relidas; nenhuma alegação de sincronização sem prova; relatório distingue concluído localmente de publicado.
- **Validação:** executar teste focado correspondente, lint/tipos dos módulos alterados e registrar comando real em `docs/evidence/F5-07.md`; tarefas documentais validam links e consistência.
- **Limite:** não implementar a tarefa seguinte nem mudar o contrato sem registrar a decisão.
