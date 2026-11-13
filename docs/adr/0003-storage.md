# ADR 0003 — persistência local inicial

Estado: proposta implementada em 13/11/2026.

O MVP guarda cada resposta HTTP como JSON bruto em caminho endereçado por SHA-256, com sidecar JSON de proveniência e escrita atômica no filesystem local. O catálogo/warehouse do SDP fica em volume local/temporário durante a prova. Não há banco de negócio, objeto cloud ou garantia transacional entre raw e sidecar.

Isso permite reprocessar bytes originais e detectar conteúdo repetido sem introduzir serviço adicional. Depois, a Fase 2 adicionará manifesto de lote e recuperação entre arquivos.
