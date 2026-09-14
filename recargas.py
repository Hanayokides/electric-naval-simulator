import math
import numpy_financial as npf


class RecargaBase:
    def __init__(self, modelo_comum):
        self.comum = modelo_comum

    def calcular_demanda_energetica(self, L, T_tentativo, v_knts_t, d_km):
        boca_max = L / 2
        pontal_temp = T_tentativo + 1.1
        area_conves = L * boca_max
        num_pass_t = (area_conves - (2 * L)) + 1

        v = v_knts_t
        T = T_tentativo
        res_slender_t = (
            -410.3930
            + 65.2767 * T
            + 112.7799 * v
            + 50.1402 * (T**2)
            - 28.6746 * T * v
            - 9.1978 * (v**2)
            - 3.2578 * (T**2) * v
            + 2.0769 * T * (v**2)
            + 0.2578 * (v**3)
        )
        res_hidro_t = res_slender_t * 2

        area_front_t = (pontal_temp - T_tentativo + 2) * boca_max
        v_ms_t = v * 0.514444
        res_aero_N_t = (area_front_t * 0.6 * 1.2928 * (v_ms_t**2)) / 2
        res_aero_Kw_t = (res_aero_N_t * v_ms_t) / 1000

        pot_eixo_t = (res_hidro_t + res_aero_Kw_t) / 0.5
        pot_eixo_margem_t = pot_eixo_t * 1.15
        pot_nominal_eixo_kw_t = pot_eixo_margem_t / 0.85

        pot_entrada_kw_t = pot_eixo_margem_t / (0.9 * 0.9)
        pot_nominal_entrada_kw_t = pot_entrada_kw_t / 0.85

        distancia_milhas_nauticas = d_km / 1.852
        tempo_cruzeiro_horas = distancia_milhas_nauticas / v_knts_t
        tempo_cruzeiro_minutos = tempo_cruzeiro_horas * 60.0

        tempo_aceleracao = 1.0
        tempo_desaceleracao = 4.5
        tempo_manobra = 1.0
        tempo_parado_porto = 5.0
        h_conv = 0.0166667

        e_travessia_t = pot_nominal_entrada_kw_t * 0.85 * tempo_cruzeiro_minutos * h_conv
        e_aceleracao_t = pot_nominal_entrada_kw_t * 0.90 * tempo_aceleracao * h_conv
        e_desaceleracao_t = pot_nominal_entrada_kw_t * 0.25 * tempo_desaceleracao * h_conv
        e_manobra_t = pot_nominal_entrada_kw_t * 0.90 * tempo_manobra * h_conv

        energia_hotel_t = 50 * (tempo_parado_porto + tempo_cruzeiro_minutos + tempo_aceleracao +
                                 tempo_desaceleracao + tempo_manobra) * h_conv
        energia_total_rota_temp = e_travessia_t + e_aceleracao_t + e_desaceleracao_t + e_manobra_t + energia_hotel_t

        return {
            "energia_rota": energia_total_rota_temp,
            "pot_entrada": pot_entrada_kw_t,
            "pot_nominal_eixo": pot_nominal_eixo_kw_t,
            "num_passageiros": num_pass_t,
            "tempo_cruzeiro": tempo_cruzeiro_minutos,
            "res_slender": res_slender_t,
            "res_hidro": res_hidro_t,
            "res_aero_N": res_aero_N_t,
            "res_aero_Kw": res_aero_Kw_t,
            "pot_eixo": pot_eixo_t,
            "pot_eixo_margem": pot_eixo_margem_t,
            "pot_nominal_entrada": pot_nominal_entrada_kw_t,
            "e_travessia": e_travessia_t,
            "e_aceleracao": e_aceleracao_t,
            "e_desaceleracao": e_desaceleracao_t,
            "e_manobra": e_manobra_t,
            "energia_hotel": energia_hotel_t,
            "area_front": area_front_t
        }

    def calcular_financas_e_retorno(self, L, T_eq, v_knts_t, d_km, tipo_terminal, num_infra, f_fisica,
                                     banco_bateria_kwh, pot_infraestrutura_recarga, convergido, tag_caso="",
                                     modo_lento=False, modo_misto=False, banco_bruto_lento=0.0,
                                     banco_util_misto=0.0, bateria_usd_kWh=500, fator_custo_infra=1.0,
                                     fator_eol=1.0):
        boca_max = L / 2
        pontal = T_eq + 1.1
        cotacao_real_dolar = 4.81
        taxa_desconto = 0.07

        banco_baterias = bateria_usd_kWh * banco_bateria_kwh
        infraestrutura_recarga = (691.75 * pot_infraestrutura_recarga + 1349.4) * num_infra * fator_custo_infra
        soma_custos_capital = banco_baterias + infraestrutura_recarga + banco_baterias
        custo_cabeamento = banco_baterias * 0.1
        custo_motorizacao = 275 * f_fisica["pot_nominal_eixo"]

        custo_aquisicao_barco = ((0.000000008) * (f_fisica["num_passageiros"] * v_knts_t)**2 +
                                  0.0006 * (f_fisica["num_passageiros"] * v_knts_t) -
                                  0.00000000000002) * 10**6
        custo_projeto = custo_aquisicao_barco * 0.01
        valor_venda_motor_combustao = 59.72 * (f_fisica["pot_nominal_eixo"] * 0.7457) - 12.086

        custo_capital_total = (soma_custos_capital + custo_projeto + custo_cabeamento +
                                custo_motorizacao + custo_aquisicao_barco - valor_venda_motor_combustao)

        # Tempo de uma perna da viagem, calculado a partir da velocidade e distância da rota, usado
        # para estimar quantas viagens o barco realiza por dia dentro da janela operacional.
        tempo_perna_viagem = f_fisica["tempo_cruzeiro"] + 1.0 + 4.5 + 1.0 + 5.0
        num_viagens_dia_continuo = (16.0 * 60.0) / tempo_perna_viagem
        # Número de viagens inteiras por dia (usado para receita e taxas - só conta viagens completas)
        num_viagens_dia_inteiro = math.floor(num_viagens_dia_continuo)

        if modo_lento:
            dod_efetivo = banco_bruto_lento / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
            num_ciclo_dia = 1.0
        elif modo_misto:
            energia_perna_misto = (2 * f_fisica["energia_rota"]) if tipo_terminal == "1T" else f_fisica["energia_rota"]
            # DOD real (energia de uma perna dividida pelo banco de baterias) - usado no cálculo de
            # ciclos até o fim de vida da bateria
            dod_efetivo = energia_perna_misto / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
            # DOD alvo (banco útil acumulado dividido pelo banco de baterias = 1/variavel_dod) - usado
            # separadamente na fórmula logarítmica de ciclos até troca por DOD
            dod_alvo_misto = banco_util_misto / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
            num_ciclo_dia = num_viagens_dia_continuo / 2 if tipo_terminal == "1T" else num_viagens_dia_continuo
        else:
            if tipo_terminal == "1T":
                dod_efetivo = (2 * f_fisica["energia_rota"]) / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
                num_ciclo_dia = num_viagens_dia_continuo / 2
            else:
                dod_efetivo = f_fisica["energia_rota"] / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
                num_ciclo_dia = num_viagens_dia_continuo

        crate_carga = pot_infraestrutura_recarga / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
        crate_descarga = f_fisica["pot_entrada"] / banco_bateria_kwh if banco_bateria_kwh > 0 else 0
        num_ciclos_anual = num_ciclo_dia * 350

        try:
            num_ciclos_ate_EOL = fator_eol * 533.95 / (0.00157317624848057 * crate_carga**2 +
                                            0.142518825665524 * dod_efetivo**2 +
                                            0.0436969889496851)
            if modo_lento:
                num_ciclos_EOL_antes_troca_DOD = math.log(max(1e-5, dod_efetivo), 0.8)
            elif modo_misto:
                num_ciclos_EOL_antes_troca_DOD = math.log(max(1e-5, dod_alvo_misto), 0.8)
            elif tipo_terminal == "1T":
                num_ciclos_EOL_antes_troca_DOD = math.log(max(1e-5, (2 * f_fisica["energia_rota"]) / banco_bateria_kwh), 0.8)
            else:
                num_ciclos_EOL_antes_troca_DOD = math.log(max(1e-5, f_fisica["energia_rota"] / banco_bateria_kwh), 0.8)

            denominador = num_ciclos_ate_EOL * num_ciclos_EOL_antes_troca_DOD
            trocas_anuais_bateria = (num_ciclos_anual / denominador) if denominador != 0 else float('nan')
        except Exception:
            num_ciclos_ate_EOL = float('nan')
            trocas_anuais_bateria = float('nan')

        custo_baterias_anual_troca = trocas_anuais_bateria * banco_baterias if not math.isnan(trocas_anuais_bateria) else 0

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
        num_viagens_ano = num_viagens_dia_inteiro * 350
        custo_anual_portuaria = 0.1 * valor_passagem * 0.25 * f_fisica["num_passageiros"] * num_viagens_ano
        custo_docagem = 0.02 * custo_capital_total
        custo_anual_eletricidade = (f_fisica["energia_rota"] * num_viagens_ano / 0.95) * (0.7 / cotacao_real_dolar)

        custo_operacional_anual = (custo_baterias_anual_troca + custo_tripulacao + custo_anual_pintura +
                                    custo_anual_portuaria + custo_docagem + custo_anual_eletricidade)
        rendimento_bruto_passagens = valor_passagem * num_viagens_ano * 0.25 * f_fisica["num_passageiros"]
        fluxo_caixa_anual = (rendimento_bruto_passagens * 0.7) - custo_operacional_anual

        fluxo_caixa_completo = [-custo_capital_total] + [fluxo_caixa_anual] * 20
        vpl_resultado = npf.npv(taxa_desconto, fluxo_caixa_completo)
        tir_resultado = npf.irr(fluxo_caixa_completo)

        empuxo_final = self.comum.calculo_deslocamento_calculado(L, T_eq)
        massa_total_barca_real = self.comum.calcular_massa_total_barca(
            L=L, T=T_eq, num_passageiros=f_fisica["num_passageiros"],
            banco_kwh=banco_bateria_kwh, pot_nominal_eixo=f_fisica["pot_nominal_eixo"]
        )

        log_txt = (
            f"\n" + "="*95 + f"\n [RASTREAMENTO] {tag_caso} Rota: {d_km} km | Terminais/Modo: {tipo_terminal} | V: {v_knts_t} knts\n" +
            "="*95 +
            f"\n Calado (Teq) = {T_eq:.4f} m\n"
        )

        retorno = {
            "tir": tir_resultado, "vpl": vpl_resultado, "calado": T_eq,
            "massa_total_barca": massa_total_barca_real,
            "deslocamento": empuxo_final, "pot_infra": pot_infraestrutura_recarga,
            "b_bateria_rec": banco_bateria_kwh, "b_baterias": banco_baterias,
            "trocas": trocas_anuais_bateria, "custo_baterias_anual_troca": custo_baterias_anual_troca,
            "infraestrutura_recarga": infraestrutura_recarga,
            "crate_carga": crate_carga, "crate_descarga": crate_descarga,
            "ciclos_eol": num_ciclos_ate_EOL, "dod_efetivo": dod_efetivo,
            "dod_alvo": (dod_alvo_misto if modo_misto else "-"),
            "pot_nominal": f_fisica["pot_nominal_eixo"],
            "convergido": convergido, "log_trace": log_txt,

            "custo_capital_total": custo_capital_total, "custo_operacional_anual": custo_operacional_anual,
            "fluxo_caixa_anual": fluxo_caixa_anual, "custo_aquisicao_barco": custo_aquisicao_barco,
            "custo_motorizacao": custo_motorizacao, "custo_cabeamento": custo_cabeamento,
            "custo_projeto": custo_projeto, "valor_venda_motor_combustao": valor_venda_motor_combustao,
            "custo_tripulacao": custo_tripulacao, "custo_anual_pintura": custo_anual_pintura,
            "custo_anual_portuaria": custo_anual_portuaria, "custo_docagem": custo_docagem,
            "custo_anual_eletricidade": custo_anual_eletricidade,
            "rendimento_bruto_passagens": rendimento_bruto_passagens
        }
        retorno.update(f_fisica)
        return retorno


