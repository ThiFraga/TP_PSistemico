import matplotlib.pyplot as plt

# 1. PARÂMETROS (constantes com unidade)
DEMANDA = 10.0          # novas funcionalidades / sprint
CAPACIDADE_BASE = 10.0  # tarefas / sprint (time sem IA e sem dívida)
META_BACKLOG = 10.0     # backlog considerado saudável (tarefas)
ATRASO_BUGS = 3         # sprints (~1,5 mês) até os bugs aparecerem
HORIZONTE = 26          # sprints (~1 ano)

# 2. ESTADO INICIAL
def initialize():
    global backlog, divida, know_how, fila_bugs
    global hist_backlog, hist_divida, hist_entregas, hist_know_how

    backlog = 15.0      # tarefas acumuladas no início
    divida = 2.0        # dívida técnica inicial (unidades de dívida)
    know_how = 0.85     # domínio do código (0 a 1)
    fila_bugs = [0.0] * ATRASO_BUGS  # memória do atraso

    hist_backlog = [backlog]
    hist_divida = [divida]
    hist_entregas = [0.0]
    hist_know_how = [know_how]

# 3. REGISTRO DOS DADOS
def observe(entregas_passo):
    hist_backlog.append(backlog)
    hist_divida.append(divida)
    hist_entregas.append(entregas_passo)
    hist_know_how.append(know_how)

# 4. REGRA DE UM PASSO (atualização simultânea)
def update():
    global backlog, divida, know_how, fila_bugs

    # Auxiliares (regras de decisão do time)
    pressao = min(1.0, max(0.0, (backlog - META_BACKLOG) / 20.0))
    uso_ia = min(1.0, 0.2 + 0.5 * pressao + 0.3 * (1.0 - know_how))
    cobertura_testes = max(0.1, 0.9 - 0.6 * pressao)

    # Efeito da IA (acelera) vs. Dívida Técnica (freia manutenção)
    fator_ia = 1.0 + 0.5 * uso_ia
    fator_divida = 1.0 / (1.0 + 0.03 * divida)

    # Fluxos calculados a partir do estado ANTIGO
    entregas = min(backlog, CAPACIDADE_BASE * fator_ia * fator_divida)
    nova_divida = 0.35 * uso_ia * entregas
    refatoracao = 0.04 * divida
    bugs_gerados = (0.03 * divida) + (0.25 * (1.0 - cobertura_testes) * entregas)

    # Atraso: sai o bug mais antigo, entra o recém-gerado
    bugs_descobertos = fila_bugs[0]
    fila_bugs = fila_bugs[1:] + [bugs_gerados]

    # Próximos estoques (antes de sobrescrever)
    prox_backlog = max(0.0, backlog + DEMANDA + bugs_descobertos - entregas)
    prox_divida = max(0.0, divida + nova_divida - refatoracao)
    prox_know_how = min(1.0, max(0.1, know_how + 0.04 * (1.0 - uso_ia) - 0.07 * uso_ia))

    # Atualiza tudo junto
    backlog, divida, know_how = prox_backlog, prox_divida, prox_know_how
    return entregas

# 5. SIMULAÇÃO E GRÁFICOS

if __name__ == "__main__":
    initialize()
    for t in range(HORIZONTE):
        entregas_t = update()
        observe(entregas_t)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax1.plot(hist_backlog, label="Backlog (tarefas)")
    ax1.plot(hist_divida, label="Dívida Técnica")
    ax1.set_ylabel("Estoques")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(hist_entregas[1:], label="Entregas / sprint", color="green")
    ax2.set_xlabel("Tempo (sprints)")
    ax2.set_ylabel("Entregas")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()