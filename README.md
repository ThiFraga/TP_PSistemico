# ELE637 — Pensamento Sistêmico em Engenharia

## Modelo discreto por sprint: IA, pressão por entregas e dívida técnica

Modelo **exploratório**, elaborado a partir dos relatos qualitativos anonimizados do grupo e do DLC/DEF. **Não são medições das empresas e não provam que IA cause dívida técnica.**

### Como executar

Com Python 3.10+ instalado:

```bash
python -m pip install -r requirements.txt
python modelo.py
```

Ou abra `ELE637_modelo.ipynb` no Google Colab e use **Executar tudo**. Não há chave de API nem necessidade de instalar Gemini.

Os CSVs e PNGs saem em `resultados/`, incluindo `sensibilidade.csv`, `sensibilidade_ia_e_metrica.csv` e `equilibrios_aproximados.csv`.

### Estoques do DEF

- **Backlog (tarefas)**: somatório interno de tarefas novas pendentes e tarefas de correção pendentes. Correções não são novas funcionalidades.
- **Bugs ocultos (bugs)**: fila de coortes de defeitos não descobertos; prazo padrão de 3 sprints.
- **Dívida técnica (UDT)**: índice de dívida em unidade abstrata, criado por implementação e reduzido por refatoração.
- **Conhecimento técnico (índice entre 0 e 1)**: indicador hipotético de compreensão sobre o código, não medida da competência de pessoas.

### Fluxos e dimensões

- Demanda externa: **tarefas/sprint**.
- Bugs identificados: **bugs/sprint**; entram no backlog após multiplicação por `TAREFAS_POR_BUG` (**tarefas/bug**).
- Entregas de novas funcionalidades e correções: **tarefas/sprint**, cada uma com fila específica.
- Geração de bugs: **bugs/sprint**, com atraso até a identificação.
- Acúmulo de dívida e refatoração: **UDT/sprint**.
- Aprendizado e perda de conhecimento: **unidade do índice/sprint**.

A capacidade equivale a tarefas por sprint e é partilhada entre entregas, correções, validação e refatoração. No código, as frações de validação e refatoração diminuem a capacidade de entregas; a refatoração diminui o estoque de dívida.

### Hipóteses e comparação

Três políticas: `Convencional`, `IA sob pressao` e `IA com qualidade`. A demanda externa e os valores iniciais dos estoques são iguais, mas as políticas alteram uso inicial de IA, reação à pressão, validação e refatoração. Os parâmetros são **ilustrativos**, sujeitos a revisão do grupo.

**Métrica gerencial de produtividade**: por padrão, usa somente as **entregas de novas funcionalidades da sprint anterior**, divididas pela capacidade de referência (12 tarefas/sprint), e influencia parcialmente a pressão de liderança. Isso evita premiar a correção de bugs como se fossem novas funcionalidades. Na análise de sensibilidade, `contar_correcoes_metrica=True` permite testar o critério alternativo, que conta toda tarefa concluída.

**IA e dívida**: o acréscimo hipotético `efeito_ia_divida * uso_ia * (1 - cobertura_testes)` entra no índice de geração de dívida por tarefa nova. Ele **não** implica dívida quando a validação é completa e pode ser desligado com `efeito_ia_divida=0`. A sensibilidade testa 0, 0.19 e 0.38, de modo a separar a relação assumida dos dados observados.

Equações simplificadas (valores por sprint):

```
backlog[t+1] = backlog[t] + demanda + tarefas_por_bug * bugs_identificados - novas_entregas - correcoes
bugs_ocultos[t+1] = bugs_ocultos[t] + bugs_nao_detectados - bugs_identificados
D[t+1] = max(0, D[t] + novas_entregas * divida_por_tarefa - refatoracao)
K[t+1] = limitar(K[t] + aprendizado - perda_conhecimento, 0, 1)
```

No modelo com atraso, `bugs_ocultos` é contabilizado como a soma das coortes; a identificação remove a coorte mais antiga. **Não** se deve somar os bugs descobertos às novas funcionalidades.

### Relações do DLC e como aparecem no código

- **B1:** backlog → pressão → intensidade de IA → entregas → redução do backlog.
- **R1:** entregas da sprint anterior → indicador de produtividade → pressão → uso de IA → entregas. É uma hipótese sobre metas crescentes, não uma regra de toda organização.
- **R2:** pressão → menos validação → bugs escapam → atraso de descoberta → tarefas de correção → backlog → pressão.
- **R3:** uso de IA e menor conhecimento → dependência (índice) → dificuldade de manutenção → maior tempo por tarefa → pressão. Uso e dependência não são sinônimos.
- **R4:** dívida técnica → dificuldade → maior tempo por tarefa → pressão → diminuição de validação/refatoração → dívida acumulada.
- **R5:** a relação entre conhecimento e manutenção se sobrepõe parcialmente a R3/R4. Está representada por funções auxiliares, não por um estoque extra.

Essas são **aproximações de mecanismos**, não uma prova de equivalência perfeita de todas as setas presentes nos arquivos draw.io. É necessário atualizar as legendas do DLC/DEF e revisar as equações com o grupo antes do relatório final.

### Testes

O script contém verificação por sprint de conservação do backlog, índices nos limites e estoques não negativos. Testa ausência de geração de bugs e de demanda, faz análise de sensibilidade para atrasos de 1/3/6 sprints, diferentes taxas de bugs, efeito hipotético da IA e critério de métrica. Pesquisa um equilíbrio **aproximado**, e não afirma que equilíbrio inexista quando o teste não o encontra.

### Limitações e revisão necessária

1. As unidades UDT, conhecimento e dependência são **índices propostos**, não extraídos de repositórios corporativos.
2. Frações de capacidade, atraso de bugs e relações entre pressão e decisões são hipóteses.
3. Os diagramas originais ainda precisam explicitar conversão bugs→tarefas, métrica de produtividade, efeito condicionado da IA e dinâmica do know-how.
4. Para o relatório final, compare a trajetória simulada ao comportamento **qualitativo** descrito pelos participantes e registre alterações de parâmetros.
5. Declare o uso de IA generativa e a conferência de código e equações pelos integrantes, como pede a disciplina.
