# ADR 0004 — semântica temporal v1

Estado: adotada na Fase 3.

A API consulta em timezone IANA da localidade para preservar limites de dia civil; contrato guarda instante timezone-aware e consumidores devem normalizar a chave para UTC, mantendo fuso original para agregação local. Precipitação representa acumulação horária. Intervalos de hora não devem ser tratados como observações instantâneas. Fixtures existentes cruzam meia-noite; casos de DST e horas ausentes ficam para validação de Fase 3.

O SDP converte cada hora local em UTC na Silver, preserva o rótulo local e agrupa Gold por data civil local. `expected_hours` deriva da diferença entre duas meias-noites locais em UTC, permitindo 23, 24 ou 25 horas. A janela móvel de 24 horas usa segundos de tempo, não contagem de linhas; a última amostra cobre o intervalo fechado de 23 horas anteriores até a hora atual. O teste Silver cobre conversões DST e o teste de replay cobre cobertura de 24 horas e correção histórica.
