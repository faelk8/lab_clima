# Guia de execução — Luna 6 médio

[Plano](../plan.md) · [Backlog](backlog.md)

## Despacho de uma tarefa

```text
Execute somente <ID> do docs/planning/backlog.md.
Modelo de desenvolvimento: gpt-6-luna; esforço médio.
Leia docs/plan.md, a tarefa, os contratos aplicáveis e os relatórios das dependências.
Confira se a fase foi autorizada e se as dependências foram validadas localmente.
Implemente somente a entrega descrita, nos caminhos previstos.
Execute os testes da própria tarefa e as regressões afetadas.
Registre docs/evidence/<ID>.md e atualize o estado da tarefa no backlog.
Não crie Issues, commits, PRs, push ou publicação sem autorização posterior.
Se houver ambiguidade de contrato ou incompatibilidade, registre a reprodução e pare.
Não avance de fase sozinho.
```

O nome do modelo no documento especifica o executor pretendido; não prova a configuração da sessão. Conferir o modelo efetivamente selecionado antes de iniciar. Não escolher outro automaticamente se estiver indisponível.

## Comandos planejados de validação

Estes comandos **não foram executados no projeto** e só se tornam operacionais depois das tarefas de configuração. O relatório deve registrar os comandos efetivamente implementados, inclusive eventuais ajustes de CLI exigidos pela versão validada.

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest tests/unit tests/contracts
uv run pytest tests/integration
uv run pytest tests/e2e
spark-pipelines dry-run --spec spark-pipeline.yml
spark-pipelines run --spec spark-pipeline.yml
sphinx-build -W --keep-going -b html docs docs/_build/html
```

Spark executa no container validado; não presumir instalação no host. Configurar testes online com marcador/flag opt-in na F1-09 para não misturá-los com a suíte offline. Um `dry-run` bem-sucedido não substitui leitura das tabelas após `run`.

## Relatório por tarefa

```markdown
# <ID> — <título>
Estado: VALIDADA LOCALMENTE | BLOQUEADA | EM EXECUÇÃO
Modelo/esforço efetivamente usados:
Dependências e evidências consultadas:
Arquivos alterados:
Decisões e desvios do plano:

| Critério | Comando/inspeção | Resultado | Evidência |
|---|---|---|---|
| ... | comando exato | PASSOU/FALHOU/NÃO EXECUTADO | trecho/caminho |

Dados: origem, intervalo, tamanho e hash quando aplicável.
Falhas, verificações omitidas e justificativas:
Conferência do coordenador:
Próximo passo permitido:
```

Não escrever PASSOU por inspeção quando o critério exige execução. Se a conexão falhar, registrar NÃO EXECUTADO ou FALHOU conforme o teste, preservar fixtures e não declarar o aceite online.

## Fechamento da fase

Conferir todas as tarefas e seus relatórios; atualizar plano, CHANGELOG e notas de aprendizado; informar arquivos, decisões, testes, métricas com fonte e pendências. Parar. Uma tarefa validada localmente não significa PR revisada nem publicação.

Quando GitHub for autorizado futuramente, retomar convenções de Issues/commits por responsabilidade e revisão independente da PR com código finalizado. Não disparar esse fluxo a partir deste guia enquanto vigorar a restrição local.
