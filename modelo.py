"""ELE637 - Pensamento Sistêmico em Engenharia.

Simulação discreta por sprint. O DEF apresenta quatro estoques; para contabilizar
corretamente as correções, o backlog é dividido internamente em duas parcelas.
Todos os números são hipóteses de simulação, não dados das empresas.
"""

import csv
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt

RESULTADOS = Path('resultados')
SPRINTS = 26
DEMANDA = 10.0                         # novas tarefas/sprint
CAPACIDADE_BASE = 12.0                # tarefas equivalentes/sprint
ATRASO_BUGS = 3                       # sprints
TAREFAS_POR_BUG = 1.0                 # tarefas/bug (hipótese)
META_BACKLOG = 12.0                   # tarefas


def limitar(valor, minimo=0.0, maximo=1.0):
    return min(maximo, max(minimo, valor))


# Mesmo sistema e mesma demanda nos cenários; mudam somente as políticas.
CENARIOS = {
    'Convencional': {'ia_inicial': 0.05, 'reacao_pressao': 0.10,
                     'validacao': 0.23, 'refatoracao': 0.10},
    'IA sob pressao': {'ia_inicial': 0.50, 'reacao_pressao': 0.40,
                       'validacao': 0.13, 'refatoracao': 0.035},
    'IA com qualidade': {'ia_inicial': 0.48, 'reacao_pressao': 0.15,
                         'validacao': 0.26, 'refatoracao': 0.14},
}


