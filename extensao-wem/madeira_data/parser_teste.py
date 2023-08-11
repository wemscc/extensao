import json
classe = "D60"
f = open("madeiras.json")
data = json.load(f)
d = list(data[classe][0].values())
class Madeira:
    def __init__(self, classe, f_bk, f_t0k, f_t90k, f_c0k, f_c90k, f_cvk, E_0m, E_005, E_90m, G_m, p_k, p_m):
        self.classe = classe
        self.f_bk = f_bk
        self.f_t0k = f_t0k
        self.f_t90k = f_t90k
        self.f_c0k = f_c0k
        self.f_c90k = f_c90k
        self.f_cvk = f_cvk
        self.E_0m = E_0m
        self.E_005 = E_005
        self.E_90m = E_90m
        self.G_m = G_m
        self.p_k = p_k
        self.p_m = p_m


madeira = Madeira(classe,d[0],d[1],d[2],d[3],d[4],d[5],d[6],d[7],d[8],d[9],d[10],d[11])
print(f"{madeira.classe}\n{madeira.f_bk}\n{madeira.f_t0k}\n{madeira.f_t90k}\n{madeira.f_c0k}\n{madeira.f_c90k}\n{madeira.f_cvk}\n{madeira.E_90m}\n{madeira.E_005}\n{madeira.E_90m}\n{madeira.G_m}\n{madeira.p_k}\n{madeira.p_m}")
f.close()