class RecargaRapida(RecargaBase):
    def simular(self, L, variavel_dod, tipo_terminal, v_knts_t, d_km=5.0, forcar_debug=False,
                bateria_usd_kWh=500, fator_custo_infra=1.0, fator_eol=1.0):
        from scipy.optimize import brentq, minimize_scalar
        num_infra = 1.0 if tipo_terminal == "1T" else 2.0

        def objetivo_calado(T_tentativo):
            fisica = self.calcular_demanda_energetica(L, T_tentativo, v_knts_t, d_km)
            banco_kwh = (2 / num_infra) * fisica["energia_rota"] * variavel_dod
            massa_total = self.comum.calcular_massa_total_barca(
                L=L, T=T_tentativo, num_passageiros=fisica["num_passageiros"],
                banco_kwh=banco_kwh, pot_nominal_eixo=fisica["pot_nominal_eixo"]
            )
            empuxo = self.comum.calculo_deslocamento_calculado(L, T_tentativo)
            return massa_total - empuxo

        convergido = True
        try:
            T_eq = brentq(objetivo_calado, 0.7, 1.7)
        except ValueError:
            try:
                T_eq = brentq(objetivo_calado, 0.5, 2.5)
            except ValueError:
                try:
                    T_eq = brentq(objetivo_calado, 0.3, 10.0)
                except ValueError:
                    T_eq = minimize_scalar(lambda t: abs(objetivo_calado(t)), bounds=(0.3, 10.0), method='bounded').x
                    convergido = False

        fisica_final = self.calcular_demanda_energetica(L, T_eq, v_knts_t, d_km)
        pot_infra = (2 * fisica_final["energia_rota"]) / (5/60) if tipo_terminal == "1T" else (fisica_final["energia_rota"]) / (5/60)
        banco_final_kwh = (2 / num_infra) * fisica_final["energia_rota"] * variavel_dod

        return self.calcular_financas_e_retorno(L, T_eq, v_knts_t, d_km, tipo_terminal, num_infra, fisica_final,
                                                  banco_final_kwh, pot_infra, convergido,
                                                  f"RECARGA RAPIDA ({tipo_terminal})",
                                                  bateria_usd_kWh=bateria_usd_kWh,
                                                  fator_custo_infra=fator_custo_infra, fator_eol=fator_eol)