def simular(politica, sprints=SPRINTS, atraso=ATRASO_BUGS,
            taxa_bugs=0.36, taxa_divida=0.11, demanda=DEMANDA,
            efeito_ia_divida=0.38, contar_correcoes_metrica=False):
    """Simula uma equipe por sprints.

    efeito_ia_divida: hipótese de risco adicional quando a validação é insuficiente.
    Use 0 para testar a ausência desse efeito. Não é um parâmetro medido.
    contar_correcoes_metrica: False considera apenas novas funcionalidades no
    indicador gerencial; True considera toda tarefa concluída.
    """
    if atraso < 1 or int(atraso) != atraso:
        raise ValueError("O atraso deve ser um número inteiro de pelo menos 1 sprint.")
    if sprints < 1 or taxa_bugs < 0 or taxa_divida < 0 or demanda < 0 or efeito_ia_divida < 0:
        raise ValueError("Horizonte e parâmetros devem ser não negativos, com sprints >= 1.")
    tarefas_novas = 15.0                # parcela do backlog [tarefas]
    tarefas_correcao = 0.0              # parcela do backlog [tarefas]
    divida = 2.0                        # unidades abstratas de dívida [UDT]
    conhecimento = 0.85                 # índice [0, 1]
    bugs_ocultos = deque([0.0] * atraso)  # cada célula representa uma coorte
    entregas_anteriores = CAPACIDADE_BASE  # inicialização neutra das métricas
    historico_ia = deque([politica['ia_inicial']] * 2, maxlen=2)
    linhas = []

    for sprint in range(sprints + 1):
        backlog = tarefas_novas + tarefas_correcao
        # Indicador da liderança: volume de entregas, não qualidade do software.
        # Por padrão, exclui correções para não premiar retrabalho na métrica.
        produtividade_medida = entregas_anteriores / CAPACIDADE_BASE
        dependencia = limitar(sum(historico_ia) / len(historico_ia) *
                              (0.20 + 0.80 * (1.0 - conhecimento)))
        dificuldade = 1.0 + 0.024 * divida + 0.55 * (1 - conhecimento) + 0.35 * dependencia
        tempo_relativo = dificuldade  # índice: tempo por tarefa / tempo de referência
        pressao = limitar(0.48 * max(0, (backlog - META_BACKLOG) / 24.0) +
                          0.30 * max(0, tempo_relativo - 1.0) +
                          0.22 * max(0, produtividade_medida - 1.0))
        uso_ia = limitar(politica['ia_inicial'] + politica['reacao_pressao'] * pressao)
        # A pressão pode deslocar capacidade antes reservada à validação/refatoração.
        parcela_testes = limitar(politica['validacao'] * (1.0 - 0.55 * pressao), 0.02, 0.35)
        parcela_refatoracao = limitar(politica['refatoracao'] * (1.0 - 0.70 * pressao), 0.005, 0.25)
        cobertura_testes = limitar(0.15 + 2.5 * parcela_testes, 0.10, 0.95)

        linhas.append({
            'sprint': sprint, 'backlog': backlog,
            'tarefas_novas_pendentes': tarefas_novas,
            'tarefas_correcao_pendentes': tarefas_correcao,
            'bugs_ocultos': sum(bugs_ocultos), 'divida': divida,
            'conhecimento': conhecimento, 'pressao': pressao,
            'uso_ia': uso_ia, 'dependencia_ia': dependencia,
            'cobertura_testes': cobertura_testes,
            'produtividade_medida': produtividade_medida,
            'tarefas_contadas_na_metrica': entregas_anteriores,
            'dificuldade_manutencao': dificuldade,
            'entregas': 0.0, 'entregas_novas': 0.0,
            'correcoes': 0.0, 'bugs_identificados': 0.0,
            'geracao_bugs': 0.0, 'acumulo_divida': 0.0,
            'refatoracao': 0.0,
        })
        if sprint == sprints:
            break

        # Bugs escapam da validação e aparecem apenas após o atraso.
        bugs_identificados = bugs_ocultos.popleft()
        correcoes_disponiveis = tarefas_correcao + TAREFAS_POR_BUG * bugs_identificados
        novas_disponiveis = tarefas_novas + demanda

        # A refatoração e os testes consomem capacidade da mesma equipe.
        capacidade_entregas = max(0.0, CAPACIDADE_BASE * (1.0 + 0.70 * uso_ia) *
                                  (1.0 - parcela_testes - parcela_refatoracao) / dificuldade)
        correcoes = min(correcoes_disponiveis, capacidade_entregas * 0.50)
        entregas_novas = min(novas_disponiveis, capacidade_entregas - correcoes)
        # Aproveita capacidade restante em correções, se não houver novas tarefas.
        correcoes += min(correcoes_disponiveis - correcoes,
                         max(0.0, capacidade_entregas - correcoes - entregas_novas))
        entregas = entregas_novas + correcoes

        # A geração de bugs e de dívida ocorre com novas funcionalidades;
        # a IA não é causa direta: seu efeito de risco é condicionado à validação.
        geracao_bugs = taxa_bugs * entregas_novas * (1.0 - cobertura_testes)
        divida_por_tarefa = (taxa_divida + 0.55 * pressao * (1.0 - cobertura_testes)
                             + efeito_ia_divida * uso_ia * (1.0 - cobertura_testes))
        acumulo_divida = entregas_novas * divida_por_tarefa  # UDT/sprint
        refatoracao = min(divida, 1.2 * CAPACIDADE_BASE * parcela_refatoracao)  # UDT/sprint

        # Aprendizado/perda são variações de um índice normalizado por sprint.
        aprendizado = 0.09 * cobertura_testes * (1.0 - conhecimento)
        perda_conhecimento = 0.055 * dependencia * (1.0 - cobertura_testes) * conhecimento

        tarefas_novas = max(0.0, novas_disponiveis - entregas_novas)
        tarefas_correcao = max(0.0, correcoes_disponiveis - correcoes)
        divida = max(0.0, divida + acumulo_divida - refatoracao)
        conhecimento = limitar(conhecimento + aprendizado - perda_conhecimento)
        bugs_ocultos.append(geracao_bugs)
        entregas_anteriores = entregas if contar_correcoes_metrica else entregas_novas
        historico_ia.append(uso_ia)
        linhas[-1].update(entregas=entregas, entregas_novas=entregas_novas,
                          correcoes=correcoes, bugs_identificados=bugs_identificados,
                          geracao_bugs=geracao_bugs, acumulo_divida=acumulo_divida,
                          refatoracao=refatoracao)
        # Conservação de tarefas: backlog(t+1) = backlog(t) + entradas - saídas.
        proximo_backlog = tarefas_novas + tarefas_correcao
        esperado = backlog + demanda + TAREFAS_POR_BUG * bugs_identificados - entregas
        assert abs(proximo_backlog - esperado) < 1e-8
        assert 0.0 <= conhecimento <= 1.0
        assert min(tarefas_novas, tarefas_correcao, divida) >= 0
    return linhas


def exportar_csv(caminho, linhas):
    with open(caminho, 'w', newline='', encoding='utf-8-sig') as arq:
        escritor = csv.DictWriter(arq, fieldnames=linhas[0].keys())
        escritor.writeheader()
        escritor.writerows(linhas)


