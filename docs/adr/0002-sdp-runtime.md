# ADR 0002 — runtime para prova Spark SDP

Estado: proposta testada parcialmente em 13/11/2026.

Escolha: PySpark 4.1.0 com extra `pipelines`, conforme guia oficial da mesma versão. Essa release introduz SDP e requer runtime Java suportado; a máquina tem Java 21. A dependência está travada em poetry.lock. A PoC separa a transformação declarativa de qualquer acesso HTTP.

Alternativa: Structured Streaming imperativo. Mantida para casos que exijam controle direto de query contínua; o MVP usa reprocessamento batch.

Validação: import, CLI, dry-run e run são registrados em `docs/evidence/F1-02.md`. O resultado somente é aceito se a tabela persistida puder ser consultada.
