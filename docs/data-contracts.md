# Contrato climático v1

A ingestão salva a resposta íntegra como raw com hash SHA-256 e manifesto contendo fonte, lote/localidade, parâmetros, horário UTC de coleta, tamanho e versão do coletor. Nunca gravar tokens ou segredos no manifesto.

A camada de domínio representa uma linha horária por `(location_id, measurement_time, source, model)`. `measurement_time` deve ser timezone-aware e normalizado para UTC na persistência analítica. Variáveis: temperatura em °C, precipitação em mm no intervalo horário indicado pela fonte, umidade em %, vento em km/h. `None` significa ausente, nunca zero. `quality_flags` identifica correções/rejeições. Contrato versionado por `contract_version`.

O parser inicial exige arrays temporais com mesmo comprimento e converte horas locais sem offset para UTC como convenção explícita do endpoint configurado com timezone. Essa escolha deve ser exercitada com fixtures de mudança de horário e revista se a API retornar offsets explícitos.

Invariantes: ID de local não vazio; hora com fuso; precipitação não negativa; umidade no intervalo 0–100; versão suportada. Campo solicitado ausente ou arrays divergentes causam erro explícito, sem truncamento silencioso; variáveis não solicitadas ficam como `None`. O chamador do parser informa explicitamente o subconjunto solicitado.

A precipitação horária é acumulada durante o intervalo da hora, não um valor instantâneo. Dia civil é definido pelo fuso da localidade. Não somar origens/modelos. Futuras correções preservam a versão raw e exigem replay. Contrato atual: `src/climatewatch/domain/weather.py`.

No SDP da Fase 3, `silver_observations` aplica o contrato horário e escolhe a revisão mais recente por `(location_id, observed_at_utc, source, model)`; `silver_rejected` preserva as flags das linhas inválidas. `gold_daily` agrega por local, fonte, modelo, fuso e data local. `gold_indicators` representa janelas temporais de 24 horas, com contagens de cobertura. Consulte [arquitetura](architecture.md) para schemas e consultas.