def gerar_figuras(simulacoes):
    for nome, coluna, unidade in [
        ('backlog', 'backlog', 'tarefas'),
        ('divida_tecnica', 'divida', 'UDT'),
        ('bugs_ocultos', 'bugs_ocultos', 'bugs'),
        ('know_how', 'conhecimento', 'índice [0,1]'),
        ('entregas', 'entregas', 'tarefas/sprint')
    ]:
        fig, ax = plt.subplots(figsize=(9, 4.5))
        for cenario, linhas in simulacoes.items():
            pontos = linhas[:-1] if nome == 'entregas' else linhas
            ax.plot([l['sprint'] for l in pontos], [l[coluna] for l in pontos], label=cenario)
        ax.set(xlabel='Sprint', ylabel=unidade, title=nome.replace('_', ' ').capitalize())
        ax.legend()
        ax.grid(alpha=0.2)
        fig.tight_layout()
        fig.savefig(RESULTADOS / f'{nome}.png', dpi=170)
        plt.close(fig)


def verificar_extremos():
    # Sem bugs, não há entrada de tarefas de correção.
    for atraso in (1, 3, 6):
        dados = simular(CENARIOS['IA sob pressao'], sprints=26, atraso=atraso,
                        taxa_bugs=0.0)
        assert all(l['geracao_bugs'] == 0.0 for l in dados)
        assert all(l['tarefas_correcao_pendentes'] == 0.0 for l in dados)
    # Sem demanda e sem defeitos, o backlog não pode aumentar.
    sem_entradas = simular(CENARIOS['Convencional'], sprints=15,
                           demanda=0, taxa_bugs=0)
    assert all(sem_entradas[i+1]['backlog'] <= sem_entradas[i]['backlog'] + 1e-8
               for i in range(len(sem_entradas)-1))
    # Sensibilidade: atraso, geração de bugs e efeito hipotético da IA na dívida.
    linhas = []
    for atraso in (1, 3, 6):
        for taxa in (0.18, 0.36, 0.54):
            dados = simular(CENARIOS['IA sob pressao'], atraso=atraso, taxa_bugs=taxa)
            linhas.append({'atraso_sprints': atraso, 'taxa_bugs': taxa,
                           'backlog_final': dados[-1]['backlog'],
                           'divida_final': dados[-1]['divida']})
    exportar_csv(RESULTADOS / 'sensibilidade.csv', linhas)
    efeito_linhas = []
    for cenario, politica in CENARIOS.items():
        for efeito in (0.0, 0.19, 0.38):
            for contar_correcoes in (False, True):
                dados = simular(politica, efeito_ia_divida=efeito,
                                contar_correcoes_metrica=contar_correcoes)
                efeito_linhas.append({
                    'cenario': cenario, 'efeito_ia_divida': efeito,
                    'inclui_correcoes_na_metrica': contar_correcoes,
                    'backlog_final': dados[-1]['backlog'],
                    'divida_final': dados[-1]['divida'],
                    'conhecimento_final': dados[-1]['conhecimento']})
    exportar_csv(RESULTADOS / 'sensibilidade_ia_e_metrica.csv', efeito_linhas)


def investigar_equilibrio():
    """Busca estabilidade aproximada nas últimas 10 sprints de um horizonte longo.

    Não encontrar equilíbrio neste teste não prova sua inexistência.
    """
    linhas = []
    for nome, politica in CENARIOS.items():
        dados = simular(politica, sprints=160)
        variaveis = ('backlog', 'divida', 'conhecimento', 'bugs_ocultos')
        variacoes = {k: abs(dados[-1][k] - dados[-11][k]) / 10.0 for k in variaveis}
        linhas.append({'cenario': nome, **{f'variacao_{k}_por_sprint': v
                                          for k, v in variacoes.items()},
                       'equilibrio_aproximado': all(v < 0.01 for v in variacoes.values())})
    exportar_csv(RESULTADOS / 'equilibrios_aproximados.csv', linhas)


def main():
    RESULTADOS.mkdir(exist_ok=True)
    simulacoes = {nome: simular(politica) for nome, politica in CENARIOS.items()}
    for nome, linhas in simulacoes.items():
        exportar_csv(RESULTADOS / f"{nome.lower().replace(' ', '_')}.csv", linhas)
    gerar_figuras(simulacoes)
    verificar_extremos()
    investigar_equilibrio()
    print('Cenário                    Backlog    Dívida (UDT)    Know-how')
    for nome, linhas in simulacoes.items():
        ult = linhas[-1]
        print(f"{nome:25} {ult['backlog']:8.2f} {ult['divida']:13.2f} {ult['conhecimento']:10.3f}")
    print(f'Arquivos gerados em: {RESULTADOS.resolve()}')


if __name__ == '__main__':
    main()
