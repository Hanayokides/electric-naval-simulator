# Simulador Naval Elétrico

Modelo de dimensionamento e viabilidade financeira para uma embarcação de transporte de passageiros (catamarã, 53 m), comparando diferentes estratégias de propulsão:

- **Diesel** (motor a combustão, baseline)
- **Recarga Rápida** (1 e 2 terminais)
- **Recarga Lenta** (overnight)
- **Recarga Mista** (combinação de rápida + lenta, com potência de infraestrutura ajustável, 1 e 2 terminais)

Para cada configuração, o modelo dimensiona o casco (calado de equilíbrio via balanço de massa/empuxo), calcula a demanda energética da rota e estima a Taxa Interna de Retorno (TIR) e o Valor Presente Líquido (VPL) do investimento.

## Estrutura do código

| Arquivo | Conteúdo |
|---|---|
| `calculos_comuns.py` | Equações de hidrostática e massa estrutural do casco (comuns a todas as configurações) |
| `recargas.py` | Modelos de demanda energética e retorno financeiro para Recarga Rápida, Lenta e Mista |
| `diesel.py` | Modelo de retorno financeiro para a configuração a Diesel |
| `main.py` | Orquestração das simulações, geração dos relatórios (Excel e Word) e dos gráficos de sensibilidade |

## Como rodar

### Dependências

```bash
pip install pandas numpy matplotlib scipy numpy-financial python-docx openpyxl
```

### Execução

```bash
python main.py
```

O programa pergunta o modo de execução:
- **O** — apenas os resultados ótimos (DOD que maximiza o TIR em cada configuração)
- **M** — inclui também uma varredura de múltiplos valores de DOD para comparação
- **ESC** — encerra sem rodar

### Saídas

- Uma planilha Excel (`planilha_dimensionamento_completa_*.xlsx`) com os resultados detalhados de cada configuração, rota e velocidade simulada.
- Um relatório Word (`relatorio_graficos_completo_*.docx`) com os gráficos de sensibilidade (TIR vs. DOD, TIR vs. Potência de infraestrutura) e tabelas-resumo.

## Parâmetros principais

- Comprimento da embarcação: 53 m (fixo)
- Rotas simuladas: 5, 7.5, 10, 12.5 e 15 km
- Velocidades simuladas: 8, 12, 16 e 20 nós