class RecargaLenta(RecargaBase):
    def simular(self, L, variavel_dod, tipo_terminal="Lenta", v_knts_t=12.0, d_km=5.0, forcar_debug=False,
                bateria_usd_kWh=500, fator_custo_infra=1.0, fator_eol=1.0):
        from scipy.optimize import brentq, minimize_scalar
        num_infra = 1.0

        def objetivo_calado(T_tentativo):
            fisica = self.calcular_demanda_energetica(L, T_tentativo, v_knts_t, d_km)
            banco_bruto_kwh = 38.4 * fisica["energia_rota"]
            banco_kwh = banco_bruto_kwh * variavel_dod
            massa_total = self.comum.calcular_massa_total_barca(
                L=L, T=T_tentativo, num_passageiros=fisica["num_passageiros"],
                banco_kwh=banco_kwh, pot_nominal_eixo=fisica["pot_nominal_eixo"]
            )
            empuxo = self.comum.calculo_deslocamento_calculado(L, T_tentativo)
            return massa_total - empuxo

        convergido = True
        try:
            T_eq = brentq(objetivo_calado, 0.7, 2.5)
        except ValueError:
            try:
                T_eq = brentq(objetivo_calado, 0.3, 10.0)
            except ValueError:
                T_eq = minimize_scalar(lambda t: abs(objetivo_calado(t)), bounds=(0.3, 10.0), method='bounded').x
                convergido = False

        fisica_final = self.calcular_demanda_energetica(L, T_eq, v_knts_t, d_km)
        banco_bruto_final = 38.4 * fisica_final["energia_rota"]
        banco_final_kwh = banco_bruto_final * variavel_dod
        pot_infra = banco_bruto_final / 8.0

        return self.calcular_financas_e_retorno(L, T_eq, v_knts_t, d_km, tipo_terminal, num_infra, fisica_final,
                                                  banco_final_kwh, pot_infra, convergido,
                                                  tag_caso="RECARGA LENTA (OVERNIGHT)", modo_lento=True,
                                                  banco_bruto_lento=banco_bruto_final,
                                                  bateria_usd_kWh=bateria_usd_kWh,
                                                  fator_custo_infra=fator_custo_infra, fator_eol=fator_eol)


