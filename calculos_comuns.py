import math


class ModeloComumNaval:
    """
    Classe responsável pelas equações comuns de hidrostática e massa da estrutura.
    """

    def __init__(self, debug=False):
        self.debug = debug

    def calculo_deslocamento_calculado(self, L, T):
        boca_lwl = L / 9
        Cb = 0.5339 * (T ** 0.3389)
        deslocamento_calculado = L * boca_lwl * T * Cb * 1025 * 2
        return deslocamento_calculado

    def calcular_massa_total_casco(self, L, T, forcar_debug=False):
        boca_max = L / 2
        boca_lwl = L / 9
        boca_moldada = boca_lwl * 1.1
        pontal = T + 1.1
        s = 500
        sy = 220
        C1 = 3.5
        minimo = 6
        s_y = sy * 0.5
        q = 235 / s_y
        h = L / 10

        t_I34 = (((q * h) ** (1 / s)) / 272) + 2
        t_I40 = 0.003 * s * ((q * h) ** 0.5)

        t_mm_I41 = C1 + (0.042 * L) * (q ** 0.5)
        espessura_fundo = max(minimo, t_mm_I41)

        altura_caverna_M21 = (L / 1.2) / 1.1
        altura_caverna_M4 = L / 1.2
        num_vigas_conves_M44 = L * 0.75 / 0.5
        ro_aluminio = 2700
        espessura_m = math.ceil(espessura_fundo) / 1000
        h_caverna = altura_caverna_M21 / 100
        h_longarina = altura_caverna_M4 / 100

        massa_chapeamento_casco = 2 * ((2 * (pontal + boca_moldada) * L) * 0.7 * 0.7 * espessura_m * ro_aluminio)

        massa_uma_caverna = (2 * boca_moldada + 2 * pontal) * 0.7 * (h_caverna * espessura_m) * ro_aluminio
        num_cavernas = L / (s / 1000)
        massa_total_cavernas = 2 * (num_cavernas * massa_uma_caverna)

        massa_uma_longarina = L * h_longarina * espessura_m * ro_aluminio
        num_longarinas = boca_max / 2.65
        massa_total_longarinas = num_longarinas * massa_uma_longarina

        massa_conves_principal = 2 * L * boca_max * 0.75 * espessura_m * ro_aluminio

        massa_viga_tranqv_conves = (boca_max - 2 * boca_moldada) * (h_longarina * espessura_m) * ro_aluminio
        massa_total_vigas_conves = num_vigas_conves_M44 * massa_viga_tranqv_conves

        massa_chapeamento_superestrutura = (2 * L * 0.75 + 2 * boca_max) * 2 * espessura_m * ro_aluminio
        massa_teto_superestrutura = L * boca_max * espessura_m * ro_aluminio * 0.75

        num_vigas_superestrutura = L * 0.75
        massa_caverna_superestrutura = (h_caverna / 2 * espessura_m) * (boca_max + 4) * ro_aluminio
        massa_total_cavernas_super = num_vigas_superestrutura * massa_caverna_superestrutura

        num_vigas_long_super = boca_max / 2
        massa_long_super_conves = (h_longarina / 2 * espessura_m) * (L * 0.75) * ro_aluminio
        massa_total_long_super = num_vigas_long_super * massa_long_super_conves

        anteparas = boca_moldada * pontal * (L / 5) * 0.7 * espessura_m * ro_aluminio

        soma_massas = (massa_chapeamento_casco + massa_total_cavernas +
                       massa_total_longarinas + massa_conves_principal + massa_chapeamento_superestrutura +
                       massa_total_vigas_conves +
                       massa_teto_superestrutura + massa_total_cavernas_super +
                       massa_total_long_super + anteparas)

        bolboletas_solda = soma_massas * 0.1
        outros = bolboletas_solda

        massa_total_casco = (massa_total_long_super + massa_total_cavernas_super +
                              massa_total_vigas_conves + massa_conves_principal +
                              anteparas + massa_teto_superestrutura + outros +
                              massa_chapeamento_superestrutura + outros +
                              (massa_total_longarinas + massa_total_cavernas + massa_chapeamento_casco) * 2)

        return massa_total_casco

    def calcular_massa_total_barca(self, L, T, num_passageiros, banco_kwh, pot_nominal_eixo):
        massa_passageiros = num_passageiros * 70
        massa_casco = self.calcular_massa_total_casco(L, T, False)
        massa_baterias = banco_kwh * 13.0
        massa_motor = 2.6342 * pot_nominal_eixo + 457.12
        massa_tanque_agua = num_passageiros * 10
        massa_outros = (num_passageiros * 10) + (L * 70)

        massa_total_barca = (massa_passageiros + massa_baterias + massa_casco +
                              massa_motor + massa_tanque_agua + massa_outros)

        return massa_total_barca