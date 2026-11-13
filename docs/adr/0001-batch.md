# ADR 0001 — ingestão batch sem Kafka

Estado: decisão aplicada na Fase 2, 13/11/2026.

A fonte primária oferece consultas históricas por intervalo e não emite eventos de domínio contínuos. O MVP divide datas em janelas fechadas e reprocessáveis, registra cada request e preserva respostas raw versionadas. Kafka adicionaria brokers, conectores, schemas de evento e operação sem requisito atual de baixa latência. Uma mudança para streaming exige caso de uso com event time/replay e ADR revisado.

Janela padrão: até sete dias, orçamento de 30 requests por execução incluindo retries. A configuração pode ser reduzida; nunca há loop contínuo. Reprocessar um intervalo não duplica arquivo de conteúdo igual; correções da fonte geram versão nova.
