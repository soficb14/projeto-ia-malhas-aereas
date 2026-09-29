# Malhas Aéreas — Busca em Grafos

Projeto desenvolvido para a disciplina de Inteligência Artificial, com o objetivo de aplicar algoritmos de busca em um domínio de malha aérea.

O problema é modelado como um grafo direcionado, no qual os aeroportos representam os estados do ambiente e os voos representam as ações possíveis. A partir dessa modelagem, são implementados e comparados os algoritmos de Busca em Largura (BFS) e A*.

## Objetivo

Encontrar rotas entre aeroportos considerando a distância total percorrida.

O projeto utiliza três versões da malha aérea, permitindo analisar o comportamento dos algoritmos em diferentes tamanhos de espaço de busca:

- **Mapa pequeno:** 10 aeroportos
- **Mapa médio:** 25 aeroportos
- **Mapa grande:** 40 aeroportos

Os mapas utilizam a mesma representação conceitual de uma malha aérea como grafo direcionado.

## Modelagem do problema

A malha aérea é representada como um grafo direcionado:

- **Estado:** aeroporto.
- **Ação:** voo direto entre dois aeroportos.
- **Transição:** deslocamento do aeroporto de origem para o aeroporto de destino.
- **Custo da ação:** distância do voo em quilômetros.
- **Estado inicial:** aeroporto de origem da consulta.
- **Estado objetivo:** aeroporto de destino.

Para um caminho:

```text
A₀ → A₁ → ... → Aₙ
```

o custo total é calculado pela soma das distâncias dos voos:

```text
g(n) = Σ d(Aᵢ, Aᵢ₊₁)
```

onde `d(Aᵢ, Aᵢ₊₁)` representa a distância do voo entre dois aeroportos consecutivos.

## Algoritmos implementados

### BFS — Busca em Largura

A BFS é uma estratégia de busca não informada que explora os estados por níveis, utilizando uma fila.

Neste projeto, ela é utilizada como referência para comparação com uma estratégia que utiliza informação heurística sobre o domínio.

Como os voos possuem custos diferentes, a BFS não deve ser interpretada como um algoritmo de otimização da distância em quilômetros. Ela prioriza a quantidade de arestas da rota.

### A*

O A* combina o custo acumulado do caminho com uma estimativa do custo restante:

```text
f(n) = g(n) + h(n)
```

onde:

- `g(n)` é o custo acumulado desde a origem;
- `h(n)` é a estimativa do custo restante;
- `f(n)` é o valor utilizado para priorizar os estados.

A heurística utilizada é a distância geográfica em linha reta entre o aeroporto atual e o destino.

Para validar a heurística, as distâncias dos voos foram verificadas para garantir que o custo de cada voo não seja inferior à distância em linha reta entre seus aeroportos.

## Estrutura do projeto

```text
projeto-ia-malhas-aereas/
├── data/
│   └── maps/
│       ├── airports.json
│       ├── mapa_pequeno.json
│       ├── mapa_medio.json
│       └── mapa_grande.json
│
├── docs/
│   └── documentação do projeto
│
├── experiments/
│   └── phase1/
│       └── experimentos da Fase 1
│
├── notebooks/
│   └── Marco_I_Experimentos.ipynb
│
├── results/
│   └── resultados dos experimentos
│
├── scripts/
│   └── scripts auxiliares
│
├── src/
│   ├── environment/
│   │   ├── airport.py
│   │   ├── flight.py
│   │   ├── graph.py
│   │   └── loader.py
│   │
│   └── search/
│       ├── bfs.py
│       ├── astar.py
│       └── heuristics.py
│
├── tests/
│   ├── test_astar.py
│   ├── test_bfs.py
│   ├── test_graph.py
│   ├── test_heuristics.py
│   └── test_maps.py
│
├── requirements.txt
└── README.md
```

## Testes automatizados

O projeto possui testes automatizados para verificar:

- estrutura e funcionamento do grafo;
- validade dos mapas;
- comportamento da BFS;
- comportamento do A*;
- propriedades da heurística utilizada.

Para executar os testes localmente:

```bash
python3 -m pytest tests -v
```

Todos os testes devem ser executados antes da realização dos experimentos.

## Notebook

O projeto possui um notebook com os experimentos da Fase 1:

```text
notebooks/Marco_I_Experimentos.ipynb
```

O notebook foi preparado para execução no Google Colab e pode ser executado integralmente em uma sessão nova.

Ao executar o notebook, são realizados automaticamente:

1. clonagem do repositório quando necessário;
2. instalação das dependências;
3. verificação da estrutura dos arquivos;
4. limpeza de caches de execução;
5. execução dos testes automatizados;
6. carregamento dos três mapas;
7. execução dos algoritmos BFS e A*;
8. coleta das métricas;
9. comparação dos resultados;
10. análise dos experimentos.

Após abrir o notebook no Google Colab, utilize **Executar tudo (Run all)** para reproduzir os experimentos.

## Experimento principal

O experimento principal utiliza a busca por uma rota entre:

```text
ATL → LAX
```

A mesma consulta é executada nos mapas pequeno, médio e grande.

Isso permite observar o comportamento das estratégias de busca em diferentes tamanhos de espaço de estados.

As seguintes métricas são coletadas:

- **Custo da rota:** distância total percorrida em quilômetros;
- **Nós expandidos:** quantidade de estados processados durante a busca;
- **Tempo de execução:** tempo necessário para encontrar a solução, em milissegundos.

## Heurística

A heurística utilizada pelo A* é baseada na distância geográfica em linha reta entre dois aeroportos.

As coordenadas geográficas dos aeroportos são armazenadas em:

```text
data/maps/airports.json
```

A distância geográfica é utilizada como estimativa do custo restante até o destino.

Durante a validação dos mapas, cada voo é comparado com a distância em linha reta entre seus aeroportos. Dessa forma, garante-se que a distância registrada para um voo não seja menor que a distância geográfica correspondente.

## Tecnologias utilizadas

- Python 3
- pytest
- Google Colab
- Git
- GitHub
- JSON

## Reprodução

Para reproduzir o projeto localmente:

```bash
git clone https://github.com/soficb14/projeto-ia-malhas-aereas.git
cd projeto-ia-malhas-aereas
pip install -r requirements.txt
python3 -m pytest tests -v
```

Para reproduzir os experimentos, abra:

```text
notebooks/Marco_I_Experimentos.ipynb
```

no Google Colab e execute todas as células em sequência.

## Autores
Sofia de Carvalho Brito - 2512130063
Pedro de Faria Mello - 2512130037
Victor Sousa Pereira - 2512130015


Projeto acadêmico desenvolvido para a disciplina de Inteligência Artificial.
