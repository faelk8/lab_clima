# ADR 0004 — semântica temporal v1

Estado: proposta para MVP.

A API consulta em timezone IANA da localidade para preservar limites de dia civil; contrato guarda instante timezone-aware e consumidores devem normalizar a chave para UTC, mantendo fuso original para agregação local. Precipitação representa acumulação horária. Intervalos de hora não devem ser tratados como observações instantâneas. Fixtures existentes cruzam meia-noite; casos de DST e horas ausentes ficam para validação de Fase 3.
