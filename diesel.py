import math
import numpy_financial as npf
from recargas import RecargaBase
from scipy.optimize import brentq, minimize_scalar


class SimuladorDiesel(RecargaBase):
    def calcular_massa_total_diesel(self, L, T, num_passageiros, pot_nominal_eixo):
        massa_passageiros = num_passageiros * 70
        massa_casco = self.comum.calcular_massa_total_casco(L, T, False)
        massa_motor = 2.873 * pot_nominal_eixo - 138.37
        massa_tanque_agua = num_passageiros * 10
        massa_outros = (num_passageiros * 10) + (L * 70)

        massa_total_barca = massa_passageiros + massa_casco + massa_motor + massa_tanque_agua + massa_outros
        return massa_total_barca

    def calcular_financas_diesel(self, L, T_eq, v_knts_t, d_km, f_fisica, convergido):
        boca_max = L / 2
        pontal = T_eq + 1.1
        cotacao_real_dolar = 4.81
        taxa_desconto = 0.07
        preco_diesel = 1.0

        custo_aquisicao_barco = ((0.000000008) * (f_fisica["num_passageiros"] * v_knts_t)**2 +
                                  0.0006 * (f_fisica["num_passageiros"] * v_knts_t) -
                                  0.00000000000002) * 10**6
        custo_projeto = custo_aquisicao_barco * 0.01
        custo_motor_combustao = 59.72 * (f_fisica["pot_nominal_eixo"] * 0.7457) - 12.086

        custo_capital_total = custo_aquisicao_barco

        # Tempo de uma perna da viagem, calculado a partir da velocidade e distância da rota, usado
        # para estimar quantas viagens o barco realiza por dia dentro da janela operacional.
        tempo_perna_viagem = f_fisica["tempo_cruzeiro"] + 1.0 + 4.5 + 1.0 + 5.0
        num_viagens_dia = (16.0 * 60.0) / tempo_perna_viagem
        # Viagens inteiras por dia (usado para receita e taxas - só conta viagens completas)
        num_viagens_dia_inteiro = math.floor(num_viagens_dia)
        num_viagens_ano = num_viagens_dia_inteiro * 350

        litros_diesel_dia = (f_fisica["energia_rota"] * num_viagens_dia) * (187.0 / 842.6)
        custo_anual_combustivel = litros_diesel_dia * 350 * preco_diesel

        # Custo de tripulação por faixa de comprimento do barco. Para L >= 40m: comandante, imediato,
        # chefe de máquinas e 5 marinheiros.
        dados_tripulacao = [
            {"qtde": 1, "salario": 10000, "imposto": 7500, "meses": 13},  # Comandante
            {"qtde": 1, "salario": 7000, "imposto": 5250, "meses": 13},   # Imediato
            {"qtde": 1, "salario": 7000, "imposto": 5250, "meses": 13},   # Chefe Maquinas
            {"qtde": 5, "salario": 3000, "imposto": 2250, "meses": 13},   # Marinheiros
        ]
        custo_tripulacao_reais = sum([t["qtde"] * (t["salario"] + t["imposto"]) * t["meses"] for t in dados_tripulacao])
        custo_tripulacao = custo_tripulacao_reais / cotacao_real_dolar

        custo_anual_pintura = (((L * pontal) * 4) + ((boca_max * L) * 2)) * 2 * 0.1 * 130 / cotacao_real_dolar
        valor_passagem = 7.7 / cotacao_real_dolar
        custo_anual_portuaria = 0.1 * valor_passagem * 0.25 * f_fisica["num_passageiros"] * num_viagens_ano
        custo_docagem = 0.02 * custo_capital_total

        custo_operacional_anual = (custo_anual_combustivel + custo_tripulacao + custo_anual_pintura +
                                    custo_anual_portuaria + custo_docagem)

        rendimento_bruto_passagens = valor_passagem * num_viagens_ano * 0.25 * f_fisica["num_passageiros"]
        fluxo_caixa_anual = (rendimento_bruto_passagens * 0.7) - custo_operacional_anual

        fluxo_caixa_completo = [-custo_capital_total] + [fluxo_caixa_anual] * 20
        vpl_resultado = npf.npv(taxa_desconto, fluxo_caixa_completo)
        tir_resultado = npf.irr(fluxo_caixa_completo)

        empuxo_final = self.comum.calculo_deslocamento_calculado(L, T_eq)
        massa_total_barca_real = self.calcular_massa_total_diesel(L, T_eq, f_fisica["num_passageiros"], f_fisica["pot_nominal_eixo"])

        retorno = {
            "tir": tir_resultado, "vpl": vpl_resultado, "calado": T_eq,
            "massa_total_barca": massa_total_barca_real, "deslocamento": empuxo_final,
            "pot_infra": "-", "b_bateria_rec": "-", "b_baterias": "-", "trocas": "-",
            "custo_baterias_anual_troca": "-", "infraestrutura_recarga": "-",
            "crate_carga": "-", "crate_descarga": "-", "ciclos_eol": "-",
            "dod_efetivo": "-", "dod_alvo": "-", "pot_nominal": f_fisica["pot_nominal_eixo"],
            "convergido": convergido,

            "custo_capital_total": custo_capital_total, "custo_operacional_anual": custo_operacional_anual,
            "fluxo_caixa_anual": fluxo_caixa_anual, "custo_aquisicao_barco": custo_aquisicao_barco,
            "custo_motor_combustao": custo_motor_combustao, "custo_projeto": custo_projeto,
            "litros_diesel_dia": litros_diesel_dia, "custo_anual_combustivel": custo_anual_combustivel,
            "custo_tripulacao": custo_tripulacao, "custo_anual_pintura": custo_anual_pintura,
            "custo_anual_portuaria": custo_anual_portuaria, "custo_docagem": custo_docagem,
            "rendimento_bruto_passagens": rendimento_bruto_passagens
        }
        retorno.update(f_fisica)
        return retorno

    def simular(self, L, v_knts_t, d_km=5.0):
        def objetivo_calado(T_tentativo):
            fisica = self.calcular_demanda_energetica(L, T_tentativo, v_knts_t, d_km)
            massa_total = self.calcular_massa_total_diesel(L, T_tentativo, fisica["num_passageiros"], fisica["pot_nominal_eixo"])
            empuxo = self.comum.calculo_deslocamento_calculado(L, T_tentativo)
            return massa_total - empuxo

        convergido = True
        try:
            T_eq = brentq(objetivo_calado, 0.5, 2.5)
        except ValueError:
            try:
                T_eq = brentq(objetivo_calado, 0.3, 10.0)
            except ValueError:
                T_eq = minimize_scalar(lambda t: abs(objetivo_calado(t)), bounds=(0.3, 10.0), method='bounded').x
                convergido = False

        fisica_final = self.calcular_demanda_energetica(L, T_eq, v_knts_t, d_km)
        return self.calcular_financas_diesel(L, T_eq, v_knts_t, d_km, fisica_final, convergido)