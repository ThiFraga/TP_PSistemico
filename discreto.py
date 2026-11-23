import os
import csv
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

PASTA_RESULTADOS = "resultados"
NOME_CENARIO = "cenario_base"


# ==============================================================================
# 2. ESTADO INICIAL (os 4 estoques do DEF + memória das métricas)
# ==============================================================================
def initialize():
    global backlog, divida, know_how, fila_bugs, ultimas_entregas
    global hist_backlog, hist_bugs_ocultos, hist_divida, hist_know_how
    global hist_entregas, hist_uso_ia, hist_testes

    backlog = 15.0                      # [tarefas]
    divida = 2.0                        # [unid.]
    know_how = 0.85                     # [0-1]
    fila_bugs = [0.0] * ATRASO_BUGS     # estoque de bugs ocultos [bugs]
    ultimas_entregas = CAPACIDADE_BASE  # referência inicial para R1

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

    # Auxiliares (calculados a partir do estado ANTIGO)
    dificuldade_manut = 1.0 + IMPACTO_DIVIDA * divida + IMPACTO_KNOWHOW * (1.0 - know_how)
    tempo_tarefas = dificuldade_manut

    metricas_eficiencia = max(0.0, (ultimas_entregas - CAPACIDADE_BASE) / CAPACIDADE_BASE)

    pressao = min(1.0, max(0.0,
        0.50 * max(0.0, (backlog - META_BACKLOG) / 20.0)
        + 0.35 * max(0.0, tempo_tarefas - 1.0)
        + 0.50 * metricas_eficiencia
    ))

    uso_ia = min(1.0, 0.20 + 0.60 * pressao + 0.25 * (1.0 - know_how))
    dependencia_ia = min(1.0, 0.50 * uso_ia + 0.50 * (1.0 - know_how))
    cobertura_testes = max(0.15, 0.90 - 0.65 * pressao)

    # Fluxos (taxas por sprint)
    fator_ia = 1.0 + GANHO_IA * uso_ia
    entregas = min(backlog, CAPACIDADE_BASE * fator_ia / tempo_tarefas)

    acumulo_divida = (TAXA_DIVIDA_IA * uso_ia + TAXA_DIVIDA_PRESSAO * pressao) * entregas
    refatoracao = TAXA_REFATORACAO * divida

    geracao_bugs = TAXA_BUGS * (1.0 - cobertura_testes) * entregas
    bugs_identificados = fila_bugs[0]

    aprendizado = TAXA_APRENDIZADO * (1.0 - uso_ia)
    perda_know_how = TAXA_PERDA_KH * dependencia_ia

    # Próximos estoques (calculados antes de sobrescrever)
    prox_backlog = max(0.0, backlog + DEMANDA + bugs_identificados - entregas)
    prox_divida = max(0.0, divida + acumulo_divida - refatoracao)
    prox_know_how = min(1.0, max(0.10, know_how + aprendizado - perda_know_how))
    prox_fila_bugs = fila_bugs[1:] + [geracao_bugs]

    backlog, divida, know_how = prox_backlog, prox_divida, prox_know_how
    fila_bugs = prox_fila_bugs
    ultimas_entregas = entregas

    return entregas, uso_ia, cobertura_testes


# ==============================================================================
# 5. EXPORTAÇÃO DOS ESTADOS E GRÁFICO
# ==============================================================================
def salvar_estados(caminho_csv):
    with open(caminho_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "sprint",
            "backlog",
            "divida_tecnica",
            "bugs_ocultos",
            "know_how",
            "uso_ia",
            "cobertura_testes",
            "entregas"
        ])
        for t in range(len(hist_backlog)):
            writer.writerow([
                t,
                round(hist_backlog[t], 4),
                round(hist_divida[t], 4),
                round(hist_bugs_ocultos[t], 4),
                round(hist_know_how[t], 4),
                round(hist_uso_ia[t], 4),
                round(hist_testes[t], 4),
                round(hist_entregas[t], 4),
            ])


def salvar_grafico(caminho_png):
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(9, 8), sharex=True)

    ax1.plot(hist_backlog, label="Backlog [tarefas]")
    ax1.plot(hist_divida, label="Dívida Técnica [unid.]")
    ax1.plot(hist_bugs_ocultos, label="Bugs Ocultos [bugs]", linestyle="--")
    ax1.set_ylabel("Estoques")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.plot(hist_know_how, label="Know-how [0-1]", color="purple")
    ax2.plot(hist_uso_ia, label="Uso de IA [0-1]", color="orange")
    ax2.plot(hist_testes, label="Cobertura de Testes [0-1]", color="teal")
    ax2.set_ylabel("Índices [0-1]")
    ax2.set_ylim(0, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    ax3.plot(hist_entregas, label="Entregas [tarefas/sprint]", color="green")
    ax3.axhline(DEMANDA, color="red", linestyle=":", label="Demanda externa")
    ax3.set_xlabel("Tempo (sprints)")
    ax3.set_ylabel("Fluxo")
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(caminho_png, dpi=300)
    plt.close(fig)  # troque por plt.show() se também quiser abrir a janela


# ==============================================================================
# 6. EXECUÇÃO
# ==============================================================================
if __name__ == "__main__":
    os.makedirs(PASTA_RESULTADOS, exist_ok=True)

    initialize()
    for t in range(HORIZONTE):
        entregas_t, uso_ia_t, testes_t = update()
        observe(entregas_t, uso_ia_t, testes_t)

    caminho_csv = os.path.join(PASTA_RESULTADOS, f"estados_{NOME_CENARIO}.csv")
    caminho_png = os.path.join(PASTA_RESULTADOS, f"grafico_{NOME_CENARIO}.png")

    salvar_estados(caminho_csv)
    salvar_grafico(caminho_png)

    print(f"Salvo com sucesso:\n- {caminho_png}\n- {caminho_csv}")