class RecargaMista(RecargaBase):
    def simular(self, L, variavel_dod, tipo_terminal, v_knts_t, d_km=5.0, pot_infra_manual=1000.0, forcar_debug=False):
        from scipy.optimize import brentq, minimize_scalar
        num_infra = 1.0 if tipo_terminal == "1T" else 2.0

        def objetivo_calado(T_tentativo):
            fisica = self.calcular_demanda_energetica(L, T_tentativo, v_knts_t, d_km)
            energia_perna = (2 * fisica["energia_rota"]) if tipo_terminal == "1T" else fisica["energia_rota"]
            energia_recarga_5min = pot_infra_manual * (5.0 / 60.0)
            deficit = energia_perna - energia_recarga_5min

            tempo_perna = fisica["tempo_cruzeiro"] + 1.0 + 4.5 + 1.0 + 5.0
            num_viagens_dia = (15.833333333 * 60.0) / tempo_perna
            num_recargas_dia = num_viagens_dia / 2.0 if tipo_terminal == "1T" else num_viagens_dia

            if deficit <= 0:
                banco_util = energia_perna
            else:
                banco_util = deficit * (num_recargas_dia - 1.0) + energia_perna

            banco_kwh = banco_util * variavel_dod
            massa_total = self.comum.calcular_massa_total_barca(
                L=L, T=T_tentativo, num_passageiros=fisica["num_passageiros"],
                banco_kwh=banco_kwh, pot_nominal_eixo=fisica["pot_nominal_eixo"]
            )
            empuxo = self.comum.calculo_deslocamento_calculado(L, T_tentativo)
            return massa_total - empuxo

        convergido = True
        try:
            T_eq = brentq(objetivo_calado, 0.5, 3.0)
        except ValueError:
            try:
                T_eq = brentq(objetivo_calado, 0.3, 10.0)
            except ValueError:
                T_eq = minimize_scalar(lambda t: abs(objetivo_calado(t)), bounds=(0.3, 10.0), method='bounded').x
                convergido = False

        fisica_final = self.calcular_demanda_energetica(L, T_eq, v_knts_t, d_km)
        energia_perna_final = (2 * fisica_final["energia_rota"]) if tipo_terminal == "1T" else fisica_final["energia_rota"]
        energia_recarga_5min_final = pot_infra_manual * (5.0 / 60.0)
        deficit_final = energia_perna_final - energia_recarga_5min_final

        tempo_perna_final = fisica_final["tempo_cruzeiro"] + 1.0 + 4.5 + 1.0 + 5.0
        num_viagens_dia_final = (15.833333333 * 60.0) / tempo_perna_final
        num_recargas_dia_final = num_viagens_dia_final / 2.0 if tipo_terminal == "1T" else num_viagens_dia_final

        if deficit_final <= 0:
            banco_util_final = energia_perna_final
        else:
            banco_util_final = deficit_final * (num_recargas_dia_final - 1.0) + energia_perna_final

        banco_final_kwh = banco_util_final * variavel_dod

        return self.calcular_financas_e_retorno(
            L, T_eq, v_knts_t, d_km, tipo_terminal, num_infra, fisica_final, banco_final_kwh,
            pot_infra_manual, convergido,
            tag_caso=f"RECARGA MISTA ({tipo_terminal} {pot_infra_manual}kW)", modo_misto=True,
            banco_util_misto=banco_util_final
        )
