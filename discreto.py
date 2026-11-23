import matplotlib.pyplot as plt

# ==============================================================================
# 1. PARÂMETROS (constantes no topo para facilitar testes e sensibilidade)
# ==============================================================================
DEMANDA = 10.0            # novas funcionalidades / sprint (fronteira)
CAPACIDADE_BASE = 10.0    # tarefas / sprint (sem IA, sem dívida, know-how 100%)
META_BACKLOG = 10.0       # backlog saudável [tarefas]
ATRASO_BUGS = 3           # sprints até os bugs ocultos serem identificados
HORIZONTE = 26            # sprints (~1 ano)

# Pesos das relações auxiliares e fluxos
GANHO_IA = 0.65           # aumento máximo de velocidade com uso_ia = 1
IMPACTO_DIVIDA = 0.03     # quanto cada unid. de dívida aumenta a dif. manutenção
IMPACTO_KNOWHOW = 0.60    # quanto a falta de know-how aumenta a dif. manutenção
TAXA_DIVIDA_IA = 0.30     # unid. de dívida geradas por entrega via IA
TAXA_DIVIDA_PRESSAO = 0.15# unid. de dívida geradas por atalhos sob pressão
TAXA_REFATORACAO = 0.04   # fração da dívida limpa por sprint [1/sprint]
TAXA_BUGS = 0.28          # bugs gerados por entrega sem cobertura de testes
TAXA_APRENDIZADO = 0.04   # ganho de know-how trabalhando sem IA [1/sprint]
TAXA_PERDA_KH = 0.08      # erosão de know-how por dependência de IA [1/sprint]


# ==============================================================================
# 2. ESTADO INICIAL (os 4 estoques do DEF + memória das métricas)
# ==============================================================================
def initialize():
    global backlog, divida, know_how, fila_bugs, ultimas_entregas
    global hist_backlog, hist_bugs_ocultos, hist_divida, hist_know_how
    global hist_entregas, hist_uso_ia, hist_testes

    # Estoques iniciais
    backlog = 15.0                   # [tarefas]
    divida = 2.0                     # [unid.]
    know_how = 0.85                  # [0-1]
    fila_bugs = [0.0] * ATRASO_BUGS  # estoque de bugs ocultos [bugs]
    ultimas_entregas = CAPACIDADE_BASE  # referência inicial para R1

    # Séries temporais para gráficos
    hist_backlog = [backlog]
    hist_bugs_ocultos = [sum(fila_bugs)]
    hist_divida = [divida]
    hist_know_how = [know_how]
    hist_entregas = [ultimas_entregas]
    hist_uso_ia = [0.2]
    hist_testes = [0.85]


# ==============================================================================
# 3. REGISTRO DOS DADOS
# ==============================================================================
def observe(entregas_t, uso_ia_t, testes_t):
    hist_backlog.append(backlog)
    hist_bugs_ocultos.append(sum(fila_bugs))
    hist_divida.append(divida)
    hist_know_how.append(know_how)
    hist_entregas.append(entregas_t)
    hist_uso_ia.append(uso_ia_t)
    hist_testes.append(testes_t)


# ==============================================================================
# 4. REGRA DE UM PASSO (atualização simultânea de estoques e fluxos)
# ==============================================================================
def update():
    global backlog, divida, know_how, fila_bugs, ultimas_entregas

    # --- AUXILIARES (calculados a partir do estado ANTIGO) ---
    # R4 e R5: dívida (+) e know-how (-) definem dificuldade e tempo por tarefa
    dificuldade_manut = 1.0 + IMPACTO_DIVIDA * divida + IMPACTO_KNOWHOW * (1.0 - know_how)
    tempo_tarefas = dificuldade_manut  # 1.0 = tempo nominal

    # R1: entregas acima da linha de base elevam as métricas/expectativas
    metricas_eficiencia = max(0.0, (ultimas_entregas - CAPACIDADE_BASE) / CAPACIDADE_BASE)

    # Pressão da liderança: backlog (+), tempo das tarefas (+) e métricas (+)
    pressao = min(1.0, max(0.0,
        0.50 * max(0.0, (backlog - META_BACKLOG) / 20.0)
        + 0.35 * max(0.0, tempo_tarefas - 1.0)
        + 0.50 * metricas_eficiencia
    ))

    # Reações do time sob pressão
    uso_ia = min(1.0, 0.20 + 0.60 * pressao + 0.25 * (1.0 - know_how))
    dependencia_ia = min(1.0, 0.50 * uso_ia + 0.50 * (1.0 - know_how))
    cobertura_testes = max(0.15, 0.90 - 0.65 * pressao)

    # --- FLUXOS (taxas por sprint) ---
    # B1: IA acelera (+), tempo das tarefas freia (-)
    fator_ia = 1.0 + GANHO_IA * uso_ia
    entregas = min(backlog, CAPACIDADE_BASE * fator_ia / tempo_tarefas)

    # Fluxos da Dívida Técnica
    acumulo_divida = (TAXA_DIVIDA_IA * uso_ia + TAXA_DIVIDA_PRESSAO * pressao) * entregas
    refatoracao = TAXA_REFATORACAO * divida

    # Fluxos de Bugs (R2 + atraso)
    geracao_bugs = TAXA_BUGS * (1.0 - cobertura_testes) * entregas
    bugs_identificados = fila_bugs[0]  # sai o mais antigo da fila

    # Fluxos de Know-how (R3)
    aprendizado = TAXA_APRENDIZADO * (1.0 - uso_ia)
    perda_know_how = TAXA_PERDA_KH * dependencia_ia

    # --- PRÓXIMOS ESTOQUES (calculados antes de sobrescrever) ---
    prox_backlog = max(0.0, backlog + DEMANDA + bugs_identificados - entregas)
    prox_divida = max(0.0, divida + acumulo_divida - refatoracao)
    prox_know_how = min(1.0, max(0.10, know_how + aprendizado - perda_know_how))
    prox_fila_bugs = fila_bugs[1:] + [geracao_bugs]

    # Atualização simultânea
    backlog, divida, know_how = prox_backlog, prox_divida, prox_know_how
    fila_bugs = prox_fila_bugs
    ultimas_entregas = entregas

    return entregas, uso_ia, cobertura_testes


# ==============================================================================
# 5. SIMULAÇÃO E GRÁFICOS
# ==============================================================================
if __name__ == "__main__":
    initialize()
    for t in range(HORIZONTE):
        entregas_t, uso_ia_t, testes_t = update()
        observe(entregas_t, uso_ia_t, testes_t)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)

    # Painel 1: Estoques de trabalho e dívida
    ax1.plot(hist_backlog, label="Backlog [tarefas]")
    ax1.plot(hist_divida, label="Dívida Técnica [unid.]")
    ax1.plot(hist_bugs_ocultos, label="Bugs Ocultos [bugs]", linestyle="--")
    ax1.set_ylabel("Estoques")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Painel 2: Know-how e variáveis comportamentais (0 a 1)
    ax2.plot(hist_know_how, label="Know-how [0-1]", color="purple")
    ax2.plot(hist_uso_ia, label="Uso de IA [0-1]", color="orange")
    ax2.plot(hist_testes, label="Cobertura de Testes [0-1]", color="teal")
    ax2.set_ylabel("Índices [0-1]")
    ax2.set_ylim(0, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Painel 3: Entregas vs Demanda
    ax3.plot(hist_entregas, label="Entregas [tarefas/sprint]", color="green")
    ax3.axhline(DEMANDA, color="red", linestyle=":", label="Demanda externa")
    ax3.set_xlabel("Tempo (sprints)")
    ax3.set_ylabel("Fluxo")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()