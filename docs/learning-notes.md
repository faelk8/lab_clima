# Notas de aprendizado — ClimateWatch

[Plano](plan.md) · [Backlog](planning/backlog.md)

## Fase 0 — Planejamento

Estado: estudo documental, sem execução Spark. O problema é ingestão de intervalos históricos por API: batch incremental é a hipótese inicial adequada. Reanálise de modelo não é observação direta de estação, e uma série curta não demonstra mudança climática.

SDP descreve datasets e dependências para o engine organizar a execução. Structured Streaming é a API de processamento incremental contínuo/microbatch; não é sinônimo de Kafka nem substituto automático de SDP. As definições SDP devem descrever transformação, enquanto coleta HTTP e seus efeitos ficam fora delas. Referência: [guia oficial SDP](https://spark.apache.org/docs/latest/declarative-pipelines-programming-guide.html).

### Exercício mínimo proposto (não executado)

Na F1-02, usar três registros sintéticos conhecidos e uma transformação simples: filtrar valor nulo e somar os demais. Declarar uma materialized view, analisar com dry-run, executar com run e ler o resultado persistido. Na F3-08, escrever a mesma transformação em DataFrame imperativo e comparar onde leitura, dependências e escrita são controladas. Discutir o que mudaria se chegassem novos arquivos continuamente; não instalar Kafka para demonstrar essa diferença.

Resultado esperado é calculado manualmente a partir da fixture escolhida, não presumido como obtido. O exercício só estará concluído quando comandos, versões e saída estiverem no relatório.

## Roteiro por fase

| Fase | Conceitos | Experimento controlado |
|---|---|---|
| 1 | Proveniência, unidades, contratos e limites da API | Resposta válida versus arrays desalinhados |
| 2 | Cache, idempotência, falha e retomada | Interromper após raw e antes do manifesto |
| 3 | Medallion, dedupe, UTC/dia local, dados tardios | Repetir lote e corrigir uma hora histórica |
| 4 | Cobertura, interpretação e transparência | Janela incompleta não pode disparar conclusão segura |
| 5 | Reprodutibilidade, documentação e comunicação | Reproduzir quickstart com fixture e conferir afirmações dos posts |

Adicionar resultados reais somente após cada execução. Para cada experimento: hipótese, entrada, comando, saída, falha observada e trade-off aprendido.
