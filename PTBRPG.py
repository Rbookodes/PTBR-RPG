import os, random, time, json, sys

# ─────────────────────────────────────────
#  CORES
# ─────────────────────────────────────────
class C:
    RESET="\033[0m"; BOLD="\033[1m"; BRANCO="\033[97m"; CINZA="\033[90m"
    AMARELO="\033[93m"; VERDE="\033[92m"; VERMELHO="\033[91m"
    CIANO="\033[96m"; ROXO="\033[95m"; AZUL="\033[94m"; LARANJA="\033[33m"

def cor(texto, c): return c + str(texto) + C.RESET
def limpar(): os.system("cls" if os.name=="nt" else "clear")
def pausar(m="  ENTER para continuar..."): input(C.CINZA+"\n"+m+C.RESET)
def linha(c="─",n=52,cl=C.CINZA): print(cl+c*n+C.RESET)

def titulo(txt, emoji="", cl=C.CIANO):
    linha()
    if emoji: print(C.BOLD+cl+"  "+emoji+"  "+txt+"  "+C.RESET)
    else:     print(C.BOLD+cl+"  "+txt+"  "+C.RESET)
    linha()

def digitar(txt, d=0.018):
    for ch in txt: print(ch,end="",flush=True); time.sleep(d)
    print()

def barra(atual, mx, larg=18, cb=C.VERDE, cv=C.CINZA):
    atual=max(0,atual); b=int(atual/max(mx,1)*larg)
    return cb+"█"*b+cv+"░"*(larg-b)+C.RESET


# ─────────────────────────────────────────
#  SISTEMA DE RARIDADES
# ─────────────────────────────────────────
RARIDADES = {
    "Comum":      {"cor": C.BRANCO,   "emoji": "⬜", "mult_stat": 1.0,  "chance": 0.45, "efeito": None},
    "Incomum":    {"cor": C.VERDE,    "emoji": "🟢", "mult_stat": 1.25, "chance": 0.25, "efeito": "regen_hp"},
    "Raro":       {"cor": C.AZUL,     "emoji": "🔵", "mult_stat": 1.55, "chance": 0.13, "efeito": "regen_mp"},
    "Epico":      {"cor": C.ROXO,     "emoji": "🟣", "mult_stat": 1.90, "chance": 0.08, "efeito": "critico_bonus"},
    "Lendario":   {"cor": C.AMARELO,  "emoji": "🟡", "mult_stat": 2.40, "chance": 0.04, "efeito": "double_gold"},
    "Mitico":     {"cor": C.VERMELHO, "emoji": "🔴", "mult_stat": 3.00, "chance": 0.025,"efeito": "vampirismo"},
    "Abissal":    {"cor": C.CINZA,    "emoji": "⚫", "mult_stat": 4.00, "chance": 0.01, "efeito": "ignorar_def"},
    "Conceitual": {"cor": C.CIANO,    "emoji": "🌀", "mult_stat": 6.00, "chance": 0.005,"efeito": "caos"},
}

EFEITOS_DESC = {
    "regen_hp":     "Regenera 5 HP por turno",
    "regen_mp":     "Regenera 5 MP por turno",
    "critico_bonus":"+20% chance de critico",
    "double_gold":  "Dobra gold ganho em batalha",
    "vampirismo":   "Rouba 15% do dano causado como HP",
    "ignorar_def":  "Ignora 50% da defesa inimiga",
    "caos":         "Efeito aleatorio a cada turno",
}

def sortear_raridade():
    r = random.random()
    acum = 0
    for nome, dados in RARIDADES.items():
        acum += dados["chance"]
        if r < acum:
            return nome
    return "Comum"

def nome_colorido_raridade(nome, raridade):
    r = RARIDADES[raridade]
    return r["cor"] + C.BOLD + r["emoji"] + " " + nome + " " + C.RESET

def aplicar_raridade_equip(equip_base, raridade):
    e = dict(equip_base)
    r = RARIDADES[raridade]
    e["raridade"] = raridade
    e["efeito"]   = r["efeito"]
    if "atk" in e and e["atk"] > 0:
        e["atk"] = max(1, int(e["atk"] * r["mult_stat"]))
    if "def" in e and e["def"] > 0:
        e["def"] = max(1, int(e["def"] * r["mult_stat"]))
    return e

def aplicar_raridade_inimigo(ini_base, raridade=None):
    if raridade is None:
        raridade = sortear_raridade()
    ini = dict(ini_base)
    r   = RARIDADES[raridade]
    ini["raridade"] = raridade
    ini["hp"]       = max(1, int(ini["hp"]  * r["mult_stat"]))
    ini["atk"]      = max(1, int(ini["atk"] * r["mult_stat"]))
    ini["def"]      = max(1, int(ini.get("def",0) * r["mult_stat"]))
    ini["xp"]       = int(ini.get("xp",0)   * r["mult_stat"])
    ini["gold"]     = int(ini.get("gold",0)  * r["mult_stat"])
    ini["efeito"]   = r["efeito"]
    # Nome colorido
    ini["nome_display"] = nome_colorido_raridade(ini["nome"], raridade)
    return ini

def aplicar_raridade_item(nome_item, raridade=None):
    if raridade is None:
        raridade = sortear_raridade()
    dados = dict(ITENS.get(nome_item, {}))
    r = RARIDADES[raridade]
    dados["raridade"] = raridade
    dados["efeito"]   = r["efeito"]
    if "efeito" in dados and isinstance(dados.get("efeito"), int):
        dados["efeito"] = int(dados["efeito"] * r["mult_stat"])
    return raridade, dados

def efeito_turno_jogador(j, equip, log):
    ef = equip.get("efeito") if equip else None
    if ef == "regen_hp" and j.hp < j.hp_max:
        j.hp = min(j.hp_max, j.hp + 5)
        log.append(C.VERDE + "  [" + equip.get("raridade","") + "] Regen: +5 HP " + C.RESET)
    elif ef == "regen_mp" and j.mp < j.mp_max:
        j.mp = min(j.mp_max, j.mp + 5)
        log.append(C.AZUL + "  [" + equip.get("raridade","") + "] Regen: +5 MP " + C.RESET)

def efeito_pos_ataque(j, ini, dano, equip, log):
    ef = equip.get("efeito") if equip else None
    if ef == "vampirismo":
        roubo = max(1, int(dano * 0.15))
        j.hp  = min(j.hp_max, j.hp + roubo)
        log.append(C.VERMELHO + "  [Mitico] Vampirismo: +" + str(roubo) + " HP " + C.RESET)
    elif ef == "double_gold":
        pass  # aplicado no final da batalha
    elif ef == "caos":
        op = random.choice(["cura","dano_extra","mp","nada"])
        if op == "cura":
            j.hp = min(j.hp_max, j.hp + 20)
            log.append(C.CIANO + "  [Conceitual] Caos: +20 HP! " + C.RESET)
        elif op == "dano_extra":
            ed = random.randint(10, 50)
            ini["hp_atual"] -= ed
            log.append(C.CIANO + "  [Conceitual] Caos: +" + str(ed) + " dano extra! " + C.RESET)
        elif op == "mp":
            j.mp = min(j.mp_max, j.mp + 25)
            log.append(C.CIANO + "  [Conceitual] Caos: +25 MP! " + C.RESET)
        else:
            log.append(C.CIANO + "  [Conceitual] Caos: nada aconteceu... " + C.RESET)

def calcular_dano_com_raridade(dano_base, ini, j_arma):
    ef = j_arma.get("efeito") if j_arma else None
    def_ini = ini.get("def", 0)
    if ef == "ignorar_def":
        def_ini = def_ini // 2
        dano_base = max(1, int(dano_base + def_ini // 2))
    return dano_base

def mostrar_drop_raridade(nome, raridade):
    r = RARIDADES[raridade]
    return r["cor"] + C.BOLD + r["emoji"] + " " + nome + " [" + raridade + "]" + " " + C.RESET

# ─────────────────────────────────────────
#  DADOS — CLASSES
# ─────────────────────────────────────────
CLASSES = {
    "1":{"nome":"Guerreiro","emoji":"⚔️","cor":C.VERMELHO,
         "hp":130,"mp":40,"atk":20,"defesa":12,"vel":8,
         "desc":"Tanque de aço. Sobrevive a qualquer coisa.",
         "hab_base":["Golpe Brutal","Escudo Total","Furia Berserker"]},
    "2":{"nome":"Mago","emoji":"🔮","cor":C.ROXO,
         "hp":75,"mp":130,"atk":10,"defesa":4,"vel":10,
         "desc":"Dano massivo. Frágil como vidro.",
         "hab_base":["Bola de Fogo","Raio Gelido","Meteoro"]},
    "3":{"nome":"Arqueiro","emoji":"🏹","cor":C.VERDE,
         "hp":100,"mp":75,"atk":16,"defesa":7,"vel":14,
         "desc":"Veloz e preciso. Veneno e críticos.",
         "hab_base":["Flecha Certeira","Chuva de Flechas","Veneno"]},
    "4":{"nome":"Paladino","emoji":"🛡️","cor":C.AMARELO,
         "hp":120,"mp":80,"atk":15,"defesa":15,"vel":7,
         "desc":"Guerreiro sagrado. Cura e dano divino.",
         "hab_base":["Golpe Sagrado","Cura Divina","Juizo Final"]},
    "5":{"nome":"Necromante","emoji":"💀","cor":C.CINZA,
         "hp":85,"mp":110,"atk":13,"defesa":5,"vel":11,
         "desc":"Drena vida, invoca mortos, causa maldições.",
         "hab_base":["Dreno de Vida","Maldição","Exercito dos Mortos"]},
}

HABILIDADES = {
    # Guerreiro
    "Golpe Brutal":     {"custo":15,"tipo":"dano",   "mult":2.2,"desc":"Ataque poderoso"},
    "Escudo Total":     {"custo":20,"tipo":"defesa", "turns":2, "desc":"Escudo por 2 turnos"},
    "Furia Berserker":  {"custo":30,"tipo":"berserk","mult":3.0,"desc":"Dano triplo, -15 HP"},
    "Provocar":         {"custo":10,"tipo":"provocar","turns":3,"desc":"Inimigo ataca menos"},
    "Golpe Devastador": {"custo":40,"tipo":"dano",   "mult":4.0,"desc":"Dano massivo (desbloq.)"},
    "Terremoto":        {"custo":35,"tipo":"dano",   "mult":2.8,"desc":"Atinge e atordoa o inimigo"},
    "Gritar de Guerra": {"custo":15,"tipo":"buff",   "turns":3, "desc":"ATK +40% por 3 turnos"},
    # Mago
    "Bola de Fogo":     {"custo":20,"tipo":"dano",   "mult":2.8,"desc":"Explosão de fogo"},
    "Raio Gelido":      {"custo":25,"tipo":"lento",  "mult":1.8,"desc":"Dano + reduz ATK"},
    "Meteoro":          {"custo":45,"tipo":"dano",   "mult":3.5,"desc":"Dano massivo"},
    "Escudo Arcano":    {"custo":20,"tipo":"defesa", "turns":2, "desc":"Barreira mágica"},
    "Tempestade":       {"custo":50,"tipo":"dano",   "mult":5.0,"desc":"Dano absoluto (desbloq.)"},
    "Congelar":         {"custo":30,"tipo":"lento",  "mult":2.0,"desc":"Paralisa o inimigo por 2 turnos"},
    "Absorver Magia":   {"custo":20,"tipo":"mp",     "efeito":40,"desc":"Rouba 40 MP da batalha"},
    # Arqueiro
    "Flecha Certeira":  {"custo":15,"tipo":"critico","mult":2.0,"desc":"Alta chance critico"},
    "Chuva de Flechas": {"custo":25,"tipo":"dano",   "mult":2.4,"desc":"Multiplos acertos"},
    "Veneno":           {"custo":20,"tipo":"veneno", "mult":1.2,"desc":"Envenena por 3 turnos"},
    "Esquivar":         {"custo":15,"tipo":"evasao", "turns":1, "desc":"Evita proximo ataque"},
    "Flecha Explosiva": {"custo":35,"tipo":"dano",   "mult":3.5,"desc":"Dano em area (desbloq.)"},
    "Rastrear":         {"custo":10,"tipo":"critico","mult":1.5,"desc":"Proximos 2 ataques sao criticos"},
    "Bomba de Fumaca":  {"custo":20,"tipo":"evasao", "turns":2, "desc":"Esquiva por 2 turnos"},
    # Paladino
    "Golpe Sagrado":    {"custo":20,"tipo":"dano_sagrado","mult":2.0,"desc":"Dano + cura 10 HP"},
    "Cura Divina":      {"custo":25,"tipo":"cura",   "efeito":50,"desc":"Cura 50 HP"},
    "Juizo Final":      {"custo":40,"tipo":"dano",   "mult":3.5,"desc":"Dano sagrado massivo"},
    "Benção":           {"custo":15,"tipo":"buff",   "turns":3, "desc":"ATK +30% por 3 turnos"},
    "Ressurreicao":     {"custo":60,"tipo":"reviver","desc":"Revive com 50% HP (desbloq.)"},
    "Martelo Sagrado":  {"custo":25,"tipo":"dano_sagrado","mult":2.5,"desc":"Dano sagrado + cura 20 HP"},
    "Aura Protetora":   {"custo":30,"tipo":"defesa", "turns":3, "desc":"Escudo divino por 3 turnos"},
    # Necromante
    "Dreno de Vida":    {"custo":20,"tipo":"dreno",  "mult":1.8,"desc":"Dano + rouba HP"},
    "Maldição":         {"custo":25,"tipo":"maldição","turns":3,"desc":"Inimigo perde ATK e DEF"},
    "Exercito dos Mortos":{"custo":35,"tipo":"dano", "mult":2.5,"desc":"Invoca esqueletos"},
    "Toque da Morte":   {"custo":30,"tipo":"dano",   "mult":2.0,"desc":"Ignora defesa"},
    "Apocalipse":       {"custo":60,"tipo":"dano",   "mult":4.5,"desc":"Dano lendario (desbloq.)"},
    "Pacto Sombrio":    {"custo":25,"tipo":"dreno",  "mult":2.5,"desc":"Drena 25% do HP inimigo"},
    "Invocar Lorde":    {"custo":40,"tipo":"dano",   "mult":3.5,"desc":"Invoca um Lorde das Trevas"},
}

HAB_DESBLOQUEAVEL = {
    "Guerreiro": [("Provocar",300),("Golpe Devastador",800)],
    "Mago":      [("Escudo Arcano",300),("Tempestade",800)],
    "Arqueiro":  [("Esquivar",300),("Flecha Explosiva",800)],
    "Paladino":  [("Benção",300),("Ressurreicao",800)],
    "Necromante":[("Toque da Morte",300),("Apocalipse",800)],
}

# ─────────────────────────────────────────
#  DADOS — EQUIPAMENTOS
# ─────────────────────────────────────────
ARMAS = [
    {"nome":"Punhos",      "emoji":"👊","atk":0,  "tipo":"todos",      "valor":0,   "tier":0},
    {"nome":"Espada Enf.", "emoji":"⚔️","atk":8,  "tipo":"Guerreiro",  "valor":80,  "tier":1},
    {"nome":"Cajado Mag.", "emoji":"🪄","atk":10, "tipo":"Mago",       "valor":80,  "tier":1},
    {"nome":"Arco Longo",  "emoji":"🏹","atk":7,  "tipo":"Arqueiro",   "valor":80,  "tier":1},
    {"nome":"Martelo Sagr.","emoji":"🔨","atk":9, "tipo":"Paladino",   "valor":80,  "tier":1},
    {"nome":"Foice Negra", "emoji":"⚰️","atk":8,  "tipo":"Necromante", "valor":80,  "tier":1},
    {"nome":"Espada Real", "emoji":"🗡️","atk":18, "tipo":"Guerreiro",  "valor":250, "tier":2},
    {"nome":"Tomo Arcano", "emoji":"📖","atk":22, "tipo":"Mago",       "valor":250, "tier":2},
    {"nome":"Arco Aereo",  "emoji":"💨","atk":17, "tipo":"Arqueiro",   "valor":250, "tier":2},
    {"nome":"Lança Divina","emoji":"✝️","atk":20, "tipo":"Paladino",   "valor":250, "tier":2},
    {"nome":"Coroa Negra", "emoji":"👑","atk":19, "tipo":"Necromante", "valor":250, "tier":2},
    {"nome":"Excalibur",   "emoji":"🌟","atk":35, "tipo":"Guerreiro",  "valor":600, "tier":3},
    {"nome":"Grimorio",    "emoji":"🌀","atk":40, "tipo":"Mago",       "valor":600, "tier":3},
    {"nome":"Arco Lendario","emoji":"⚡","atk":32,"tipo":"Arqueiro",   "valor":600, "tier":3},
    {"nome":"Mjolnir",     "emoji":"⚡","atk":38, "tipo":"Paladino",   "valor":600, "tier":3},
    {"nome":"Cajado Morte","emoji":"☠️","atk":36, "tipo":"Necromante", "valor":600, "tier":3},
]

ARMADURAS = [
    {"nome":"Roupa",       "emoji":"👕","def":0,  "tipo":"todos",      "valor":0,   "tier":0},
    {"nome":"Armad. Couro","emoji":"🦺","def":5,  "tipo":"todos",      "valor":60,  "tier":1},
    {"nome":"Malha de Aco","emoji":"🛡️","def":12, "tipo":"Guerreiro",  "valor":150, "tier":2},
    {"nome":"Manto Arcano","emoji":"🧥","def":6,  "tipo":"Mago",       "valor":150, "tier":2},
    {"nome":"Armad. Escama","emoji":"🐉","def":9, "tipo":"Arqueiro",   "valor":150, "tier":2},
    {"nome":"Placa Sagrada","emoji":"✨","def":14,"tipo":"Paladino",   "valor":150, "tier":2},
    {"nome":"Vestes Mortas","emoji":"💀","def":7, "tipo":"Necromante", "valor":150, "tier":2},
    {"nome":"Armad. Titã", "emoji":"⚔️","def":22, "tipo":"Guerreiro",  "valor":400, "tier":3},
    {"nome":"Manto Estelar","emoji":"🌟","def":14,"tipo":"Mago",       "valor":400, "tier":3},
    {"nome":"Capa Sombria", "emoji":"🌑","def":16,"tipo":"Arqueiro",   "valor":400, "tier":3},
    {"nome":"Aegis Divina", "emoji":"🔱","def":25,"tipo":"Paladino",   "valor":400, "tier":3},
    {"nome":"Sudario Negro","emoji":"⚰️","def":18,"tipo":"Necromante", "valor":400, "tier":3},
]

# ─────────────────────────────────────────
#  DADOS — INIMIGOS E CHEFES
# ─────────────────────────────────────────
INIMIGOS = {
    "floresta":[
        {"nome":"Goblin",        "emoji":"👺","hp":45, "atk":9, "def":2,"xp":25,"gold":12},
        {"nome":"Lobo Sombrio",  "emoji":"🐺","hp":60, "atk":13,"def":4,"xp":32,"gold":16},
        {"nome":"Bandido",       "emoji":"🗡️","hp":70, "atk":15,"def":5,"xp":38,"gold":22},
        {"nome":"Planta Carnivora","emoji":"🌿","hp":55,"atk":11,"def":3,"xp":28,"gold":14},
    ],
    "caverna":[
        {"nome":"Troll",         "emoji":"🧌","hp":100,"atk":20,"def":9, "xp":60,"gold":35},
        {"nome":"Morcego Gigante","emoji":"🦇","hp":80, "atk":17,"def":6, "xp":48,"gold":28},
        {"nome":"Esqueleto",     "emoji":"💀","hp":90, "atk":22,"def":11,"xp":65,"gold":38},
        {"nome":"Minotauro",     "emoji":"🐂","hp":120,"atk":25,"def":12,"xp":80,"gold":45},
    ],
    "torre":[
        {"nome":"Golem de Pedra","emoji":"🪨","hp":150,"atk":25,"def":18,"xp":95, "gold":60},
        {"nome":"Demonio Menor", "emoji":"😈","hp":130,"atk":28,"def":14,"xp":100,"gold":65},
        {"nome":"Espectro",      "emoji":"👻","hp":110,"atk":30,"def":10,"xp":90, "gold":55},
    ],
    "abismo":[
        {"nome":"Demonio Maior", "emoji":"🔥","hp":200,"atk":38,"def":22,"xp":150,"gold":100},
        {"nome":"Lich",          "emoji":"🧙","hp":180,"atk":42,"def":18,"xp":160,"gold":110},
        {"nome":"Behemoth",      "emoji":"🦕","hp":250,"atk":35,"def":28,"xp":170,"gold":120},
    ],
    "fortaleza":[
        {"nome":"Cavaleiro Negro","emoji":"🖤","hp":300,"atk":50,"def":30,"xp":220,"gold":160},
        {"nome":"Dragao Anciao", "emoji":"🐲","hp":350,"atk":55,"def":35,"xp":250,"gold":180},
        {"nome":"Arcanista Sombrio","emoji":"🌑","hp":280,"atk":58,"def":25,"xp":230,"gold":170},
    ],
    "pantano":[
        {"nome":"Zumbi",         "emoji":"🧟","hp":55, "atk":10,"def":2,"xp":28,"gold":13},
        {"nome":"Serpente Negra","emoji":"🐍","hp":65, "atk":14,"def":3,"xp":35,"gold":18},
        {"nome":"Bruxa do Lodo", "emoji":"🧙","hp":75, "atk":16,"def":5,"xp":42,"gold":22},
        {"nome":"Hidrinha",      "emoji":"🐊","hp":90, "atk":18,"def":7,"xp":50,"gold":28},
    ],
    "ruinas":[
        {"nome":"Pedra Animada", "emoji":"🪨","hp":70, "atk":13,"def":8,"xp":38,"gold":20},
        {"nome":"Fantasma Antigo","emoji":"👻","hp":60,"atk":17,"def":3,"xp":40,"gold":22},
        {"nome":"Guardiao Roto", "emoji":"🤖","hp":85, "atk":15,"def":10,"xp":48,"gold":25},
    ],
    "minas":[
        {"nome":"Mineiro Morto",  "emoji":"⛏️","hp":80,"atk":19,"def":8,"xp":50,"gold":30},
        {"nome":"Verme Gigante",  "emoji":"🪱","hp":95,"atk":21,"def":6,"xp":58,"gold":32},
        {"nome":"Golem de Ouro",  "emoji":"🏅","hp":110,"atk":23,"def":14,"xp":68,"gold":45},
    ],
    "cemiterio":[
        {"nome":"Lich Menor",     "emoji":"💀","hp":100,"atk":24,"def":10,"xp":70,"gold":40},
        {"nome":"Banshee",        "emoji":"👻","hp":85, "atk":28,"def":6, "xp":65,"gold":38},
        {"nome":"Cavaleiro Morto","emoji":"🖤","hp":120,"atk":26,"def":15,"xp":80,"gold":48},
    ],
    "vulcao":[
        {"nome":"Elemental de Fogo","emoji":"🔥","hp":220,"atk":40,"def":18,"xp":140,"gold":90},
        {"nome":"Demonio de Lava",  "emoji":"🌋","hp":250,"atk":44,"def":22,"xp":160,"gold":105},
        {"nome":"Dragao de Magma",  "emoji":"🐉","hp":280,"atk":48,"def":25,"xp":180,"gold":120},
    ],
}

CHEFES = [
    {"nome":"Rei Goblin",     "emoji":"👑","fases":[
        {"hp":200,"atk":22,"def":8, "fala":"Vou esmagar seus ossos!","especial":"Grito de Guerra","mult_esp":1.8},
        {"hp":200,"atk":30,"def":12,"fala":"CHEGA! MODO BERSERK!",  "especial":"Furia Total",    "mult_esp":2.5},
    ],"xp":200,"gold":120,"area":"floresta"},

    {"nome":"Dragao das Sombras","emoji":"🐉","fases":[
        {"hp":350,"atk":38,"def":20,"fala":"Mortais tolos!",          "especial":"Bafo de Fogo",  "mult_esp":2.0},
        {"hp":350,"atk":50,"def":25,"fala":"Minha ira verdadeira...", "especial":"Inferno Total", "mult_esp":3.0},
        {"hp":350,"atk":60,"def":30,"fala":"PODER ABSOLUTO!",         "especial":"Caos Dragônico","mult_esp":4.0},
    ],"xp":400,"gold":300,"area":"caverna"},

    {"nome":"Senhor da Torre",  "emoji":"🗼","fases":[
        {"hp":400,"atk":45,"def":28,"fala":"Esta torre é minha!",     "especial":"Raio da Torre", "mult_esp":2.2},
        {"hp":400,"atk":58,"def":35,"fala":"Impossivel...",           "especial":"Colapso",       "mult_esp":3.2},
    ],"xp":500,"gold":400,"area":"torre"},

    {"nome":"Abominacao",       "emoji":"👾","fases":[
        {"hp":500,"atk":55,"def":32,"fala":"Você não deveria ter vindo...","especial":"Tentaculos","mult_esp":2.5},
        {"hp":500,"atk":68,"def":40,"fala":"TRANSFORMAÇÃO!",          "especial":"Mutação Caótica","mult_esp":3.5},
        {"hp":500,"atk":80,"def":45,"fala":"FORMA FINAL!",            "especial":"Apocalipse",    "mult_esp":5.0},
    ],"xp":700,"gold":600,"area":"abismo"},

    {"nome":"Bruxa Suprema",    "emoji":"🧙","fases":[
        {"hp":220,"atk":25,"def":10,"fala":"Voce nao pertence ao pantano!","especial":"Maldição do Lodo","mult_esp":2.0},
        {"hp":220,"atk":35,"def":18,"fala":"Meu poder verdadeiro!",        "especial":"Chuva de Veneno","mult_esp":3.0},
    ],"xp":280,"gold":180,"area":"pantano"},
    {"nome":"Guardiao das Ruinas","emoji":"🏛️","fases":[
        {"hp":260,"atk":28,"def":20,"fala":"Intruso! As ruinas sao sagradas!","especial":"Colapso","mult_esp":2.2},
        {"hp":260,"atk":40,"def":28,"fala":"DESPERTAR TOTAL!",               "especial":"Terremoto","mult_esp":3.2},
    ],"xp":300,"gold":200,"area":"ruinas"},
    {"nome":"Rei das Minas",     "emoji":"⛏️","fases":[
        {"hp":300,"atk":32,"def":22,"fala":"Essas minas sao minhas!","especial":"Explosao de Minério","mult_esp":2.3},
        {"hp":300,"atk":45,"def":30,"fala":"COLAPSE TUDO!",          "especial":"Desmoronamento",    "mult_esp":3.5},
    ],"xp":320,"gold":220,"area":"minas"},
    {"nome":"Senhor dos Mortos", "emoji":"⚰️","fases":[
        {"hp":350,"atk":38,"def":25,"fala":"Todos morrem aqui...",    "especial":"Exercito dos Mortos","mult_esp":2.5},
        {"hp":350,"atk":52,"def":35,"fala":"EU SOU A MORTE!",         "especial":"Apocalipse Morto",  "mult_esp":4.0},
    ],"xp":380,"gold":260,"area":"cemiterio"},
    {"nome":"Titan do Vulcao",   "emoji":"🌋","fases":[
        {"hp":420,"atk":50,"def":30,"fala":"Sua carne vai derreter!","especial":"Erupcao",     "mult_esp":2.8},
        {"hp":420,"atk":65,"def":42,"fala":"FOGO ETERNO!",           "especial":"Mare de Lava","mult_esp":4.2},
        {"hp":420,"atk":80,"def":55,"fala":"EXPLOSAO FINAL!",        "especial":"Supernova",  "mult_esp":6.0},
    ],"xp":550,"gold":450,"area":"vulcao"},
    {"nome":"Senhor das Trevas","emoji":"☠️","fases":[
        {"hp":600,"atk":65,"def":40,"fala":"Você ousou chegar até aqui...","especial":"Maldição das Trevas","mult_esp":2.5},
        {"hp":600,"atk":80,"def":50,"fala":"Impossivel! Mais poder!","especial":"Noite Eterna",   "mult_esp":3.8},
        {"hp":600,"atk":100,"def":60,"fala":"EU SOU A ESCURIDÃO!",   "especial":"Extinção",       "mult_esp":6.0},
    ],"xp":1000,"gold":1000,"area":"fortaleza"},
]

MAPA = {
    "floresta":  {"nome":"Floresta Sombria",    "emoji":"🌲","desc":"Arvores antigas escondem perigos...",        "prox":["caverna","pantano"],"bat":3},
    "pantano":   {"nome":"Pantano Maldito",      "emoji":"🌿","desc":"Agua negra e criaturas podres por toda parte.","prox":["caverna","ruinas"],"bat":3},
    "ruinas":    {"nome":"Ruinas Esquecidas",    "emoji":"🏛️","desc":"Cidade antiga tomada por monstros.",          "prox":["caverna"],"bat":3},
    "caverna":   {"nome":"Caverna do Abismo",    "emoji":"🪨","desc":"O cheiro de enxofre e insuportavel.",         "prox":["torre","minas"],"bat":3},
    "minas":     {"nome":"Minas Profundas",      "emoji":"⛏️","desc":"Ouro e perigo em igual medida.",              "prox":["torre"],"bat":3},
    "torre":     {"nome":"Torre das Trevas",     "emoji":"🗼","desc":"Energia maligna pulsa nas pedras.",           "prox":["abismo","cemiterio"],"bat":3},
    "cemiterio": {"nome":"Cemiterio dos Herois", "emoji":"⚰️","desc":"Ate herois caem aqui.",                       "prox":["abismo"],"bat":3},
    "abismo":    {"nome":"Abismo Eterno",        "emoji":"🌑","desc":"Aqui a luz nao existe mais.",                 "prox":["fortaleza","vulcao"],"bat":3},
    "vulcao":    {"nome":"Vulcao do Fim",        "emoji":"🌋","desc":"Lava e demônios por todo lado.",              "prox":["fortaleza"],"bat":3},
    "fortaleza": {"nome":"Fortaleza das Trevas", "emoji":"🏰","desc":"O lar do Senhor das Trevas.",                 "prox":[],"bat":3},
}

DROPS_AREA = {
    "floresta":  [("Pocao Pequena",0.40),("Eter Pequeno",0.25),("Antidoto",0.20)],
    "pantano":   [("Antidoto",0.50),("Pocao Pequena",0.30),("Eter Pequeno",0.20)],
    "ruinas":    [("Pocao Media",0.35),("Pedra Magica",0.20),("Eter Medio",0.20)],
    "caverna":   [("Pocao Media",  0.35),("Eter Medio",  0.25),("Pedra Magica",0.15)],
    "minas":     [("Pocao Media",0.30),("Pedra Magica",0.30),("Eter Medio",0.20)],
    "torre":     [("Pocao Grande", 0.30),("Eter Grande",  0.20),("Elixir Menor",0.12)],
    "cemiterio": [("Pocao Grande",0.25),("Eter Grande",0.20),("Elixir Menor",0.15)],
    "abismo":    [("Elixir Menor", 0.30),("Eter Grande",  0.20),("Pedra do Caos",0.15)],
    "vulcao":    [("Elixir Menor",0.30),("Pedra do Caos",0.25),("Eter Supremo",0.15)],
    "fortaleza": [("Elixir",       0.35),("Eter Supremo", 0.25),("Pedra Lendaria",0.15)],
}

ITENS = {
    "Pocao Pequena": {"emoji":"🧪","tipo":"cura","efeito":35,"desc":"Restaura 35 HP","valor":25},
    "Pocao Media":   {"emoji":"🧪","tipo":"cura","efeito":70,"desc":"Restaura 70 HP","valor":55},
    "Pocao Grande":  {"emoji":"⚗️","tipo":"cura","efeito":130,"desc":"Restaura 130 HP","valor":100},
    "Eter Pequeno":  {"emoji":"💧","tipo":"mp",  "efeito":30,"desc":"Restaura 30 MP","valor":30},
    "Eter Medio":    {"emoji":"💧","tipo":"mp",  "efeito":60,"desc":"Restaura 60 MP","valor":60},
    "Eter Grande":   {"emoji":"💧","tipo":"mp",  "efeito":100,"desc":"Restaura 100 MP","valor":90},
    "Eter Supremo":  {"emoji":"💦","tipo":"mp",  "efeito":200,"desc":"Restaura 200 MP","valor":150},
    "Antidoto":      {"emoji":"🌿","tipo":"cura_v","efeito":0,"desc":"Cura veneno","valor":20},
    "Elixir Menor":  {"emoji":"✨","tipo":"tudo","efeito":150,"desc":"HP+MP +150","valor":200},
    "Elixir":        {"emoji":"🌟","tipo":"tudo","efeito":9999,"desc":"HP+MP totais","valor":500},
    "Pedra Magica":  {"emoji":"💎","tipo":"mp",  "efeito":80, "desc":"Restaura 80 MP","valor":80},
    "Pedra do Caos": {"emoji":"🔮","tipo":"cura","efeito":200,"desc":"Restaura 200 HP","valor":200},
    "Pedra Lendaria":{"emoji":"⚡","tipo":"tudo","efeito":9999,"desc":"HP+MP totais","valor":800},
}




# ─────────────────────────────────────────
#  MAGIAS PASSIVAS POR CLASSE
# ─────────────────────────────────────────
PASSIVAS = {
    "Guerreiro": [
        {"id":"sede_de_sangue", "nome":"Sede de Sangue",
         "desc":"Cada ataque tem 20% de chance de regenerar 8 HP",
         "gatilho":"pos_ataque",
         "efeito": lambda j,dano,ini,log: (
             setattr(j,"hp",min(j.hp_max,j.hp+8)),
             log.append(C.VERDE+"  [Passiva] Sede de Sangue: +8 HP "+C.RESET)
         ) if random.random()<0.20 else None},
        {"id":"pele_de_aco",  "nome":"Pele de Aco",
         "desc":"Reduz todo dano recebido em 3 pontos fixos",
         "gatilho":"pre_dano",
         "efeito": lambda dano: max(1, dano-3)},
        {"id":"ultimo_recurso","nome":"Ultimo Recurso",
         "desc":"Quando HP < 20%, ATK dobra automaticamente",
         "gatilho":"turno",
         "efeito": lambda j,log: log.append(
             C.VERMELHO+C.BOLD+"  [Passiva] Ultimo Recurso ATIVO! ATK dobrado! "+C.RESET
         ) if j.hp/max(j.hp_max,1)<0.20 else None},
    ],
    "Mago": [
        {"id":"escudo_arcano_p","nome":"Escudo Arcano",
         "desc":"15% chance de refletir 30% do dano recebido",
         "gatilho":"pre_dano",
         "efeito": lambda dano,ini,log: (
             ini.__setitem__("hp_atual", ini["hp_atual"]-int(dano*0.30)),
             log.append(C.ROXO+"  [Passiva] Escudo Arcano refletiu "+str(int(dano*0.30))+" dano! "+C.RESET)
         ) if random.random()<0.15 else None},
        {"id":"mana_infinita",  "nome":"Mana Infinita",
         "desc":"Regenera 3 MP por turno automaticamente",
         "gatilho":"turno",
         "efeito": lambda j,log: (
             setattr(j,"mp",min(j.mp_max,j.mp+3)),
             log.append(C.AZUL+"  [Passiva] Mana Infinita: +3 MP "+C.RESET)
         ) if j.mp<j.mp_max else None},
        {"id":"sobrecarga",    "nome":"Sobrecarga",
         "desc":"Quando MP > 80%, magias causam +25% de dano",
         "gatilho":"multiplicador",
         "efeito": lambda j: 1.25 if j.mp/max(j.mp_max,1)>0.80 else 1.0},
    ],
    "Arqueiro": [
        {"id":"olho_de_aguia", "nome":"Olho de Aguia",
         "desc":"Chance de critico aumenta +10% permanentemente",
         "gatilho":"critico",
         "efeito": lambda: 0.10},
        {"id":"fluxo",         "nome":"Fluxo",
         "desc":"Cada critico consecutivo aumenta o proximo em +5%",
         "gatilho":"critico_chain",
         "efeito": None},  # tratado no loop
        {"id":"veneno_passivo","nome":"Veneno Passivo",
         "desc":"Todo ataque tem 15% de chance de envenenar",
         "gatilho":"pos_ataque",
         "efeito": lambda j,dano,ini,log: (
             ini.__setitem__("veneno_turns", max(ini.get("veneno_turns",0),2)),
             log.append(C.VERDE+"  [Passiva] Veneno Passivo aplicado! "+C.RESET)
         ) if random.random()<0.15 else None},
    ],
    "Paladino": [
        {"id":"aura_sagrada",  "nome":"Aura Sagrada",
         "desc":"Regenera 5 HP por turno passivamente",
         "gatilho":"turno",
         "efeito": lambda j,log: (
             setattr(j,"hp",min(j.hp_max,j.hp+5)),
             log.append(C.AMARELO+"  [Passiva] Aura Sagrada: +5 HP "+C.RESET)
         ) if j.hp<j.hp_max else None},
        {"id":"escudo_da_fe",  "nome":"Escudo da Fe",
         "desc":"20% chance de bloquear completamente um ataque",
         "gatilho":"pre_dano",
         "efeito": lambda dano,ini,log: (
             log.append(C.AMARELO+"  [Passiva] Escudo da Fe bloqueou o ataque! "+C.RESET),
             0
         ) if random.random()<0.20 else None},
        {"id":"martir",        "nome":"Martir",
         "desc":"Quando HP < 30%, cura 20 HP ao receber dano",
         "gatilho":"pre_dano",
         "efeito": lambda j,dano,log: (
             setattr(j,"hp",min(j.hp_max,j.hp+20)),
             log.append(C.AMARELO+"  [Passiva] Martir: +20 HP! "+C.RESET)
         ) if j.hp/max(j.hp_max,1)<0.30 else None},
    ],
    "Necromante": [
        {"id":"aura_da_morte", "nome":"Aura da Morte",
         "desc":"Todo turno, 15% chance de reduzir ATK do inimigo",
         "gatilho":"turno_ini",
         "efeito": lambda ini,log: (
             ini.__setitem__("atk_red", ini.get("atk_red",0)+1),
             log.append(C.CINZA+"  [Passiva] Aura da Morte enfraqueceu o inimigo! "+C.RESET)
         ) if random.random()<0.15 else None},
        {"id":"pacto_de_sangue","nome":"Pacto de Sangue",
         "desc":"Ao matar um inimigo, recupera 15% do HP max",
         "gatilho":"pos_vitoria",
         "efeito": lambda j,log: (
             setattr(j,"hp",min(j.hp_max,j.hp+int(j.hp_max*0.15))),
             log.append(C.CINZA+"  [Passiva] Pacto de Sangue: +"+str(int(j.hp_max*0.15))+" HP! "+C.RESET)
         )},
        {"id":"corpo_de_lich", "nome":"Corpo de Lich",
         "desc":"Reduz todo dano recebido em 10%",
         "gatilho":"pre_dano",
         "efeito": lambda dano: max(1,int(dano*0.90))},
    ],
}

def aplicar_passivas_turno(j, ini, log):
    """Aplica passivas com gatilho 'turno' e 'turno_ini' a cada turno."""
    passivas = PASSIVAS.get(j.classe, [])
    for p in passivas:
        try:
            if p["gatilho"]=="turno" and p["efeito"]:
                p["efeito"](j, log)
            elif p["gatilho"]=="turno_ini" and p["efeito"]:
                p["efeito"](ini, log)
        except: pass

def aplicar_passiva_pre_dano(j, ini, dano, log):
    """Aplica passivas de redução de dano. Retorna dano modificado."""
    passivas = PASSIVAS.get(j.classe, [])
    for p in passivas:
        try:
            if p["gatilho"]=="pre_dano" and p["efeito"]:
                res = p["efeito"](dano, ini, log) if p["id"] in ("escudo_arcano_p",) else                       p["efeito"](dano, log) if p["id"] in ("escudo_da_fe","martir") else                       p["efeito"](j,dano,log) if p["id"]=="martir" else                       p["efeito"](dano)
                if isinstance(res, int) and res>=0:
                    dano = res
        except: pass
    return dano

def aplicar_passiva_pos_ataque(j, ini, dano, log):
    """Aplica passivas após atacar (vampirismo, veneno, etc)."""
    passivas = PASSIVAS.get(j.classe, [])
    for p in passivas:
        try:
            if p["gatilho"]=="pos_ataque" and p["efeito"]:
                p["efeito"](j, dano, ini, log)
        except: pass

def bonus_critico_passiva(j):
    """Retorna bônus de crítico das passivas."""
    passivas = PASSIVAS.get(j.classe, [])
    bonus = 0
    for p in passivas:
        try:
            if p["gatilho"]=="critico" and p["efeito"]:
                bonus += p["efeito"]()
        except: pass
    return bonus

def bonus_dano_passiva(j):
    """Retorna multiplicador de dano das passivas (ex: Sobrecarga do Mago)."""
    passivas = PASSIVAS.get(j.classe, [])
    mult = 1.0
    for p in passivas:
        try:
            if p["gatilho"]=="multiplicador" and p["efeito"]:
                mult *= p["efeito"](j)
        except: pass
    return mult

def mostrar_passivas(j):
    limpar(); titulo("MAGIAS PASSIVAS","🔮",C.ROXO)
    passivas = PASSIVAS.get(j.classe, [])
    print(C.CINZA+"  Passivas de "+j.classe+":\n"+C.RESET)
    for p in passivas:
        print("  "+C.ROXO+C.BOLD+p["nome"]+C.RESET)
        print(C.CINZA+"  "+p["desc"]+" "+C.RESET)
        print()
    pausar()
# ─────────────────────────────────────────
#  SISTEMA DE SUMMONS
# ─────────────────────────────────────────
SUMMONS_DEF = {
    # ── Guerreiro ──
    "Escudeiro":   {"emoji":"🛡️","classe":"Guerreiro","custo_mp":25,"turns":3,
                    "tipo":"tank",   "desc":"Absorve 30% do proximo dano recebido",
                    "cor":C.VERMELHO},
    "Cavaleiro":   {"emoji":"⚔️","classe":"Guerreiro","custo_mp":35,"turns":3,
                    "tipo":"ataque", "poder":(15,30),"desc":"Ataca o inimigo (15-30 dano/turno)",
                    "cor":C.VERMELHO},
    "Titan":       {"emoji":"🗿","classe":"Guerreiro","custo_mp":50,"turns":4,
                    "tipo":"tank_forte","desc":"Absorve 60% do dano e contra-ataca",
                    "poder":(10,20),"cor":C.VERMELHO},

    # ── Mago ──
    "Elemental":   {"emoji":"🌊","classe":"Mago","custo_mp":30,"turns":3,
                    "tipo":"ataque", "poder":(20,35),"desc":"Ataque elemental (20-35 dano/turno)",
                    "cor":C.ROXO},
    "Golem Arcano":{"emoji":"💎","classe":"Mago","custo_mp":40,"turns":3,
                    "tipo":"debuff", "desc":"Reduz ATK e DEF do inimigo por turno",
                    "cor":C.ROXO},
    "Fenix Arcana":{"emoji":"🔥","classe":"Mago","custo_mp":55,"turns":4,
                    "tipo":"cura",   "poder":(15,25),"desc":"Cura 15-25 HP/turno e ataca",
                    "cor":C.ROXO},

    # ── Arqueiro ──
    "Lobo da Caça":{"emoji":"🐺","classe":"Arqueiro","custo_mp":25,"turns":3,
                    "tipo":"ataque", "poder":(12,22),"desc":"Ataca rapido (12-22 dano/turno)",
                    "cor":C.VERDE},
    "Aguia":       {"emoji":"🦅","classe":"Arqueiro","custo_mp":30,"turns":3,
                    "tipo":"critico","poder":(18,28),"desc":"Alta chance de critico (18-28 dano)",
                    "cor":C.VERDE},
    "Enxame":      {"emoji":"🐝","classe":"Arqueiro","custo_mp":40,"turns":4,
                    "tipo":"veneno_sum","desc":"Envenena o inimigo todo turno",
                    "cor":C.VERDE},

    # ── Paladino ──
    "Anjo Guardiao":{"emoji":"😇","classe":"Paladino","custo_mp":35,"turns":3,
                     "tipo":"cura",   "poder":(20,35),"desc":"Cura 20-35 HP/turno",
                     "cor":C.AMARELO},
    "Serafim":     {"emoji":"✨","classe":"Paladino","custo_mp":45,"turns":3,
                    "tipo":"tank_sagrado","poder":(10,20),"desc":"Absorve dano e cura o jogador",
                    "cor":C.AMARELO},
    "Lorde Sagrado":{"emoji":"👼","classe":"Paladino","custo_mp":60,"turns":4,
                     "tipo":"ataque_sagrado","poder":(25,45),"desc":"Dano sagrado massivo/turno",
                     "cor":C.AMARELO},

    # ── Necromante ──
    "Esqueleto":   {"emoji":"💀","classe":"Necromante","custo_mp":20,"turns":3,
                    "tipo":"ataque", "poder":(10,18),"desc":"Ataque basico (10-18 dano/turno)",
                    "cor":C.CINZA},
    "Lich":        {"emoji":"🧙","classe":"Necromante","custo_mp":40,"turns":3,
                    "tipo":"dreno_sum","poder":(15,25),"desc":"Drena HP do inimigo para voce",
                    "cor":C.CINZA},
    "Lorde das Trevas":{"emoji":"👑","classe":"Necromante","custo_mp":60,"turns":4,
                        "tipo":"caos_sum","poder":(20,40),"desc":"Ataca, envenena e debuffa/turno",
                        "cor":C.CINZA},
}

SUMMONS_POR_CLASSE = {
    "Guerreiro":  ["Escudeiro","Cavaleiro","Titan"],
    "Mago":       ["Elemental","Golem Arcano","Fenix Arcana"],
    "Arqueiro":   ["Lobo da Caça","Aguia","Enxame"],
    "Paladino":   ["Anjo Guardiao","Serafim","Lorde Sagrado"],
    "Necromante": ["Esqueleto","Lich","Lorde das Trevas"],
}

def agir_summon(s, j, ini, log):
    """Age um summon ativo por turno. Retorna False se expirou."""
    s["turns_restantes"] -= 1
    nome  = s["nome"]  # nome é a chave do SUMMONS_DEF, não um campo interno
    d = SUMMONS_DEF.get(nome, {})
    if not d: return False
    tipo  = d["tipo"]
    emoji = d["emoji"]
    cor_s = d["cor"]
    poder = d.get("poder", (10,20))

    if tipo == "ataque":
        dano = random.randint(*poder)
        ini["hp_atual"] -= dano
        log.append(cor_s+"  "+emoji+" "+nome+": "+str(dano)+" de dano! "+C.RESET)

    elif tipo == "critico":
        crit = random.random() < 0.45
        dano = random.randint(*poder) * (2 if crit else 1)
        ini["hp_atual"] -= dano
        log.append(cor_s+"  "+emoji+" "+nome+("  CRITICO!" if crit else "")+"! "+str(dano)+" dano. "+C.RESET)

    elif tipo == "cura":
        c = min(random.randint(*poder), j.hp_max - j.hp)
        j.hp += c
        log.append(cor_s+"  "+emoji+" "+nome+": +"+str(c)+" HP curado! "+C.RESET)

    elif tipo == "tank":
        s["tank_ativo"] = True
        log.append(cor_s+"  "+emoji+" "+nome+": protegendo (absorve 30% do dano)! "+C.RESET)

    elif tipo == "tank_forte":
        s["tank_ativo"] = True
        dano_c = random.randint(*poder)
        ini["hp_atual"] -= dano_c
        log.append(cor_s+"  "+emoji+" "+nome+": protegendo e contra-atacando! "+str(dano_c)+" dano. "+C.RESET)

    elif tipo == "tank_sagrado":
        s["tank_ativo"] = True
        c = min(random.randint(*poder), j.hp_max - j.hp)
        j.hp += c
        log.append(cor_s+"  "+emoji+" "+nome+": escudo sagrado +"+str(c)+" HP! "+C.RESET)

    elif tipo == "debuff":
        ini["atk_red"] = ini.get("atk_red", 0) + 1
        ini["maldito"] = ini.get("maldito", 0) + 1
        log.append(cor_s+"  "+emoji+" "+nome+": ATK e DEF do inimigo reduzidos! "+C.RESET)

    elif tipo == "veneno_sum":
        if ini.get("veneno_turns", 0) < 3:
            ini["veneno_turns"] = 3
            log.append(cor_s+"  "+emoji+" "+nome+": inimigo envenenado! "+C.RESET)
        else:
            dano = random.randint(8, 15)
            ini["hp_atual"] -= dano
            log.append(cor_s+"  "+emoji+" "+nome+": "+str(dano)+" dano de veneno! "+C.RESET)

    elif tipo == "dreno_sum":
        dano = random.randint(*poder)
        ini["hp_atual"] -= dano
        roubo = min(dano // 2, j.hp_max - j.hp)
        j.hp += roubo
        log.append(cor_s+"  "+emoji+" "+nome+": drena "+str(dano)+" dano, +"+str(roubo)+" HP! "+C.RESET)

    elif tipo == "ataque_sagrado":
        dano = random.randint(*poder)
        ini["hp_atual"] -= dano
        c = min(10, j.hp_max - j.hp)
        j.hp += c
        log.append(cor_s+"  "+emoji+" "+nome+": "+str(dano)+" dano sagrado +"+str(c)+" HP! "+C.RESET)

    elif tipo == "fenix_arcana" or (tipo == "cura" and "poder" in d):
        dano = random.randint(*poder)
        ini["hp_atual"] -= dano
        c = min(random.randint(*poder) // 2, j.hp_max - j.hp)
        j.hp += c
        log.append(cor_s+"  "+emoji+" "+nome+": "+str(dano)+" dano +"+str(c)+" HP! "+C.RESET)

    elif tipo == "caos_sum":
        dano = random.randint(*poder)
        ini["hp_atual"] -= dano
        ini["veneno_turns"] = max(ini.get("veneno_turns", 0), 2)
        ini["atk_red"] = ini.get("atk_red", 0) + 1
        log.append(cor_s+"  "+emoji+" "+nome+": "+str(dano)+" dano + veneno + debuff! "+C.RESET)

    if s["turns_restantes"] <= 0:
        log.append(C.CINZA+"  "+emoji+" "+nome+" expirou e retornou. "+C.RESET)
        return False
    return True

def agir_todos_summons(j, ini, log):
    """Age todos os summons ativos. Remove os expirados."""
    j.summons_ativos = [s for s in j.summons_ativos if agir_summon(s, j, ini, log)]

def summon_absorve_dano(j, dano):
    """Se tem tank ativo, absorve parte do dano."""
    for s in j.summons_ativos:
        d = SUMMONS_DEF[s["nome"]]
        if s.get("tank_ativo"):
            s["tank_ativo"] = False
            if d["tipo"] == "tank":
                absorvido = int(dano * 0.30)
            elif d["tipo"] == "tank_forte":
                absorvido = int(dano * 0.60)
            elif d["tipo"] == "tank_sagrado":
                absorvido = int(dano * 0.40)
            else:
                absorvido = 0
            return max(0, dano - absorvido), absorvido
    return dano, 0

def menu_summons(j):
    disponiveis = SUMMONS_POR_CLASSE.get(j.classe, [])
    while True:
        limpar(); titulo("SUMMONS","🔮",C.ROXO)
        print(C.LARANJA+"  MP: "+str(j.mp)+"/"+str(j.mp_max)+" "+C.RESET)
        if j.summons_ativos:
            print(C.VERDE+"  Ativos: "+", ".join(
                s["emoji"]+" "+s["nome"]+" ("+str(s["turns_restantes"])+"t)"
                for s in j.summons_ativos)+" "+C.RESET)
        else:
            print(C.CINZA+"  Nenhum summon ativo."+C.RESET)
        print()
        for i, nome in enumerate(disponiveis, 1):
            d = SUMMONS_DEF[nome]
            cor_mp = C.AZUL if j.mp >= d["custo_mp"] else C.CINZA
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+d["cor"]+d["emoji"]+" "+nome+C.RESET+
                  "  "+cor_mp+"["+str(d["custo_mp"])+" MP]"+C.RESET+
                  "  "+C.CINZA+d["desc"]+" ("+str(d["turns"])+" turnos)"+C.RESET)
        print()
        print("  "+C.CINZA+"0  Voltar"+C.RESET+"\n")
        esc = input(C.AMARELO+"  Invocar: "+C.RESET).strip()
        if esc == "0": break
        try:
            idx = int(esc) - 1
            nome = disponiveis[idx]
            d = SUMMONS_DEF[nome]
            if j.mp < d["custo_mp"]:
                print(C.VERMELHO+"\n  MP insuficiente! "+C.RESET); pausar(); continue
            j.mp -= d["custo_mp"]
            j.total_summons += 1
            j.summons_ativos.append({
                "nome": nome, "emoji": d["emoji"],
                "turns_restantes": d["turns"], "tank_ativo": False
            })
            print(d["cor"]+C.BOLD+"\n  "+d["emoji"]+" "+nome+" invocado por "+str(d["turns"])+" turnos! "+C.RESET)
            pausar()
        except:
            print(C.VERMELHO+"\n  Invalido! "+C.RESET); pausar()


# ─────────────────────────────────────────
#  SAVE / LOAD
# ─────────────────────────────────────────
import json, os as _os

SAVE_FILE = "rpg2_save.json"

def salvar_jogo(j, areas):
    dados = {
        "nome": j.nome, "classe": j.classe,
        "nivel": j.nivel, "xp": j.xp, "gold": j.gold,
        "hp": j.hp, "hp_max": j.hp_max,
        "mp": j.mp, "mp_max": j.mp_max,
        "atk_base": j.atk_base, "defesa_base": j.defesa_base,
        "habilidades": j.habilidades,
        "inventario": j.inventario,
        "arma": j.arma, "armadura": j.armadura,
        "vitorias": j.vitorias, "chefes": j.chefes,
        "conquistas": list(j.conquistas),
        "titulos": list(j.titulos),
        "titulo_ativo": j.titulo_ativo,
        "quests_concluidas": list(j.quests_concluidas),
        "quests_notificadas": list(j.quests_notificadas),
        "reputacao": j.reputacao,
        "karma": j.karma,
        "historias_vistas": list(j.historias_vistas),
        "arena_recorde": j.arena_recorde,
        "dungeon_recorde": j.dungeon_recorde,
        "derrotou_bobafat": j.derrotou_bobafat,
        "derrotou_conceito": j.derrotou_conceito,
        "total_summons": j.total_summons,
        "areas_visitadas": list(j.areas_visitadas),
        "crafts": j.crafts,
        "areas_desbloqueadas": areas,
        "pet": j.pet,
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(C.VERMELHO+"  Erro ao salvar: "+str(e)+" "+C.RESET)
        return False

def carregar_jogo():
    if not _os.path.exists(SAVE_FILE):
        return None, None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        # Restrói jogador
        cls_id = next((k for k,v in CLASSES.items() if v["nome"]==d["classe"]), "1")
        j = Jogador(d["nome"], cls_id)
        j.nivel=d["nivel"]; j.xp=d["xp"]; j.gold=d["gold"]
        j.hp=d["hp"]; j.hp_max=d["hp_max"]
        j.mp=d["mp"]; j.mp_max=d["mp_max"]
        j.atk_base=d["atk_base"]; j.defesa_base=d["defesa_base"]
        j.habilidades=d["habilidades"]
        j.inventario=d["inventario"]
        j.arma=d["arma"]; j.armadura=d["armadura"]
        j.vitorias=d["vitorias"]; j.chefes=d["chefes"]
        j.conquistas=set(d["conquistas"])
        j.titulos=set(d["titulos"])
        j.titulo_ativo=d.get("titulo_ativo")
        j.quests_concluidas=set(d["quests_concluidas"])
        j.quests_notificadas=set(d["quests_notificadas"])
        j.reputacao=d["reputacao"]
        j.karma=d.get("karma",0)
        j.historias_vistas=set(d.get("historias_vistas",[]))
        j.arena_recorde=d.get("arena_recorde",0)
        j.dungeon_recorde=d.get("dungeon_recorde",0)
        j.derrotou_bobafat=d.get("derrotou_bobafat",False)
        j.derrotou_conceito=d.get("derrotou_conceito",False)
        j.total_summons=d.get("total_summons",0)
        j.areas_visitadas=set(d.get("areas_visitadas",[]))
        j.crafts=d.get("crafts",0)
        j.pet=d.get("pet")
        areas=d.get("areas_desbloqueadas",["floresta"])
        return j, areas
    except Exception as e:
        print(C.VERMELHO+"  Erro ao carregar: "+str(e)+" "+C.RESET)
        return None, None

def deletar_save():
    try:
        if _os.path.exists(SAVE_FILE):
            _os.remove(SAVE_FILE); return True
    except: pass
    return False

# ─────────────────────────────────────────
#  GERENCIAMENTO DE INVENTÁRIO
# ─────────────────────────────────────────
INV_LIMITE = 20

def tela_inventario_gerenciar(j):
    while True:
        limpar(); titulo("INVENTARIO","🎒",C.AMARELO)
        print(C.CINZA+"  Itens: "+str(len(j.inventario))+"/"+str(INV_LIMITE)+" "+C.RESET)
        if not j.inventario:
            print(C.CINZA+"  Vazio."+C.RESET); pausar(); return
        from collections import Counter
        inv_c = Counter(j.inventario)
        itens_unicos = list(inv_c.keys())
        for i,it in enumerate(itens_unicos,1):
            d=ITENS.get(it,{}); qtd=inv_c[it]
            valor=d.get("valor",0)
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+d.get("emoji","")+" "+it+
                  " x"+str(qtd)+"  "+C.CINZA+d.get("desc","")+"  "+
                  C.LARANJA+"[vender: "+str(valor//2)+"g]"+C.RESET)
        print()
        print("  "+C.VERDE+"u<n>"+C.RESET+" Usar  "+
              C.LARANJA+"v<n>"+C.RESET+" Vender  "+
              C.CINZA+"0"+C.RESET+" Voltar")
        print(C.CINZA+"  Ex: u1 usa o item 1 / v2 vende o item 2"+C.RESET+"\n")
        cmd=input(C.AMARELO+"  Comando: "+C.RESET).strip().lower()
        if cmd=="0": break
        try:
            if cmd.startswith("u"):
                idx_u=int(cmd[1:])-1; it_nome=itens_unicos[idx_u]
                idx_inv=j.inventario.index(it_nome)
                ok,msg=j.usar_item(idx_inv)
                print((C.VERDE if ok else C.VERMELHO)+"\n  "+msg+C.RESET); pausar()
            elif cmd.startswith("v"):
                idx_v=int(cmd[1:])-1; it_nome=itens_unicos[idx_v]
                d=ITENS.get(it_nome,{}); preco=d.get("valor",0)//2
                idx_inv=j.inventario.index(it_nome); j.inventario.pop(idx_inv)
                j.gold+=preco
                print(C.LARANJA+"\n  "+it_nome+" vendido por "+str(preco)+"g! "+C.RESET); pausar()
        except: print(C.VERMELHO+"\n  Comando invalido!"+C.RESET); pausar()

# ─────────────────────────────────────────
#  RELATÓRIO DE BATALHA
# ─────────────────────────────────────────
class Relatorio:
    def __init__(self):
        self.dano_causado=0; self.dano_recebido=0
        self.curas=0; self.criticos=0; self.turnos=0
        self.habs_usadas=[]; self.summons_invocados=0

    def mostrar(self, ini_nome):
        limpar(); titulo("RELATORIO DE BATALHA","📊",C.CIANO)
        print(C.CINZA+"  Inimigo: "+ini_nome+"\n"+C.RESET)
        print("  Turnos          "+C.AMARELO+str(self.turnos)+" "+C.RESET)
        print("  Dano causado    "+C.VERDE+str(self.dano_causado)+" "+C.RESET)
        print("  Dano recebido   "+C.VERMELHO+str(self.dano_recebido)+" "+C.RESET)
        print("  HP curado       "+C.VERDE+str(self.curas)+" "+C.RESET)
        print("  Criticos        "+C.AMARELO+str(self.criticos)+" "+C.RESET)
        print("  Summons usados  "+C.ROXO+str(self.summons_invocados)+" "+C.RESET)
        if self.habs_usadas:
            from collections import Counter
            habs_c=Counter(self.habs_usadas)
            print(C.CINZA+"  Habilidades: "+", ".join(h+" x"+str(n) for h,n in habs_c.items())+" "+C.RESET)
        linha(); pausar()
# ─────────────────────────────────────────
#  TÍTULOS
# ─────────────────────────────────────────
TITULOS_DEF = [
    {"id":"iniciante",   "nome":"Iniciante",        "emoji":"🌱","cond":lambda j: j.nivel>=1},
    {"id":"aventureiro", "nome":"Aventureiro",       "emoji":"⚔️","cond":lambda j: j.vitorias>=5},
    {"id":"veterano",    "nome":"Veterano de Guerra","emoji":"🛡️","cond":lambda j: j.vitorias>=20},
    {"id":"cacador",     "nome":"Cacador de Chefes", "emoji":"👑","cond":lambda j: j.chefes>=3},
    {"id":"lenda",       "nome":"Lenda Viva",        "emoji":"🌟","cond":lambda j: j.nivel>=15},
    {"id":"arena",       "nome":"Gladiador",         "emoji":"🏟️","cond":lambda j: j.arena_recorde>=10},
    {"id":"alquimista",  "nome":"Alquimista",        "emoji":"🔨","cond":lambda j: j.crafts>=3},
    {"id":"invocador",   "nome":"Mestre Invocador",  "emoji":"🔮","cond":lambda j: len(j.summons_ativos)>=2},
    {"id":"ricao",       "nome":"Magnata",           "emoji":"💰","cond":lambda j: j.gold>=3000},
    {"id":"bobafat",     "nome":"O Inominavel",      "emoji":"👁️","cond":lambda j: j.derrotou_bobafat},
    {"id":"conceitual",  "nome":"Alem da Logica",    "emoji":"🌀","cond":lambda j: j.arma.get("raridade")=="Conceitual"},
]

def checar_titulos(j):
    novos=[]
    for t in TITULOS_DEF:
        if t["id"] not in j.titulos:
            try:
                if t["cond"](j):
                    j.titulos.add(t["id"]); novos.append(t)
            except: pass
    return novos

def mostrar_titulos(j):
    limpar(); titulo("TITULOS","🏅",C.AMARELO)
    print(C.CINZA+"  Desbloqueados: "+str(len(j.titulos))+"/"+str(len(TITULOS_DEF))+" "+C.RESET+"\n")
    disponiveis=[]
    for t in TITULOS_DEF:
        if t["id"] in j.titulos: disponiveis.append(t)
    for t in TITULOS_DEF:
        if t["id"] in j.titulos:
            eq=" [EQUIPADO]" if j.titulo_ativo and j.titulo_ativo["id"]==t["id"] else ""
            print("  "+C.AMARELO+t["emoji"]+" "+t["nome"]+C.RESET+C.VERDE+eq+C.RESET)
        else:
            print("  "+C.CINZA+"🔒 ???"+C.RESET)
    if disponiveis:
        print()
        esc=input(C.AMARELO+"  Equipar titulo (numero) ou ENTER: "+C.RESET).strip()
        try:
            idx=int(esc)-1
            if 0<=idx<len(disponiveis):
                j.titulo_ativo=disponiveis[idx]
                print(C.VERDE+"\n  Titulo equipado: "+disponiveis[idx]["emoji"]+" "+disponiveis[idx]["nome"]+" "+C.RESET)
                pausar()
                return
        except: pass
    pausar()

# ─────────────────────────────────────────
#  QUESTS
# ─────────────────────────────────────────
QUESTS_DEF = [
    {"id":"q_iniciante", "nome":"Primeiros Passos",   "emoji":"🌱",
     "desc":"Venca 3 batalhas","recompensa":"Pocao Media x3 + 50 gold",
     "cond":lambda j: j.vitorias>=3,
     "recomp":lambda j: ([j.inventario.extend(["Pocao Media"]*3),setattr(j,"gold",j.gold+50)])},

    {"id":"q_explorador","nome":"Explorador Nato",    "emoji":"🗺️",
     "desc":"Visite 3 areas diferentes","recompensa":"Eter Grande x2 + 100 gold",
     "cond":lambda j: len(j.areas_visitadas)>=3,
     "recomp":lambda j: ([j.inventario.extend(["Eter Grande"]*2),setattr(j,"gold",j.gold+100)])},

    {"id":"q_caçador",   "nome":"Cacador de Monstros","emoji":"🗡️",
     "desc":"Venca 15 batalhas","recompensa":"Elixir Menor + 200 gold",
     "cond":lambda j: j.vitorias>=15,
     "recomp":lambda j: ([j.inventario.append("Elixir Menor"),setattr(j,"gold",j.gold+200)])},

    {"id":"q_chefe",     "nome":"Matador de Titãs",   "emoji":"💀",
     "desc":"Derrote 2 chefes","recompensa":"Pedra Magica x2 + 300 gold",
     "cond":lambda j: j.chefes>=2,
     "recomp":lambda j: ([j.inventario.extend(["Pedra Magica"]*2),setattr(j,"gold",j.gold+300)])},

    {"id":"q_arena",     "nome":"Gladiador Iniciante","emoji":"🏟️",
     "desc":"Sobreviva 5 ondas na arena","recompensa":"Pocao Grande x3 + 150 gold",
     "cond":lambda j: j.arena_recorde>=5,
     "recomp":lambda j: ([j.inventario.extend(["Pocao Grande"]*3),setattr(j,"gold",j.gold+150)])},

    {"id":"q_craft",     "nome":"Artesao Habilidoso", "emoji":"🔨",
     "desc":"Crie 2 itens pelo crafting","recompensa":"Pedra do Caos + 250 gold",
     "cond":lambda j: j.crafts>=2,
     "recomp":lambda j: ([j.inventario.append("Pedra do Caos"),setattr(j,"gold",j.gold+250)])},

    {"id":"q_summon",    "nome":"Mestre das Invocacoes","emoji":"🔮",
     "desc":"Invoque 3 summons diferentes","recompensa":"Elixir + 400 gold",
     "cond":lambda j: j.total_summons>=3,
     "recomp":lambda j: ([j.inventario.append("Elixir"),setattr(j,"gold",j.gold+400)])},

    {"id":"q_lendario",  "nome":"Em Busca do Lendario","emoji":"🌟",
     "desc":"Equipe um item Lendario ou superior","recompensa":"500 gold + titulo especial",
     "cond":lambda j: j.arma.get("raridade") in ("Lendario","Mitico","Abissal","Conceitual"),
     "recomp":lambda j: setattr(j,"gold",j.gold+500)},
]

def checar_quests(j):
    concluidas=[]
    for q in QUESTS_DEF:
        if q["id"] not in j.quests_concluidas and q["id"] not in j.quests_notificadas:
            try:
                if q["cond"](j):
                    j.quests_notificadas.add(q["id"])
                    concluidas.append(q)
            except: pass
    return concluidas

def coletar_quest(j, q):
    if q["id"] in j.quests_concluidas: return False
    try: q["recomp"](j)
    except: pass
    j.quests_concluidas.add(q["id"])
    return True

def tela_quests(j):
    while True:
        limpar(); titulo("QUESTS","📜",C.LARANJA)
        pendentes=[q for q in QUESTS_DEF if q["id"] not in j.quests_concluidas]
        concluidas_list=[q for q in QUESTS_DEF if q["id"] in j.quests_concluidas]
        print(C.CINZA+"  Concluidas: "+str(len(concluidas_list))+"/"+str(len(QUESTS_DEF))+" "+C.RESET+"\n")

        # Prontas pra coletar
        prontas=[q for q in pendentes if q["id"] in j.quests_notificadas]
        if prontas:
            print(C.VERDE+C.BOLD+"  Prontas para coletar:"+C.RESET)
            for i,q in enumerate(prontas,1):
                print("  "+C.AMARELO+str(i)+C.RESET+"  "+q["emoji"]+" "+q["nome"])
                print(C.CINZA+"     Recompensa: "+q["recompensa"]+" "+C.RESET)
            print()

        # Em progresso
        em_prog=[q for q in pendentes if q["id"] not in j.quests_notificadas]
        if em_prog:
            print(C.AMARELO+C.BOLD+"  Em progresso:"+C.RESET)
            for q in em_prog:
                print("  "+q["emoji"]+" "+C.CINZA+q["nome"]+" — "+q["desc"]+" "+C.RESET)
            print()

        if concluidas_list:
            print(C.CINZA+"  Concluidas: "+", ".join(q["emoji"] for q in concluidas_list)+C.RESET+"\n")

        if prontas:
            esc=input(C.AMARELO+"  Coletar recompensa (numero) ou ENTER: "+C.RESET).strip()
            try:
                idx=int(esc)-1
                if 0<=idx<len(prontas):
                    q=prontas[idx]
                    coletar_quest(j,q)
                    print(C.VERDE+C.BOLD+"\n  Quest concluida: "+q["emoji"]+" "+q["nome"]+"! "+C.RESET)
                    print(C.AMARELO+"  Recompensa: "+q["recompensa"]+" "+C.RESET)
                    pausar(); continue
            except: pass
        else:
            pausar(); break

def notificar_quests(concluidas):
    for q in concluidas:
        print(C.LARANJA+C.BOLD+"  📜 QUEST COMPLETA: "+q["emoji"]+" "+q["nome"]+"! "+C.RESET)
        print(C.CINZA+"     Va ate Quests para coletar: "+q["recompensa"]+" "+C.RESET)

# ─────────────────────────────────────────
#  FACOES / REPUTACAO
# ─────────────────────────────────────────
FACOES = {
    "Guarda Real":   {"emoji":"⚔️","cor":C.AZUL,    "desc":"Defensores do reino","bonus":"DEF +10%"},
    "Ordem Arcana":  {"emoji":"🔮","cor":C.ROXO,    "desc":"Mestres da magia",   "bonus":"MP +20%"},
    "Irmandade Sombria":{"emoji":"💀","cor":C.CINZA,"desc":"Mercenarios das trevas","bonus":"ATK +10%"},
    "Comerciantes":  {"emoji":"💰","cor":C.LARANJA, "desc":"Mestres do ouro",    "bonus":"Gold +25%"},
}

NIVEIS_REP = [(0,"Desconhecido"),(100,"Conhecido"),(300,"Amigavel"),(600,"Honrado"),(1000,"Exaltado")]

def nivel_reputacao(rep):
    nivel="Desconhecido"
    for minimo,nome in NIVEIS_REP:
        if rep>=minimo: nivel=nome
    return nivel

def tela_facoes(j):
    limpar(); titulo("FACOES","🏰",C.AZUL)
    print(C.CINZA+"  Sua reputacao com cada facao:\n"+C.RESET)
    for nome,f in FACOES.items():
        rep=j.reputacao.get(nome,0)
        niv=nivel_reputacao(rep)
        barra_r=int(min(rep,1000)/1000*20)
        print("  "+f["cor"]+f["emoji"]+" "+nome+C.RESET)
        print("  "+C.CINZA+f["desc"]+" | Bonus: "+f["bonus"]+C.RESET)
        print("  "+C.AZUL+"█"*barra_r+C.CINZA+"░"*(20-barra_r)+C.RESET+
              "  "+f["cor"]+niv+" ("+str(rep)+"/1000)"+C.RESET)
        if rep>=600:
            print(C.VERDE+"  Bonus ATIVO: "+f["bonus"]+" "+C.RESET)
        print()
    pausar()

def aplicar_bonus_facao(j):
    for nome,f in FACOES.items():
        rep=j.reputacao.get(nome,0)
        if rep>=600:
            if nome=="Guarda Real":    j.defesa_base=int(j.defesa_base*1.10)
            elif nome=="Ordem Arcana": j.mp_max=int(j.mp_max*1.20); j.mp=min(j.mp,j.mp_max)
            elif nome=="Irmandade Sombria": j.atk_base=int(j.atk_base*1.10)

def ganhar_reputacao(j, log):
    if j.vitorias%3==0 and j.vitorias>0:
        facao=random.choice(list(FACOES.keys()))
        ganho=random.randint(15,40)
        j.reputacao[facao]=min(1000,j.reputacao.get(facao,0)+ganho)
        log.append(FACOES[facao]["cor"]+"  +"+str(ganho)+" rep com "+facao+"! "+C.RESET)

# ─────────────────────────────────────────
#  CLIMA E TEMPO
# ─────────────────────────────────────────
CLIMAS = {
    "ensolarado":{"emoji":"☀️","desc":"Dia claro e quente","efeito":"atk+5%","cor":C.AMARELO,
                  "ascii":["  \\  |  /  ","   .--.    ","  / () \\  ","   \\__/    ","  /  |  \\  "],
                  "msg_batalha":["A luz do sol aquece seus musculos!","Visibilidade perfeita!"]},
    "chuvoso":   {"emoji":"🌧️","desc":"Chuva forte","efeito":"vel-10%","cor":C.AZUL,
                  "ascii":["  .--.      "," ( () )    "," `--'      ","  / / /    "," / / /     "],
                  "msg_batalha":["A chuva dificulta os movimentos!","O chao esta escorregadio!"]},
    "tempestade":{"emoji":"⛈️","desc":"Tempestade magica","efeito":"mp+10%","cor":C.ROXO,
                  "ascii":["  .-.-.     ","(  |||  )  "," `-'-'     ","  )\\(     ","   V       "],
                  "msg_batalha":["Energia magica no ar!","Raios energizam seus feiticos!"]},
    "nevando":   {"emoji":"❄️","desc":"Neve intensa","efeito":"ini_lento","cor":C.CIANO,
                  "ascii":["   *  *  *  ","  * * *    ","   *  *  * ","  * * *    ","   *  *  * "],
                  "msg_batalha":["O frio congela os inimigos!","Neve cobre o campo!"]},
    "noite":     {"emoji":"🌙","desc":"Noite fechada","efeito":"critico+15%","cor":C.CINZA,
                  "ascii":["   .  * .  ","  * . * .  "," .  )(  *  ","  * .  . * ","   . * .   "],
                  "msg_batalha":["A escuridao aguça seus sentidos!","Criticos mais faceis no escuro!"]},
    "aurora":    {"emoji":"🌌","desc":"Aurora magica","efeito":"xp+20%","cor":C.ROXO,
                  "ascii":["  ~-~-~-~  ","  ~-~-~-~  ","  ~-~-~-~  ","  ~-~-~-~  ","  ~-~-~-~  "],
                  "msg_batalha":["A aurora potencializa o aprendizado!","Magia ancestral no ar!"]},
}

def sortear_clima():
    return random.choice(list(CLIMAS.keys()))

def mostrar_clima(clima_atual):
    c=CLIMAS.get(clima_atual, CLIMAS["ensolarado"])
    print(c["cor"]+"  "+c["emoji"]+" "+c["desc"].upper()+"  |  "+c["efeito"]+" "+C.RESET)

def mostrar_clima_visual(clima_atual):
    c=CLIMAS.get(clima_atual, CLIMAS["ensolarado"])
    print(c["cor"]+C.BOLD+"  "+c["emoji"]+"  "+c["desc"].upper()+" "+C.RESET)
    for linha_a in c.get("ascii",[]):
        print(c["cor"]+"  "+linha_a+C.RESET)
    if c.get("msg_batalha"):
        print(C.CINZA+"  "+random.choice(c["msg_batalha"])+" "+C.RESET)
    print()

def msg_clima_turno(clima_atual, log):
    c=CLIMAS.get(clima_atual, {})
    if c.get("msg_batalha") and random.random()<0.15:
        log.append(c["cor"]+"  ["+c["emoji"]+"] "+random.choice(c["msg_batalha"])+" "+C.RESET)

def aplicar_efeito_clima(j, ini, clima):
    ef=CLIMAS[clima]["efeito"]
    if ef=="atk+5%":    return int(j.atk*1.05)
    if ef=="critico+15%": return None  # tratado no combate
    if ef=="ini_lento": ini["atk"]=int(ini.get("atk",10)*0.85)
    return None

# ─────────────────────────────────────────
#  HISTORIA COM ESCOLHAS MORAIS
# ─────────────────────────────────────────
HISTORIA_EVENTOS = [
    {"id":"aldeao",
     "titulo":"O Aldeao em Perigo",
     "desc":"Voce encontra um aldeao sendo atacado por bandidos.",
     "opcoes":[
         {"texto":"Salvar o aldeao (heroi)","karma":+20,"gold":0,"rep":("Guarda Real",30),
          "resultado":"Voce salva o aldeao! Ele agradece com lagrimas nos olhos."},
         {"texto":"Ignorar e passar (neutro)","karma":0,"gold":0,"rep":None,
          "resultado":"Voce passa sem olhar. O grito do aldeao some ao longe."},
         {"texto":"Roubar os bandidos depois","karma":-10,"gold":40,"rep":("Irmandade Sombria",15),
          "resultado":"Voce espera os bandidos irem embora e pega o ouro deles."},
     ]},
    {"id":"mercador",
     "titulo":"O Mercador Corrupto",
     "desc":"Um mercador vende pocoes falsas para doentes. Voce descobre.",
     "opcoes":[
         {"texto":"Denunciar as autoridades","karma":+15,"gold":-20,"rep":("Guarda Real",25),
          "resultado":"As autoridades prendem o mercador. A cidade agradece."},
         {"texto":"Chantagear o mercador","karma":-20,"gold":150,"rep":("Irmandade Sombria",20),
          "resultado":"O mercador paga para voce ficar quieto. Gold sujo, mas gold."},
         {"texto":"Destruir as pocoes falsas","karma":+10,"gold":0,"rep":("Comerciantes",-10),
          "resultado":"Voce destroi tudo. O mercador fica furioso mas ninguem morre."},
     ]},
    {"id":"prisioneiro",
     "titulo":"O Prisioneiro das Trevas",
     "desc":"Voce encontra um prisioneiro do Senhor das Trevas. Ele implora por liberdade.",
     "opcoes":[
         {"texto":"Libertar o prisioneiro","karma":+25,"gold":0,"rep":("Ordem Arcana",20),
          "resultado":"Livre! O prisioneiro revela ser um mago e te ensina algo."},
         {"texto":"Deixar onde esta","karma":-5,"gold":0,"rep":None,
          "resultado":"Voce continua seu caminho. O prisioneiro chora."},
         {"texto":"Negociar informacoes","karma":0,"gold":80,"rep":None,
          "resultado":"Ele conta segredos do castelo em troca da liberdade... talvez."},
     ]},
]

def evento_historia(j):
    ev=random.choice([e for e in HISTORIA_EVENTOS if e["id"] not in j.historias_vistas])
    if not ev: return
    j.historias_vistas.add(ev["id"])

    limpar(); linha("=",52,C.CIANO)
    print(C.CIANO+C.BOLD+"\n  📖 "+ev["titulo"]+"\n"+C.RESET)
    digitar(C.CINZA+"  "+ev["desc"]+C.RESET)
    print()
    for i,op in enumerate(ev["opcoes"],1):
        karma_txt=(C.VERDE+" [karma +"+str(op["karma"])+"]" if op["karma"]>0
                   else C.VERMELHO+" [karma "+str(op["karma"])+"]" if op["karma"]<0
                   else C.CINZA+" [neutro]")+C.RESET
        print("  "+C.AMARELO+str(i)+C.RESET+"  "+op["texto"]+karma_txt)
    print()
    esc=input(C.AMARELO+"  Escolha: "+C.RESET).strip()
    try:
        idx=int(esc)-1
        op=ev["opcoes"][idx]
        print()
        digitar(C.BRANCO+"  "+op["resultado"]+C.RESET)
        j.karma+=op["karma"]
        j.gold=max(0,j.gold+op.get("gold",0))
        if op.get("rep"):
            facao,val=op["rep"]
            j.reputacao[facao]=min(1000,j.reputacao.get(facao,0)+val)
            print(FACOES[facao]["cor"]+"  Reputacao com "+facao+": +"+str(val)+" "+C.RESET)
        if op["karma"]>0:
            print(C.VERDE+"  Karma: +"+str(op["karma"])+" "+C.RESET)
        elif op["karma"]<0:
            print(C.VERMELHO+"  Karma: "+str(op["karma"])+" "+C.RESET)
    except: pass
    linha("=",52,C.CIANO); pausar()

# ─────────────────────────────────────────
#  DUNGEON
# ─────────────────────────────────────────
def modo_dungeon(j):
    limpar(); titulo("DUNGEON","🏚️",C.VERMELHO)
    print(C.CINZA+"  Andares progressivos. Cada andar mais dificil."+C.RESET)
    print(C.CINZA+"  Recompensas maiores a cada 5 andares."+C.RESET)
    print(C.CINZA+"  Recorde: "+str(j.dungeon_recorde)+" andares"+C.RESET+"\n")
    esc=input(C.AMARELO+"  Entrar na dungeon? (s/n): "+C.RESET).strip().lower()
    if esc!="s": return

    andar=0; todos_ini=[i for lista in INIMIGOS.values() for i in lista]
    j.fenix_usada=False

    while True:
        andar+=1
        clima=sortear_clima(); c_dados=CLIMAS[clima]
        limpar(); linha("=",52,C.VERMELHO)
        print(C.VERMELHO+C.BOLD+"  🏚️ DUNGEON — ANDAR "+str(andar)+" "+C.RESET)
        print(C.CINZA+"  Recorde: "+str(j.dungeon_recorde)+" "+C.RESET)
        mostrar_clima(clima)
        linha("=",52,C.VERMELHO)

        # Evento especial a cada 5 andares
        if andar%5==0:
            print(C.AMARELO+C.BOLD+"\n  Sala especial! Escolha:"+C.RESET)
            print("  "+C.AMARELO+"1"+C.RESET+"  Sala de cura (restaura 50% HP/MP)")
            print("  "+C.AMARELO+"2"+C.RESET+"  Sala do tesouro (+gold aleatorio)")
            print("  "+C.AMARELO+"3"+C.RESET+"  Continuar direto\n")
            op=input(C.AMARELO+"  Opcao: "+C.RESET).strip()
            if op=="1":
                j.hp=min(j.hp_max,j.hp+j.hp_max//2)
                j.mp=min(j.mp_max,j.mp+j.mp_max//2)
                print(C.VERDE+"\n  HP e MP restaurados! "+C.RESET); pausar()
            elif op=="2":
                g=random.randint(50,200)*andar//5
                j.gold+=g
                print(C.AMARELO+"\n  +"+str(g)+" gold! "+C.RESET); pausar()
        else:
            pausar("  ENTER para avancar...")

        # Inimigo escalado
        base=random.choice(todos_ini)
        mult=1.0+andar*0.18
        ini_d={
            "nome":base["nome"],"emoji":base["emoji"],
            "hp":int(base["hp"]*mult),"atk":int(base["atk"]*mult),
            "def":int(base.get("def",0)*mult),
            "xp":int(base.get("xp",20)*mult),"gold":int(base.get("gold",10)*mult),
        }
        # Clima afeta inimigo
        if clima=="nevando": ini_d["atk"]=int(ini_d["atk"]*0.85)
        if andar>=15:  rar_pool=["Epico","Lendario","Mitico","Abissal"]
        elif andar>=8: rar_pool=["Raro","Epico","Lendario"]
        elif andar>=4: rar_pool=["Incomum","Raro","Epico"]
        else:          rar_pool=["Comum","Incomum","Raro"]
        ini_d=aplicar_raridade_inimigo(ini_d,random.choice(rar_pool))

        # Chefe a cada 10 andares
        eh_chefe_d=(andar%10==0)
        if eh_chefe_d:
            chefe_rand=random.choice(CHEFES)
            res=batalha(j,chefe_rand,eh_chefe=True)
        else:
            res=batalha(j,ini_d)

        if res=="derrota":
            limpar(); linha("=",52,C.VERMELHO)
            print(C.VERMELHO+C.BOLD+"\n  Voce foi derrotado no andar "+str(andar)+"!\n"+C.RESET)
            if andar>j.dungeon_recorde: j.dungeon_recorde=andar
            print(C.CINZA+"  Recorde: "+str(j.dungeon_recorde)+" andares "+C.RESET)
            linha("=",52,C.VERMELHO); pausar(); break

        if andar>j.dungeon_recorde: j.dungeon_recorde=andar

        # Drop bonus por clima
        if clima=="aurora":
            bonus=int(j.xp*0.20); j.ganhar_xp(bonus)
            print(C.ROXO+"  [Aurora] +"+str(bonus)+" XP bonus! "+C.RESET); pausar()

        esc2=input(C.AMARELO+"  Continuar descendo? (s/n): "+C.RESET).strip().lower()
        if esc2!="s":
            if andar>j.dungeon_recorde: j.dungeon_recorde=andar
            print(C.CINZA+"\n  Voce saiu da dungeon no andar "+str(andar)+". "+C.RESET); pausar(); break

# ─────────────────────────────────────────
#  CONTEUDO POS-BOBAFAT
# ─────────────────────────────────────────
BOSS_SECRETO_2 = {
    "nome":"O Conceito",
    "emoji":"🌀",
    "area":"void",
    "xp":99999,
    "gold":99999,
    "fases":[
        {"hp":1500,"atk":150,"def":80,
         "fala":"Voce nao devia existir aqui.",
         "especial":"Apagamento","mult_esp":4.0},
        {"hp":1500,"atk":200,"def":120,
         "fala":"Sua existencia e uma anomalia.",
         "especial":"Reescrita da Realidade","mult_esp":6.0},
        {"hp":1500,"atk":300,"def":180,
         "fala":"EU. SOU. TUDO.",
         "especial":"Fim do Conceito","mult_esp":10.0},
    ],
}

def encontro_o_conceito(j):
    if not j.derrotou_bobafat: return
    limpar(); time.sleep(0.5)
    linha("=",52,C.CIANO)
    digitar(C.CIANO+"  ...o universo tremeu quando bobafat caiu.",0.04)
    time.sleep(0.8)
    digitar(C.CIANO+"  Algo maior. Mais antigo. Acordou.",0.04)
    time.sleep(1.0)
    print(C.BOLD+C.CIANO+"\n  🌀  O  C O N C E I T O  🌀\n"+C.RESET)
    digitar(C.CINZA+"  Voce nao devia existir aqui.",0.05)
    print(C.VERMELHO+C.BOLD+"\n  BOSS FINAL VERDADEIRO DESBLOQUEADO!"+C.RESET)
    print(C.CINZA+"  3 fases. Stats absurdos. Sem misericordia."+C.RESET)
    linha("=",52,C.CIANO)
    esc=input(C.AMARELO+"  Enfrentar O Conceito? (s/n): "+C.RESET).strip().lower()
    if esc!="s":
        print(C.CINZA+"  ...ele espera. Ele sempre espera."+C.RESET); pausar(); return
    j.hp=j.hp_max; j.mp=j.mp_max
    res=batalha(j,BOSS_SECRETO_2,eh_chefe=True)
    limpar()
    if res=="derrota":
        linha("=",52,C.CIANO)
        digitar(C.CINZA+"  O Conceito te olhou por um longo momento.",0.04)
        time.sleep(0.6)
        digitar(C.CINZA+"  Depois simplesmente... te ignorou.",0.04)
        time.sleep(0.6)
        digitar(C.CINZA+"  Voce nao era ameaca suficiente.",0.04)
        linha("=",52,C.CIANO); pausar()
    else:
        linha("=",52,C.CIANO)
        print(C.BOLD+C.CIANO+"\n  O CONCEITO FOI DERROTADO.\n"+C.RESET)
        digitar(C.CINZA+"  A realidade parou por um segundo.",0.04)
        time.sleep(0.5)
        digitar(C.CINZA+"  Depois continuou, como se nada tivesse acontecido.",0.04)
        time.sleep(0.5)
        digitar(C.BRANCO+"  Mas voce sabe.",0.04)
        time.sleep(0.5)
        digitar(C.CIANO+"  Voce sempre vai saber.",0.04)
        j.derrotou_conceito=True
        linha("=",52,C.CIANO); pausar()

# ─────────────────────────────────────────
#  MODO HISTÓRIA
# ─────────────────────────────────────────
CAPITULOS = [
    {"id":1,"titulo":"O Chamado.",
     "texto":[
         "Voce era um aventureiro comum vivendo numa cidade pacata.",
         "Ate que uma noite o ceu ficou vermelho.",
         "Mensageiros chegaram com noticias terriveis:",
         "O Senhor das Trevas havia acordado.",
         "E por algum motivo... ele te escolheu como ameaca.",
         "Agora voce nao tem escolha.",
         "Ou enfrenta o destino, ou sucumbe a ele.",
     ],"area":"floresta"},
    {"id":2,"titulo":"A Floresta Sombria.",
     "texto":[
         "As arvores sussurram nomes de aventureiros mortos.",
         "Voce avanca mesmo assim.",
         "No fundo da floresta, o Rei Goblin aguarda.",
         "Dizem que ele sabe onde fica a proxima pista.",
     ],"area":"floresta"},
    {"id":3,"titulo":"Nas Profundezas.",
     "texto":[
         "Alem da floresta, a Caverna do Abismo se abre como uma ferida.",
         "O ar e pesado. Algo antigo respira la dentro.",
         "Um Dragao das Sombras custodia os segredos das trevas.",
     ],"area":"caverna"},
    {"id":4,"titulo":"A Torre Proibida.",
     "texto":[
         "A Torre pulsa com magia negra.",
         "Cada andar e um pesadelo diferente.",
         "O Senhor da Torre nao deixara voce passar facilmente.",
     ],"area":"torre"},
    {"id":5,"titulo":"O Abismo.",
     "texto":[
         "Voce desceu fundo demais.",
         "Aqui, ate a sombra tem medo.",
         "A Abominacao te espera.",
         "Mas voce esta perto. Muito perto.",
     ],"area":"abismo"},
    {"id":6,"titulo":"O Confronto Final.",
     "texto":[
         "A Fortaleza das Trevas.",
         "Finalmente.",
         "O Senhor das Trevas sabe que voce chegou.",
         "Ele esperava por isso.",
         "Talvez... ele esperava por voce especificamente.",
     ],"area":"fortaleza"},
]

def exibir_capitulo(cap):
    limpar(); linha("=",52,C.CIANO)
    print(C.BOLD+C.CIANO+"\n  📖 Capitulo "+str(cap["id"])+": "+cap["titulo"]+"\n"+C.RESET)
    for linha_txt in cap["texto"]:
        digitar(C.CINZA+"  "+linha_txt+C.RESET, 0.03)
        time.sleep(0.3)
    linha("=",52,C.CIANO); pausar()

def verificar_narrativa(j, area_id):
    for cap in CAPITULOS:
        if cap["area"]==area_id and cap["id"] not in j.capitulos_vistos:
            j.capitulos_vistos.add(cap["id"])
            exibir_capitulo(cap)
            break
# ─────────────────────────────────────────
#  CONQUISTAS
# ─────────────────────────────────────────
CONQUISTAS_DEF = [
    {"id":"primeiro_sangue",  "nome":"Primeiro Sangue",    "desc":"Venca sua primeira batalha",          "emoji":"🩸", "cond":lambda j: j.vitorias>=1},
    {"id":"guerreiro10",      "nome":"Veterano",           "desc":"Venca 10 batalhas",                   "emoji":"⚔️", "cond":lambda j: j.vitorias>=10},
    {"id":"guerreiro50",      "nome":"Lendario de Guerra", "desc":"Venca 50 batalhas",                   "emoji":"🏆", "cond":lambda j: j.vitorias>=50},
    {"id":"nivel5",           "nome":"Em Crescimento",     "desc":"Chegue ao nivel 5",                   "emoji":"⬆️", "cond":lambda j: j.nivel>=5},
    {"id":"nivel10",          "nome":"Poderoso",           "desc":"Chegue ao nivel 10",                  "emoji":"💪", "cond":lambda j: j.nivel>=10},
    {"id":"nivel20",          "nome":"Transcendente",      "desc":"Chegue ao nivel 20",                  "emoji":"🌟", "cond":lambda j: j.nivel>=20},
    {"id":"rico",             "nome":"Endinheirado",       "desc":"Acumule 1000 gold",                   "emoji":"💰", "cond":lambda j: j.gold>=1000},
    {"id":"megaRico",         "nome":"Milionario",         "desc":"Acumule 5000 gold",                   "emoji":"💎", "cond":lambda j: j.gold>=5000},
    {"id":"chefe1",           "nome":"Matador de Chefes",  "desc":"Derrote seu primeiro chefe",          "emoji":"👑", "cond":lambda j: j.chefes>=1},
    {"id":"chefe5",           "nome":"Caçador Lendario",   "desc":"Derrote 5 chefes",                    "emoji":"☠️", "cond":lambda j: j.chefes>=5},
    {"id":"pet",              "nome":"Amigo Fiel",         "desc":"Adote um pet",                        "emoji":"🐾", "cond":lambda j: j.pet is not None},
    {"id":"craft",            "nome":"Artesao",            "desc":"Crie um item pelo crafting",          "emoji":"🔨", "cond":lambda j: j.crafts>=1},
    {"id":"arena10",          "nome":"Gladiador",          "desc":"Sobreviva 10 ondas na arena",         "emoji":"🏟️", "cond":lambda j: j.arena_recorde>=10},
    {"id":"arena25",          "nome":"Campeao da Arena",   "desc":"Sobreviva 25 ondas na arena",         "emoji":"🥇", "cond":lambda j: j.arena_recorde>=25},
    {"id":"lendario",         "nome":"Item Lendario",      "desc":"Equipe um item Lendario ou superior", "emoji":"🟡", "cond":lambda j: j.arma.get("raridade") in ("Lendario","Mitico","Abissal","Conceitual")},
    {"id":"conceitual",       "nome":"Alem da Realidade",  "desc":"Equipe um item Conceitual",           "emoji":"🌀", "cond":lambda j: j.arma.get("raridade")=="Conceitual" or j.armadura.get("raridade")=="Conceitual"},
    {"id":"bobafat",          "nome":"O Inominavel",       "desc":"Derrote bobafat",                     "emoji":"👁️", "cond":lambda j: j.derrotou_bobafat},
    {"id":"sobrevivente",     "nome":"Sobrevivente",       "desc":"Termine uma batalha com menos de 10 HP","emoji":"❤️","cond":lambda j: j.quase_morreu},
]

def checar_conquistas(j):
    novas = []
    for c in CONQUISTAS_DEF:
        if c["id"] not in j.conquistas:
            try:
                if c["cond"](j):
                    j.conquistas.add(c["id"])
                    novas.append(c)
            except: pass
    return novas

def mostrar_conquistas(j):
    limpar(); titulo("CONQUISTAS","🏆",C.AMARELO)
    print(C.CINZA+"  Desbloqueadas: "+str(len(j.conquistas))+"/"+str(len(CONQUISTAS_DEF))+" "+C.RESET+"\n")
    for c in CONQUISTAS_DEF:
        if c["id"] in j.conquistas:
            print("  "+C.AMARELO+C.BOLD+c["emoji"]+" "+c["nome"]+C.RESET+"  "+C.CINZA+c["desc"]+" "+C.RESET)
        else:
            print("  "+C.CINZA+"🔒 ???  "+c["desc"]+" "+C.RESET)
    linha(); pausar()

def notificar_conquistas(novas):
    for c in novas:
        print(C.AMARELO+C.BOLD+"  🏆 CONQUISTA: "+c["emoji"]+" "+c["nome"]+"! "+C.RESET)
        print(C.CINZA+"     "+c["desc"]+" "+C.RESET)

# ─────────────────────────────────────────
#  PETS
# ─────────────────────────────────────────
PETS_DISPONIVEIS = [
    {"nome":"Dragaozinho","emoji":"🐲","tipo":"ataque", "desc":"Ataca o inimigo (5-15 dano/turno)","custo":300,
     "acao":lambda j,ini,log: _pet_ataque(j,ini,log,"Dragaozinho","🐲",5,15)},
    {"nome":"Fada",       "emoji":"🧚","tipo":"cura",   "desc":"Cura o jogador (5-12 HP/turno)",  "custo":300,
     "acao":lambda j,ini,log: _pet_cura(j,ini,log,"Fada","🧚",5,12)},
    {"nome":"Lobo",       "emoji":"🐺","tipo":"ataque", "desc":"Ataca com critico (10-25 dano)",  "custo":400,
     "acao":lambda j,ini,log: _pet_critico(j,ini,log,"Lobo","🐺",10,25)},
    {"nome":"Fantasma",   "emoji":"👻","tipo":"debuff",  "desc":"Reduz ATK do inimigo por 1 turno","custo":350,
     "acao":lambda j,ini,log: _pet_debuff(j,ini,log,"Fantasma","👻")},
    {"nome":"Golem",      "emoji":"🪨","tipo":"escudo",  "desc":"Absorve parte do proximo dano",   "custo":450,
     "acao":lambda j,ini,log: _pet_escudo(j,ini,log,"Golem","🪨")},
    {"nome":"Fenix",      "emoji":"🔥","tipo":"reviver", "desc":"Revive uma vez por batalha",      "custo":800,
     "acao":lambda j,ini,log: _pet_fenix(j,ini,log)},
]

def _pet_ataque(j,ini,log,nome,emoji,mn,mx):
    d=random.randint(mn,mx); ini["hp_atual"]-=d
    log.append(C.VERDE+"  "+emoji+" "+nome+" atacou! "+str(d)+" de dano. "+C.RESET)

def _pet_cura(j,ini,log,nome,emoji,mn,mx):
    c=min(random.randint(mn,mx),j.hp_max-j.hp); j.hp+=c
    log.append(C.VERDE+"  "+emoji+" "+nome+" curou +"+str(c)+" HP! "+C.RESET)

def _pet_critico(j,ini,log,nome,emoji,mn,mx):
    crit=random.random()<0.35
    d=random.randint(mn,mx)*(2 if crit else 1)
    ini["hp_atual"]-=d
    log.append(C.VERDE+"  "+emoji+" "+nome+("  CRITICO!" if crit else "")+"! "+str(d)+" dano. "+C.RESET)

def _pet_debuff(j,ini,log,nome,emoji):
    if random.random()<0.6:
        ini["atk_red"]=ini.get("atk_red",0)+1
        log.append(C.VERDE+"  "+emoji+" "+nome+" reduziu ATK do inimigo! "+C.RESET)

def _pet_escudo(j,ini,log,nome,emoji):
    if j.escudo_turns==0:
        j.escudo_turns=1
        log.append(C.VERDE+"  "+emoji+" "+nome+" criou um escudo! "+C.RESET)

def _pet_fenix(j,ini,log):
    if not getattr(j,"fenix_usada",False) and j.hp<=0:
        j.hp=j.hp_max//2; j.fenix_usada=True
        log.append(C.VERMELHO+C.BOLD+"  🔥 Fenix reviveu voce! "+str(j.hp)+" HP! "+C.RESET)

def acao_pet(j,ini,log):
    if j.pet is None: return
    if random.random()<0.75:  # 75% de agir por turno
        j.pet["acao"](j,ini,log)

def loja_pets(j):
    while True:
        limpar(); titulo("LOJA DE PETS","🐾",C.VERDE)
        print(C.LARANJA+"  Gold: "+str(j.gold)+" "+C.RESET)
        if j.pet:
            print(C.VERDE+"  Pet atual: "+j.pet["emoji"]+" "+j.pet["nome"]+" "+C.RESET+"\n")
        else:
            print(C.CINZA+"  Sem pet."+C.RESET+"\n")
        for i,p in enumerate(PETS_DISPONIVEIS,1):
            pode=C.LARANJA if j.gold>=p["custo"] else C.CINZA
            atual=" [ATUAL]" if j.pet and j.pet["nome"]==p["nome"] else ""
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+p["emoji"]+" "+p["nome"]+
                  "  ["+pode+str(p["custo"])+"g"+C.RESET+"]  "+C.CINZA+p["desc"]+C.VERDE+atual+C.RESET)
        print("\n  "+C.CINZA+"0  Sair"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Adotar: "+C.RESET).strip()
        if esc=="0": break
        try:
            idx=int(esc)-1; p=PETS_DISPONIVEIS[idx]
            if j.gold<p["custo"]: print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET); pausar(); continue
            j.gold-=p["custo"]; j.pet=p
            print(C.VERDE+C.BOLD+"\n  "+p["emoji"]+" "+p["nome"]+" adotado! "+C.RESET); pausar()
            novas=checar_conquistas(j); notificar_conquistas(novas)
        except: print(C.VERMELHO+"\n  Invalido! "+C.RESET); pausar()

# ─────────────────────────────────────────
#  CRAFTING
# ─────────────────────────────────────────
RECEITAS = [
    {"nome":"Pocao Suprema",  "emoji":"🌟","resultado":"Elixir Menor",
     "ingredientes":["Pocao Grande","Pocao Grande"],
     "desc":"2x Pocao Grande → Elixir Menor"},
    {"nome":"Mega Eter",      "emoji":"💦","resultado":"Eter Supremo",
     "ingredientes":["Eter Grande","Eter Grande"],
     "desc":"2x Eter Grande → Eter Supremo"},
    {"nome":"Elixir Supremo", "emoji":"✨","resultado":"Elixir",
     "ingredientes":["Elixir Menor","Elixir Menor"],
     "desc":"2x Elixir Menor → Elixir"},
    {"nome":"Antídoto Forte", "emoji":"🌿","resultado":"Pocao Media",
     "ingredientes":["Antidoto","Pocao Pequena"],
     "desc":"Antidoto + Pocao Pequena → Pocao Media"},
    {"nome":"Pedra do Poder", "emoji":"💎","resultado":"Pedra do Caos",
     "ingredientes":["Pedra Magica","Pedra Magica"],
     "desc":"2x Pedra Magica → Pedra do Caos"},
    {"nome":"Artefato Final", "emoji":"⚡","resultado":"Pedra Lendaria",
     "ingredientes":["Pedra do Caos","Elixir"],
     "desc":"Pedra do Caos + Elixir → Pedra Lendaria"},
    {"nome":"Super Antidoto",  "emoji":"🌿","resultado":"Pocao Grande",
     "ingredientes":["Antidoto","Antidoto","Pocao Pequena"],
     "desc":"2x Antidoto + Pocao Pequena → Pocao Grande"},
    {"nome":"Reserva de MP",   "emoji":"💧","resultado":"Eter Supremo",
     "ingredientes":["Eter Medio","Eter Medio","Pedra Magica"],
     "desc":"2x Eter Medio + Pedra Magica → Eter Supremo"},
    {"nome":"Elixir do Caos",  "emoji":"🌀","resultado":"Elixir",
     "ingredientes":["Pocao Grande","Eter Grande","Pedra do Caos"],
     "desc":"Pocao Grande + Eter Grande + Pedra do Caos → Elixir"},
    {"nome":"Lenda Final",     "emoji":"🌟","resultado":"Pedra Lendaria",
     "ingredientes":["Elixir","Pedra Lendaria"],
     "desc":"Elixir + Pedra Lendaria → 2x Pedra Lendaria"},
]

def tela_crafting(j):
    while True:
        limpar(); titulo("CRAFTING","🔨",C.LARANJA)
        print(C.CINZA+"  Itens no inventario: "+str(len(j.inventario))+" "+C.RESET+"\n")
        from collections import Counter
        inv_count=Counter(j.inventario)
        for it,qtd in inv_count.items():
            d=ITENS.get(it,{}); print("  "+d.get("emoji","")+" "+it+" x"+str(qtd))
        print()
        print(C.BOLD+"  Receitas disponíveis:"+C.RESET+"\n")
        for i,r in enumerate(RECEITAS,1):
            tem=all(inv_count.get(ing,0)>=RECEITAS[i-1]["ingredientes"].count(ing)
                    for ing in set(r["ingredientes"]))
            cor_r=C.VERDE if tem else C.CINZA
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+cor_r+r["emoji"]+" "+r["desc"]+" "+C.RESET)
        print("\n  "+C.CINZA+"0  Sair"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Craftar: "+C.RESET).strip()
        if esc=="0": break
        try:
            idx=int(esc)-1; r=RECEITAS[idx]
            inv_count=Counter(j.inventario)
            falta=False
            for ing in r["ingredientes"]:
                if inv_count.get(ing,0)<r["ingredientes"].count(ing):
                    falta=True; break
            if falta: print(C.VERMELHO+"\n  Itens insuficientes! "+C.RESET); pausar(); continue
            # Remove ingredientes
            usados=[]
            for ing in r["ingredientes"]:
                idx_rem=j.inventario.index(ing); j.inventario.pop(idx_rem); usados.append(ing)
            j.inventario.append(r["resultado"])
            j.crafts+=1
            d=ITENS.get(r["resultado"],{})
            print(C.LARANJA+C.BOLD+"\n  "+r["emoji"]+" "+r["resultado"]+" criado! "+C.RESET)
            novas=checar_conquistas(j); notificar_conquistas(novas)
            pausar()
        except Exception as e:
            print(C.VERMELHO+"\n  Erro: "+str(e)+" "+C.RESET); pausar()

# ─────────────────────────────────────────
#  EVENTOS ALEATÓRIOS
# ─────────────────────────────────────────
def evento_aleatorio(j):
    ev=random.randint(1,10)
    limpar(); linha("=",52,C.AMARELO)

    if ev<=2:
        # Mercador misterioso
        print(C.AMARELO+C.BOLD+"\n  🧙 Mercador Misterioso apareceu!\n"+C.RESET)
        item=random.choice(list(ITENS.keys()))
        d=ITENS[item]; preco=max(10,d.get("valor",30)//2)
        print(C.CINZA+"  Ele oferece: "+d["emoji"]+" "+item+" por "+str(preco)+"g "+C.RESET)
        print(C.CINZA+"  Seu gold: "+str(j.gold)+" "+C.RESET+"\n")
        esc=input(C.AMARELO+"  Comprar? (s/n): "+C.RESET).strip().lower()
        if esc=="s":
            if j.gold>=preco:
                j.gold-=preco; j.inventario.append(item)
                print(C.VERDE+"\n  "+d["emoji"]+" "+item+" comprado! "+C.RESET)
            else:
                print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET)
        else:
            print(C.CINZA+"\n  O mercador desapareceu... "+C.RESET)

    elif ev<=4:
        # Tesouro abandonado
        gold=random.randint(20,80)
        j.gold+=gold
        print(C.AMARELO+C.BOLD+"\n  💰 Tesouro Abandonado!\n"+C.RESET)
        print(C.CINZA+"  Voce encontrou "+str(gold)+" gold! "+C.RESET)
        if random.random()<0.4:
            item=random.choice(["Pocao Pequena","Pocao Media","Eter Pequeno","Antidoto"])
            j.inventario.append(item)
            d=ITENS[item]
            print(C.CINZA+"  E tambem: "+d["emoji"]+" "+item+"! "+C.RESET)

    elif ev<=5:
        # Armadilha
        dano=random.randint(10,30)
        j.hp=max(1,j.hp-dano)
        print(C.VERMELHO+C.BOLD+"\n  ⚠ Armadilha!\n"+C.RESET)
        print(C.CINZA+"  Voce caiu numa armadilha! -"+str(dano)+" HP "+C.RESET)
        if j.hp<=10: j.quase_morreu=True

    elif ev<=6:
        # Fonte sagrada
        print(C.CIANO+C.BOLD+"\n  ⛲ Fonte Sagrada!\n"+C.RESET)
        cura=int(j.hp_max*0.3); rec=int(j.mp_max*0.3)
        j.hp=min(j.hp_max,j.hp+cura); j.mp=min(j.mp_max,j.mp+rec)
        print(C.CINZA+"  A fonte restaurou +"+str(cura)+" HP e +"+str(rec)+" MP! "+C.RESET)

    elif ev<=7:
        # Viajante com dica
        dicas=[
            "Itens Conceituais tem efeito de caos a cada turno.",
            "O bobafat aparece apos derrotar o Senhor das Trevas.",
            "Pets agem automaticamente no combate.",
            "Crafting pode criar itens que nao existem nas lojas.",
            "Inimigos Abissais ignoram parte da sua defesa.",
            "Conquistas dao orgulho. Nada mais. Mas vale.",
        ]
        print(C.AZUL+C.BOLD+"\n  🧭 Viajante Misterioso:\n"+C.RESET)
        print(C.CINZA+"  \""+random.choice(dicas)+"\"\n"+C.RESET)

    elif ev<=8:
        # XP bonus
        xp=random.randint(30,100)
        ups=j.ganhar_xp(xp)
        print(C.AMARELO+C.BOLD+"\n  ⭐ Insight de Batalha!\n"+C.RESET)
        print(C.CINZA+"  Reflexao sobre batalhas passadas: +"+str(xp)+" XP! "+C.RESET)
        for nv in ups:
            print(C.CIANO+C.BOLD+"  SUBIU PARA NIVEL "+str(nv)+"! "+C.RESET)

    elif ev<=9:
        # Inimigo fraco quer fugir
        ini_fraco={"nome":"Goblin Covarde","emoji":"🏃","hp":5,"atk":1,"def":0,"xp":5,"gold":5}
        print(C.VERDE+C.BOLD+"\n  🏃 Um Goblin Covarde apareceu!\n"+C.RESET)
        print(C.CINZA+"  Ele implora pra voce nao atacar...\n"+C.RESET)
        esc=input(C.AMARELO+"  Atacar (s) ou deixar ir (n): "+C.RESET).strip().lower()
        if esc=="s":
            j.gold+=5; ups=j.ganhar_xp(5)
            print(C.VERDE+"  +5 XP +5 Gold "+C.RESET)
        else:
            j.gold+=random.randint(1,10)
            print(C.CINZA+"  Ele agradeceu e jogou algumas moedas. "+C.RESET)

    else:
        # Nada de especial
        msgs=["  O vento sopra. Nada acontece.","  Uma folha cai. So isso.",
              "  Voce ouve um barulho... era so o vento.","  Silencio total."]
        print(C.CINZA+C.BOLD+"\n  ...\n"+C.RESET)
        print(C.CINZA+random.choice(msgs)+" "+C.RESET)

    linha("=",52,C.AMARELO); pausar()
    return checar_conquistas(j)

# ─────────────────────────────────────────
#  MODO ARENA
# ─────────────────────────────────────────
def modo_arena(j):
    limpar(); titulo("MODO ARENA","🏟️",C.VERMELHO)
    print(C.CINZA+"  Batalhas infinitas. Sem fuga."+C.RESET)
    print(C.CINZA+"  Recorde atual: "+str(j.arena_recorde)+" ondas"+C.RESET)
    print(C.CINZA+"  A cada 5 ondas: cura parcial e loja rapida."+C.RESET+"\n")
    esc=input(C.AMARELO+"  Entrar na arena? (s/n): "+C.RESET).strip().lower()
    if esc!="s": return

    onda=0; j.fenix_usada=False
    todos_inimigos=[ini for lista in INIMIGOS.values() for ini in lista]

    while True:
        onda+=1
        limpar(); linha("=",52,C.VERMELHO)
        print(C.VERMELHO+C.BOLD+"  🏟️ ARENA — ONDA "+str(onda)+" "+C.RESET)
        print(C.CINZA+"  Recorde: "+str(j.arena_recorde)+" | HP: "+str(j.hp)+"/"+str(j.hp_max)+" "+C.RESET)
        linha("=",52,C.VERMELHO); pausar("  ENTER para batalhar...")

        # Escala dificuldade
        base=random.choice(todos_inimigos)
        mult=1.0+onda*0.15
        ini_arena={
            "nome":base["nome"],"emoji":base["emoji"],
            "hp":int(base["hp"]*mult),"atk":int(base["atk"]*mult),
            "def":int(base.get("def",0)*mult),
            "xp":int(base.get("xp",20)*mult),"gold":int(base.get("gold",10)*mult),
        }
        # Raridade escala com onda
        if onda>=20:   rar_pool=["Epico","Lendario","Mitico","Abissal","Conceitual"]
        elif onda>=10: rar_pool=["Raro","Epico","Lendario","Mitico"]
        elif onda>=5:  rar_pool=["Incomum","Raro","Epico"]
        else:          rar_pool=["Comum","Incomum","Raro"]
        ini_arena=aplicar_raridade_inimigo(ini_arena,random.choice(rar_pool))

        res=batalha(j,ini_arena)
        if res=="derrota":
            limpar(); linha("=",52,C.VERMELHO)
            print(C.VERMELHO+C.BOLD+"\n  Voce foi derrotado na onda "+str(onda)+"!\n"+C.RESET)
            if onda>j.arena_recorde:
                j.arena_recorde=onda
                print(C.AMARELO+C.BOLD+"  Novo recorde: "+str(onda)+" ondas! "+C.RESET)
            linha("=",52,C.VERMELHO)
            novas=checar_conquistas(j); notificar_conquistas(novas)
            pausar(); break

        if onda>j.arena_recorde: j.arena_recorde=onda
        novas=checar_conquistas(j); notificar_conquistas(novas)

        # A cada 5 ondas: descanso e loja
        if onda%5==0:
            limpar(); linha("-",52,C.VERDE)
            print(C.VERDE+C.BOLD+"\n  Onda "+str(onda)+" concluida! Intervalo.\n"+C.RESET)
            cura=int(j.hp_max*0.4); rec=int(j.mp_max*0.5)
            j.hp=min(j.hp_max,j.hp+cura); j.mp=min(j.mp_max,j.mp+rec)
            print(C.CINZA+"  +"+str(cura)+" HP  +"+str(rec)+" MP recuperados."+C.RESET)
            linha("-",52,C.VERDE)
            esc2=input(C.AMARELO+"  Acessar loja rapida? (s/n): "+C.RESET).strip().lower()
            if esc2=="s": loja_itens(j)
            esc3=input(C.AMARELO+"  Continuar na arena? (s/n): "+C.RESET).strip().lower()
            if esc3!="s":
                print(C.CINZA+"\n  Voce saiu da arena na onda "+str(onda)+". "+C.RESET); pausar(); break
# ─────────────────────────────────────────
#  CLASSE JOGADOR
# ─────────────────────────────────────────
XP_NIVEL = [0,80,200,360,560,800,1100,1500,2000,2600,3300,4200,5300,6600,8200,10000,12500,15500,19000,23500,29000]

class Jogador:
    def __init__(self, nome, cls_id):
        cls=CLASSES[cls_id]
        self.nome=nome; self.classe=cls["nome"]; self.emoji=cls["emoji"]; self.cor=cls["cor"]
        self.hp_max=cls["hp"]; self.hp=cls["hp"]
        self.mp_max=cls["mp"]; self.mp=cls["mp"]
        self.atk_base=cls["atk"]; self.defesa_base=cls["defesa"]; self.vel=cls["vel"]
        self.habilidades=list(cls["hab_base"])
        self.nivel=1; self.xp=0; self.gold=150
        self.inventario=[]
        self.arma=ARMAS[0]; self.armadura=ARMADURAS[0]
        self.vitorias=0; self.chefes=0
        # status de batalha
        self.envenenado=0; self.escudo_turns=0; self.evasao_turns=0
        self.buff_atk=0; self.atk_reduzido_turns=0; self.provocar_turns=0
        self.morreu=False
        # novos sistemas
        self.pet=None
        self.conquistas=set()
        self.crafts=0
        self.arena_recorde=0
        self.derrotou_bobafat=False
        self.quase_morreu=False
        self.fenix_usada=False
        self.summons_ativos=[]
        self.titulos=set()
        self.titulo_ativo=None
        self.quests_concluidas=set()
        self.quests_notificadas=set()
        self.reputacao={}
        self.karma=0
        self.historias_vistas=set()
        self.dungeon_recorde=0
        self.derrotou_conceito=False
        self.total_summons=0
        self.areas_visitadas=set()
        self.clima_atual=sortear_clima()
        self.capitulos_vistos=set()
        self.relatorio=None

    @property
    def atk(self):
        b=(self.nivel-1)*2+self.atk_base+self.arma["atk"]
        if self.buff_atk>0: b=int(b*1.3)
        return b

    @property
    def defesa(self):
        return self.defesa_base+(self.nivel-1)*1+self.armadura["def"]

    def ganhar_xp(self, qtd):
        self.xp+=qtd; ups=[]
        while self.nivel<len(XP_NIVEL)-1 and self.xp>=XP_NIVEL[self.nivel]:
            self.nivel+=1; self.hp_max+=12; self.mp_max+=8
            self.hp=self.hp_max; self.mp=self.mp_max
            self.defesa_base+=1; ups.append(self.nivel)
        return ups

    def usar_item(self, idx):
        if idx<0 or idx>=len(self.inventario): return False,"Invalido!"
        it=self.inventario[idx]; dados=ITENS.get(it,{})
        if not dados: return False,"Item desconhecido!"
        msg=""
        if dados["tipo"]=="cura":
            c=min(dados["efeito"],self.hp_max-self.hp); self.hp+=c; msg=f"Recuperou {c}  HP! "
        elif dados["tipo"]=="mp":
            r=min(dados["efeito"],self.mp_max-self.mp); self.mp+=r; msg=f"Recuperou {r}  MP! "
        elif dados["tipo"]=="cura_v":
            self.envenenado=0; msg="Veneno curado! "
        elif dados["tipo"]=="tudo":
            ef=dados["efeito"]
            if ef>=9999: self.hp=self.hp_max; self.mp=self.mp_max
            else: self.hp=min(self.hp_max,self.hp+ef); self.mp=min(self.mp_max,self.mp+ef)
            self.envenenado=0; msg="HP e MP restaurados! "
        self.inventario.pop(idx); return True,msg

    def xp_info(self):
        prox=XP_NIVEL[min(self.nivel,len(XP_NIVEL)-1)]
        base=XP_NIVEL[self.nivel-1] if self.nivel>1 else 0
        return self.xp-base,prox-base

# ─────────────────────────────────────────
#  HUD
# ─────────────────────────────────────────
def hud(j, ini=None):
    xp_a,xp_p=j.xp_info(); print(); linha()
    st=""
    if j.envenenado>0:    st+=" [VEN]"
    if j.escudo_turns>0:  st+=" [ESC]"
    if j.evasao_turns>0:  st+=" [EVA]"
    if j.buff_atk>0:      st+=" [ATK+]"
    print(C.BOLD+j.cor+"  "+j.emoji+" "+j.nome+" "+C.RESET+
          C.AMARELO+"Nv."+str(j.nivel)+" "+C.RESET+C.CINZA+st+C.RESET)
    print("  HP "+barra(j.hp,j.hp_max,16,C.VERDE,C.CINZA)+
          "  "+C.BOLD+str(j.hp)+" "+C.RESET+"/"+str(j.hp_max))
    print("  MP "+barra(j.mp,j.mp_max,16,C.AZUL,C.CINZA)+
          "  "+C.BOLD+C.AZUL+str(j.mp)+" "+C.RESET+"/"+str(j.mp_max))
    print("  XP "+barra(xp_a,max(xp_p,1),16,C.AMARELO,C.CINZA)+
          "  "+C.AMARELO+str(j.xp)+" "+C.RESET)
    rar_arma=j.arma.get("raridade","Comum"); r_arma=RARIDADES.get(rar_arma,RARIDADES["Comum"])
    rar_arm=j.armadura.get("raridade","Comum"); r_arm=RARIDADES.get(rar_arm,RARIDADES["Comum"])
    if j.summons_ativos:
        nomes_s=" ".join(s["emoji"]+"("+str(s["turns_restantes"])+"t)" for s in j.summons_ativos)
        print(C.ROXO+"  Summons: "+nomes_s+" "+C.RESET)
    print("  "+C.LARANJA+"Gold: "+str(j.gold)+" "+C.RESET+
          "  "+C.CINZA+"Arma: "+r_arma["cor"]+j.arma["emoji"]+" "+j.arma["nome"]+" "+C.RESET+
          "  Armor: "+r_arm["cor"]+j.armadura["emoji"]+" "+j.armadura["nome"]+" "+C.RESET)
    if ini:
        print()
        fase_txt=" [FASE "+str(ini.get("fase_atual",1))+"/"+str(ini.get("total_fases",1))+"]" if ini.get("total_fases",1)>1 else ""
        chefe_txt=C.AMARELO+"  [CHEFE"+fase_txt+"]"+C.RESET if ini.get("eh_chefe") else ""
        print(C.BOLD+C.VERMELHO+"  "+ini["emoji"]+" "+ini["nome"]+" "+C.RESET+chefe_txt)
        print("  HP "+barra(ini["hp_atual"],ini["hp_max"],16,C.VERMELHO,C.CINZA)+
              "  "+C.BOLD+C.VERMELHO+str(max(0,ini["hp_atual"]))+" "+C.RESET+"/"+str(ini["hp_max"]))
        sts=""
        if ini.get("veneno_turns",0)>0: sts+=" [VEN "+str(ini["veneno_turns"])+"]"
        if ini.get("atk_red",0)>0:      sts+=" [ATK-"+str(ini["atk_red"])+"]"
        if ini.get("maldito",0)>0:      sts+=" [MAL "+str(ini["maldito"])+"]"
        if sts: print(C.CINZA+"  "+sts+C.RESET)
    linha()

# ─────────────────────────────────────────
#  BATALHA
# ─────────────────────────────────────────
COMPORTAMENTOS = {'Goblin': 'fuga', 'Lobo Sombrio': 'furioso', 'Bandido': 'roubo', 'Planta Carnivora': 'veneno', 'Troll': 'regenerar', 'Morcego Gigante': 'evasivo', 'Esqueleto': 'ressurgir', 'Minotauro': 'furioso', 'Golem de Pedra': 'fortalecer', 'Demonio Menor': 'maldizer', 'Espectro': 'drenar', 'Demonio Maior': 'furioso', 'Lich': 'curar', 'Behemoth': 'esmagar', 'Cavaleiro Negro': 'fortalecer', 'Dragao Anciao': 'bafo', 'Arcanista Sombrio': 'drenar', 'Zumbi': 'infectar', 'Serpente Negra': 'veneno', 'Bruxa do Lodo': 'maldizer', 'Hidrinha': 'regenerar', 'Pedra Animada': 'fortalecer', 'Fantasma Antigo': 'drenar', 'Guardiao Roto': 'berserk_morto', 'Mineiro Morto': 'ressurgir', 'Verme Gigante': 'veneno', 'Golem de Ouro': 'fortalecer', 'Lich Menor': 'curar', 'Banshee': 'terror', 'Cavaleiro Morto': 'ressurgir', 'Elemental de Fogo': 'bafo', 'Demonio de Lava': 'furioso', 'Dragao de Magma': 'bafo'}

def iniciar_inimigo(base, eh_chefe=False, fase=0, total_fases=1):
    ini=dict(base)
    ini["hp_max"]=ini["hp"]; ini["hp_atual"]=ini["hp"]
    ini["veneno_turns"]=0; ini["atk_red"]=0; ini["maldito"]=0
    ini["eh_chefe"]=eh_chefe; ini["fase_atual"]=fase+1; ini["total_fases"]=total_fases
    return ini

def turno_inimigo(j, ini, log, rel=None):
    nome_ini = ini.get("nome","?")
    comp = COMPORTAMENTOS.get(nome_ini, "normal")
    hp_pct = ini["hp_atual"] / max(ini["hp_max"],1)

    # ── Comportamentos especiais ──
    # Fuga: Goblin tenta fugir quando HP < 30%
    if comp=="fuga" and hp_pct < 0.30:
        if random.random() < 0.40:
            log.append(C.CINZA+"  "+ini["emoji"]+" "+nome_ini+" fugiu! "+C.RESET)
            ini["hp_atual"] = 0  # marca como derrotado (fuga = vitória do jogador)
            return

    # Regenerar: recupera HP por turno
    if comp=="regenerar":
        regen = random.randint(6,12)
        ini["hp_atual"] = min(ini["hp_max"], ini["hp_atual"]+regen)
        log.append(C.VERDE+"  "+nome_ini+" regenerou "+str(regen)+" HP! "+C.RESET)

    # Curar: se cura quando HP < 50%
    if comp=="curar" and hp_pct < 0.50 and random.random() < 0.45:
        cura = int(ini["hp_max"]*0.20)
        ini["hp_atual"] = min(ini["hp_max"], ini["hp_atual"]+cura)
        log.append(C.VERDE+"  "+nome_ini+" se curou! +"+str(cura)+" HP "+C.RESET)
        return

    # Ressurgir: revive uma vez com 30% HP
    if comp=="ressurgir" and not ini.get("ressurgiu") and ini["hp_atual"] <= 0:
        ini["hp_atual"] = int(ini["hp_max"]*0.30)
        ini["ressurgiu"] = True
        log.append(C.ROXO+C.BOLD+"  "+nome_ini+" ressurgiu com "+str(ini["hp_atual"])+" HP! "+C.RESET)
        return

    # Fortalecer: DEF cresce a cada turno
    if comp=="fortalecer":
        ini["def"] = ini.get("def",0) + 2
        log.append(C.CIANO+"  "+nome_ini+" se fortaleceu! DEF +2 "+C.RESET)

    # Drenar MP
    if comp=="drenar" and j.mp > 0:
        drain = random.randint(5,15)
        j.mp = max(0, j.mp-drain)
        log.append(C.ROXO+"  "+nome_ini+" drenou "+str(drain)+" MP! "+C.RESET)

    # Terror: chance de paralisar (pula turno do jogador)
    if comp=="terror" and random.random() < 0.20:
        j.provocar_turns = max(j.provocar_turns, 1)
        log.append(C.CINZA+"  "+nome_ini+" te paralisou de medo! "+C.RESET)

    # Furioso: ATK +50% quando HP < 40%
    if comp=="furioso" and hp_pct < 0.40:
        ini["atk"] = int(ini.get("atk",10) * 1.02)  # cresce gradualmente
        log.append(C.VERMELHO+"  "+nome_ini+" ficou furioso! ATK aumentou! "+C.RESET)

    # Evasivo: chance de esquivar do próximo ataque
    if comp=="evasivo" and random.random() < 0.20:
        ini["evasao"] = True
        log.append(C.CINZA+"  "+nome_ini+" esta esquivando! "+C.RESET)

    # ── Ataque normal ──
    usa_esp = ini.get("especial") and random.random()<(0.15 if j.provocar_turns>0 else 0.28)
    atk_ef  = ini.get("atk",10)
    if ini.get("atk_red",0)>0:   atk_ef=int(atk_ef*0.65); ini["atk_red"]-=1
    if ini.get("maldito",0)>0:   atk_ef=int(atk_ef*0.75); ini["maldito"]-=1

    # Bafo: ataque especial a cada 3 turnos
    if comp=="bafo":
        ini["turno_count"] = ini.get("turno_count",0)+1
        if ini["turno_count"]%3==0:
            usa_esp = True
            if not ini.get("especial"): ini["especial"]="Bafo"; ini["mult_esp"]=2.2

    def_ef  = j.defesa//2 if j.escudo_turns>0 else j.defesa//4
    base    = max(1,atk_ef-def_ef)

    # Evasão do jogador
    if j.evasao_turns>0:
        j.evasao_turns-=1
        log.append(C.VERDE+"  Voce esquivou do ataque! "+C.RESET); return

    if usa_esp:
        mult=ini.get("mult_esp",2.0); dano=int(base*mult)
        log.append(C.VERMELHO+C.BOLD+"  "+nome_ini+" usou "+str(ini.get("especial","Especial"))+"! "+str(dano)+" de dano! "+C.RESET)
    else:
        dano=max(1,int(base*random.uniform(0.85,1.15)))
        log.append(C.VERMELHO+"  "+nome_ini+" atacou! "+str(dano)+" de dano. "+C.RESET)

    # Roubo: Bandido rouba gold
    if comp=="roubo" and random.random() < 0.25:
        roubado = random.randint(5,20)
        j.gold = max(0, j.gold-roubado)
        log.append(C.LARANJA+"  "+nome_ini+" roubou "+str(roubado)+" gold! "+C.RESET)

    # Infectar: reduz HP max
    if comp=="infectar" and random.random() < 0.20:
        j.hp_max = max(j.hp_max-5, 10)
        log.append(C.VERMELHO+"  Infeccao! HP max -5! "+C.RESET)

    if j.escudo_turns>0: j.escudo_turns-=1
    if j.buff_atk>0: j.buff_atk-=1
    if j.provocar_turns>0: j.provocar_turns-=1
    dano = aplicar_passiva_pre_dano(j, ini, dano, log)
    dano, absorvido = summon_absorve_dano(j, dano)
    if absorvido > 0:
        log.append(C.AZUL+"  Summon absorveu "+str(absorvido)+" de dano! "+C.RESET)
    j.hp-=dano
    if rel: rel.dano_recebido+=dano

    # veneno inimigo
    if ini.get("veneno_turns",0)>0:
        vd=random.randint(10,18); ini["hp_atual"]-=vd; ini["veneno_turns"]-=1
        log.append(C.VERDE+"  Veneno causou "+str(vd)+" no "+nome_ini+"! "+C.RESET)
    # veneno jogador
    if j.envenenado>0:
        vd=random.randint(6,12); j.hp-=vd; j.envenenado-=1
        log.append(C.VERDE+"  Voce sofreu "+str(vd)+" de veneno! "+C.RESET)

    # Comportamento de veneno/maldizer ativo
    if comp in ("veneno","infectar") and random.random()<0.35 and ini.get("veneno_turns",0)==0:
        j.envenenado = max(j.envenenado, 2)
        log.append(C.VERDE+"  "+nome_ini+" te envenenou! "+C.RESET)
    if comp=="maldizer" and random.random()<0.30:
        j.buff_atk = 0
        log.append(C.CINZA+"  "+nome_ini+" lançou uma maldição! Seus buffs foram removidos! "+C.RESET)


def aplicar_habilidade(j, ini, nome_hab, log):
    h=HABILIDADES.get(nome_hab,{}); 
    if not h: log.append(C.VERMELHO+"  Habilidade invalida! "+C.RESET); return
    if j.mp<h["custo"]: log.append(C.VERMELHO+"  MP insuficiente! ("+str(h["custo"])+" MP) "+C.RESET); return
    j.mp-=h["custo"]; tipo=h["tipo"]
    def_ini=ini.get("def",0)//3

    if tipo=="dano":
        dano=max(1,int((j.atk-def_ini)*h["mult"]))
        ini["hp_atual"]-=dano
        log.append(C.ROXO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano. "+C.RESET)
    elif tipo=="dano_sagrado":
        dano=max(1,int((j.atk-def_ini)*h["mult"]))
        ini["hp_atual"]-=dano; cura=min(10,j.hp_max-j.hp); j.hp+=cura
        log.append(C.AMARELO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano, +"+str(cura)+" HP. "+C.RESET)
    elif tipo=="critico":
        crit=random.random()<0.65; mult=2.5 if crit else h["mult"]
        dano=max(1,int((j.atk-def_ini)*mult))
        ini["hp_atual"]-=dano
        log.append(C.VERDE+C.BOLD+"  "+nome_hab+("  CRITICO!" if crit else "")+"! "+str(dano)+" de dano. "+C.RESET)
    elif tipo=="defesa":
        j.escudo_turns=h["turns"]
        log.append(C.AZUL+C.BOLD+"  "+nome_hab+"! Escudo por "+str(h["turns"])+" turnos. "+C.RESET)
    elif tipo=="evasao":
        j.evasao_turns=h["turns"]
        log.append(C.VERDE+C.BOLD+"  "+nome_hab+"! Proximo ataque sera esquivado. "+C.RESET)
    elif tipo=="berserk":
        dano=max(1,int((j.atk-def_ini)*h["mult"])); ini["hp_atual"]-=dano; j.hp-=15
        log.append(C.VERMELHO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano! (-15 HP) "+C.RESET)
    elif tipo=="lento":
        dano=max(1,int((j.atk-def_ini)*h["mult"])); ini["hp_atual"]-=dano; ini["atk_red"]=3
        log.append(C.CIANO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano + ATK inimigo reduzido! "+C.RESET)
    elif tipo=="veneno":
        dano=max(1,int((j.atk-def_ini)*h["mult"])); ini["hp_atual"]-=dano; ini["veneno_turns"]=3
        log.append(C.VERDE+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano + inimigo envenenado! "+C.RESET)
    elif tipo=="cura":
        c=min(h["efeito"],j.hp_max-j.hp); j.hp+=c
        log.append(C.VERDE+C.BOLD+"  "+nome_hab+"! +"+str(c)+" HP recuperados. "+C.RESET)
    elif tipo=="dreno":
        dano=max(1,int((j.atk-def_ini)*h["mult"])); ini["hp_atual"]-=dano
        c=min(dano//2,j.hp_max-j.hp); j.hp+=c
        log.append(C.ROXO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano, +"+str(c)+" HP drenado. "+C.RESET)
    elif tipo=="maldição":
        dano=max(1,int((j.atk-def_ini)*0.8)); ini["hp_atual"]-=dano
        ini["atk_red"]=h["turns"]; ini["maldito"]=h["turns"]
        log.append(C.CINZA+C.BOLD+"  "+nome_hab+"! ATK e DEF do inimigo reduzidos! "+C.RESET)
    elif tipo=="provocar":
        j.provocar_turns=h["turns"]
        log.append(C.LARANJA+C.BOLD+"  "+nome_hab+"! Inimigo provocado! "+C.RESET)
    elif tipo=="buff":
        j.buff_atk=h["turns"]
        log.append(C.AMARELO+C.BOLD+"  "+nome_hab+"! ATK +30% por "+str(h["turns"])+" turnos. "+C.RESET)
    elif tipo=="reviver":
        log.append(C.AMARELO+C.BOLD+"  "+nome_hab+" guardada para emergencia! "+C.RESET)
        j.morreu=False  # flag de ressurreição disponível
    else:
        dano=max(1,int((j.atk-def_ini)*h.get("mult",1.5))); ini["hp_atual"]-=dano
        log.append(C.ROXO+C.BOLD+"  "+nome_hab+"! "+str(dano)+" de dano. "+C.RESET)

def batalha(j, ini_dados, eh_chefe=False):
    """Retorna 'vitoria', 'derrota' ou 'fuga'"""
    # Chefes com múltiplas fases
    if eh_chefe:
        fases=ini_dados["fases"]; total=len(fases)
        for fi,fase in enumerate(fases):
            ini_base={**ini_dados,"hp":fase["hp"],"atk":fase["atk"],"def":fase["def"],
                     "especial":fase["especial"],"mult_esp":fase["mult_esp"]}
            ini=iniciar_inimigo(ini_base,True,fi,total)
            limpar()
            linha("=",52,C.AMARELO)
            if fi==0:
                print(C.BOLD+C.AMARELO+"\n  CHEFE: "+ini_dados["emoji"]+" "+ini_dados["nome"]+"\n"+C.RESET)
                digitar(C.CINZA+'  "'+fase["fala"]+'"'+C.RESET)
            else:
                print(C.BOLD+C.VERMELHO+"\n  FASE "+str(fi+1)+"! "+ini_dados["nome"]+" TRANSFORMA!\n"+C.RESET)
                digitar(C.CINZA+'  "'+fase["fala"]+'"'+C.RESET)
                # Recupera HP parcial entre fases
                j.hp=min(j.hp_max,j.hp+int(j.hp_max*0.2))
                j.mp=min(j.mp_max,j.mp+int(j.mp_max*0.3))
                print(C.VERDE+"\n  Voce recuperou HP e MP parcialmente! "+C.RESET)
            linha("=",52,C.AMARELO); pausar()
            res=_batalha_loop(j,ini,pode_fugir=False)
            if res=="derrota": return "derrota"
        return "vitoria"
    else:
        ini=iniciar_inimigo(ini_dados)
        ini["raridade"]=ini_dados.get("raridade","Comum")
        ini["efeito"]=ini_dados.get("efeito")
        return _batalha_loop(j,ini,pode_fugir=True)

def _batalha_loop(j,ini,pode_fugir=True):
    log=[]
    while j.hp>0 and ini["hp_atual"]>0:
        limpar()
        clima_b=getattr(j,"clima_atual","ensolarado")
        mostrar_clima(clima_b)
        msg_clima_turno(clima_b,log)
        hud(j,ini)
        if log:
            print()
            for l in log[-5:]: print(l)
            log=[]
        print(); print(C.CINZA+"  Acoes:"+C.RESET)
        print("  "+C.BOLD+C.AMARELO+"1"+C.RESET+"  Atacar")
        for i,nome_h in enumerate(j.habilidades,2):
            h=HABILIDADES.get(nome_h,{})
            c=h.get("custo",0)
            cor_mp=C.AZUL if j.mp>=c else C.CINZA
            print("  "+C.BOLD+C.AMARELO+str(i)+C.RESET+"  "+nome_h+
                  "  "+cor_mp+"["+str(c)+" MP]"+C.RESET+
                  "  "+C.CINZA+h.get("desc","")+" "+C.RESET)
        print("  "+C.BOLD+C.AMARELO+"i"+C.RESET+
              "  Inventario ("+str(len(j.inventario))+" itens)")
        ativos_txt="("+str(len(j.summons_ativos))+" ativo)" if j.summons_ativos else "(nenhum)"
        print("  "+C.BOLD+C.ROXO+"s"+C.RESET+"  Summons "+ativos_txt)
        if pode_fugir:
            print("  "+C.BOLD+C.CINZA+"f"+C.RESET+"  Fugir")
        print()
        acao=input(C.AMARELO+"  Acao: "+C.RESET).strip().lower()

        if acao=="1":
            # Bonus critico de raridade epica
            bonus_crit = 0.20 if j.arma.get("efeito")=="critico_bonus" else 0
            bonus_passiva_crit = bonus_critico_passiva(j)
            # Bonus de clima
            bonus_clima_crit=0.15 if getattr(j,"clima_atual","")=="noite" else 0
            crit=random.random()<(0.22+bonus_crit+bonus_clima_crit+bonus_passiva_crit if j.classe=="Arqueiro" else 0.10+bonus_crit+bonus_clima_crit+bonus_passiva_crit)
            # Ignorar defesa (Abissal)
            def_ef = ini.get("def",0)//3
            if j.arma.get("efeito")=="ignorar_def":
                def_ef = def_ef//2
            mult_clima=1.05 if getattr(j,"clima_atual","")=="ensolarado" else 1.0
            mult_passiva=bonus_dano_passiva(j)
            dano=max(1,int((j.atk-def_ef)*(1.9 if crit else 1.0)*random.uniform(0.88,1.12)*mult_clima*mult_passiva))
            ini["hp_atual"]-=dano
            rel.dano_causado+=dano
            if crit: rel.criticos+=1
            log.append(C.BRANCO+"  Ataque"+("  CRITICO!" if crit else "")+"! "+str(dano)+" de dano. "+C.RESET)
            aplicar_passiva_pos_ataque(j,ini,dano,log)
            # Vampirismo (Mitico)
            if j.arma.get("efeito")=="vampirismo":
                roubo=max(1,int(dano*0.15)); j.hp=min(j.hp_max,j.hp+roubo)
                log.append(C.VERMELHO+"  [Mitico] Vampirismo: +"+str(roubo)+" HP "+C.RESET)
            # Caos (Conceitual)
            elif j.arma.get("efeito")=="caos":
                op=random.choice(["cura","dano_extra","mp","nada"])
                if op=="cura": j.hp=min(j.hp_max,j.hp+20); log.append(C.CIANO+"  [Conceitual] Caos: +20 HP! "+C.RESET)
                elif op=="dano_extra": ed=random.randint(10,60); ini["hp_atual"]-=ed; log.append(C.CIANO+"  [Conceitual] Caos: +"+str(ed)+" dano extra! "+C.RESET)
                elif op=="mp": j.mp=min(j.mp_max,j.mp+25); log.append(C.CIANO+"  [Conceitual] Caos: +25 MP! "+C.RESET)
                else: log.append(C.CIANO+"  [Conceitual] Caos: nada aconteceu... "+C.RESET)
            # Regen de armadura
            if j.armadura.get("efeito")=="regen_hp" and j.hp<j.hp_max:
                j.hp=min(j.hp_max,j.hp+5); log.append(C.VERDE+"  [Incomum] Regen: +5 HP "+C.RESET)
            elif j.armadura.get("efeito")=="regen_mp" and j.mp<j.mp_max:
                j.mp=min(j.mp_max,j.mp+5); log.append(C.AZUL+"  [Raro] Regen: +5 MP "+C.RESET)
            # Clima tempestade: MP extra
            if getattr(j,"clima_atual","")=="tempestade" and j.mp<j.mp_max:
                j.mp=min(j.mp_max,j.mp+4); log.append(C.ROXO+"  [Tempestade] +4 MP "+C.RESET)

        elif acao.isdigit() and 2<=int(acao)<=len(j.habilidades)+1:
            nome_h=j.habilidades[int(acao)-2]
            aplicar_habilidade(j,ini,nome_h,log)

        elif acao=="i":
            if not j.inventario:
                log.append(C.CINZA+"  Inventario vazio! "+C.RESET); continue
            limpar(); linha()
            print(C.BOLD+C.AMARELO+"  INVENTARIO"+C.RESET); linha()
            for i,it in enumerate(j.inventario):
                d=ITENS.get(it,{}); print("  "+C.AMARELO+str(i+1)+C.RESET+
                "  "+d.get("emoji","")+" "+it+"  "+C.CINZA+d.get("desc","")+" "+C.RESET)
            print("  "+C.CINZA+"0  Cancelar"+C.RESET+"\n")
            try:
                idx=int(input(C.AMARELO+"  Usar: "+C.RESET))-1
                if idx<0: continue
                ok,msg=j.usar_item(idx)
                log.append((C.VERDE if ok else C.VERMELHO)+"  "+msg+C.RESET)
            except: pass
            continue

        elif acao=="s":
            menu_summons(j); continue
        elif pode_fugir and acao=="f":
            if random.random()<0.5:
                print(C.CINZA+"\n  Voce fugiu! "+C.RESET); pausar(); return "fuga"
            else:
                log.append(C.VERMELHO+"  Fuga falhou! "+C.RESET)
        else:
            log.append(C.VERMELHO+"  Acao invalida! "+C.RESET); continue

        if ini["hp_atual"]<=0: break
        aplicar_passivas_turno(j,ini,log)
        turno_inimigo(j,ini,log,rel)
        acao_pet(j,ini,log)
        agir_todos_summons(j,ini,log)
        # Checa quase morreu
        if j.hp<=10 and j.hp>0: j.quase_morreu=True

    limpar()
    if j.hp<=0:
        linha("=",52,C.VERMELHO)
        print(C.BOLD+C.VERMELHO+"\n  VOCE FOI DERROTADO...\n"+C.RESET)
        digitar(C.CINZA+"  A escuridao te envolve..."+C.RESET)
        linha("=",52,C.VERMELHO); pausar(); return "derrota"

    # Vitória
    hud(j); linha("=",52,C.AMARELO)
    print(C.BOLD+C.AMARELO+"\n  VITORIA! "+ini["emoji"]+" "+ini["nome"]+" derrotado!\n"+C.RESET)
    xp_g=ini_dados["xp"] if hasattr(ini_dados,"get") and ini_dados.get("xp") else ini.get("xp",30)
    gold_g=ini_dados.get("gold",10) if hasattr(ini_dados,"get") else ini.get("gold",10)
    gold_g+=random.randint(0,15)
    j.gold+=gold_g; ups=j.ganhar_xp(xp_g)
    print("  +"+C.AMARELO+str(xp_g)+C.RESET+" XP   +"+C.LARANJA+str(gold_g)+C.RESET+" Gold")
    for nv in ups:
        print(C.CIANO+C.BOLD+"\n  SUBIU PARA NIVEL "+str(nv)+"! HP e MP restaurados! "+C.RESET)
    j.vitorias+=1
    for p in PASSIVAS.get(j.classe,[]):
        if p["gatilho"]=="pos_vitoria" and p["efeito"]:
            try: p["efeito"](j,[])
            except: pass
    linha("=",52,C.AMARELO); pausar(); return "vitoria"

# Corrige o acesso a ini_dados dentro de _batalha_loop
# passando os dados originais corretamente
_batalha_loop_orig=_batalha_loop
def _batalha_loop(j,ini,pode_fugir=True):
    log=[]
    ini_dados=ini
    rel=Relatorio()
    ini_nome_rel=ini.get("nome","?")
    while j.hp>0 and ini["hp_atual"]>0:
        rel.turnos+=1
        limpar()
        clima_b=getattr(j,"clima_atual","ensolarado")
        mostrar_clima(clima_b)
        msg_clima_turno(clima_b,log)
        hud(j,ini)
        if log:
            print()
            for l in log[-5:]: print(l)
            log=[]
        print(); print(C.CINZA+"  Acoes:"+C.RESET)
        print("  "+C.BOLD+C.AMARELO+"1"+C.RESET+"  Atacar")
        for i,nome_h in enumerate(j.habilidades,2):
            h=HABILIDADES.get(nome_h,{})
            c=h.get("custo",0)
            cor_mp=C.AZUL if j.mp>=c else C.CINZA
            print("  "+C.BOLD+C.AMARELO+str(i)+C.RESET+"  "+nome_h+
                  "  "+cor_mp+"["+str(c)+" MP]"+C.RESET+
                  "  "+C.CINZA+h.get("desc","")+" "+C.RESET)
        print("  "+C.BOLD+C.AMARELO+"i"+C.RESET+
              "  Inventario ("+str(len(j.inventario))+" itens)")
        ativos_txt="("+str(len(j.summons_ativos))+" ativo)" if j.summons_ativos else "(nenhum)"
        print("  "+C.BOLD+C.ROXO+"s"+C.RESET+"  Summons "+ativos_txt)
        if pode_fugir:
            print("  "+C.BOLD+C.CINZA+"f"+C.RESET+"  Fugir")
        print()
        acao=input(C.AMARELO+"  Acao: "+C.RESET).strip().lower()

        if acao=="1":
            # Bonus critico de raridade epica
            bonus_crit = 0.20 if j.arma.get("efeito")=="critico_bonus" else 0
            bonus_passiva_crit = bonus_critico_passiva(j)
            # Bonus de clima
            bonus_clima_crit=0.15 if getattr(j,"clima_atual","")=="noite" else 0
            crit=random.random()<(0.22+bonus_crit+bonus_clima_crit+bonus_passiva_crit if j.classe=="Arqueiro" else 0.10+bonus_crit+bonus_clima_crit+bonus_passiva_crit)
            # Ignorar defesa (Abissal)
            def_ef = ini.get("def",0)//3
            if j.arma.get("efeito")=="ignorar_def":
                def_ef = def_ef//2
            mult_clima=1.05 if getattr(j,"clima_atual","")=="ensolarado" else 1.0
            mult_passiva=bonus_dano_passiva(j)
            dano=max(1,int((j.atk-def_ef)*(1.9 if crit else 1.0)*random.uniform(0.88,1.12)*mult_clima*mult_passiva))
            ini["hp_atual"]-=dano
            rel.dano_causado+=dano
            if crit: rel.criticos+=1
            log.append(C.BRANCO+"  Ataque"+("  CRITICO!" if crit else "")+"! "+str(dano)+" de dano. "+C.RESET)
            aplicar_passiva_pos_ataque(j,ini,dano,log)
            # Vampirismo (Mitico)
            if j.arma.get("efeito")=="vampirismo":
                roubo=max(1,int(dano*0.15)); j.hp=min(j.hp_max,j.hp+roubo)
                log.append(C.VERMELHO+"  [Mitico] Vampirismo: +"+str(roubo)+" HP "+C.RESET)
            # Caos (Conceitual)
            elif j.arma.get("efeito")=="caos":
                op=random.choice(["cura","dano_extra","mp","nada"])
                if op=="cura": j.hp=min(j.hp_max,j.hp+20); log.append(C.CIANO+"  [Conceitual] Caos: +20 HP! "+C.RESET)
                elif op=="dano_extra": ed=random.randint(10,60); ini["hp_atual"]-=ed; log.append(C.CIANO+"  [Conceitual] Caos: +"+str(ed)+" dano extra! "+C.RESET)
                elif op=="mp": j.mp=min(j.mp_max,j.mp+25); log.append(C.CIANO+"  [Conceitual] Caos: +25 MP! "+C.RESET)
                else: log.append(C.CIANO+"  [Conceitual] Caos: nada aconteceu... "+C.RESET)
            # Regen de armadura
            if j.armadura.get("efeito")=="regen_hp" and j.hp<j.hp_max:
                j.hp=min(j.hp_max,j.hp+5); log.append(C.VERDE+"  [Incomum] Regen: +5 HP "+C.RESET)
            elif j.armadura.get("efeito")=="regen_mp" and j.mp<j.mp_max:
                j.mp=min(j.mp_max,j.mp+5); log.append(C.AZUL+"  [Raro] Regen: +5 MP "+C.RESET)
            # Clima tempestade: MP extra
            if getattr(j,"clima_atual","")=="tempestade" and j.mp<j.mp_max:
                j.mp=min(j.mp_max,j.mp+4); log.append(C.ROXO+"  [Tempestade] +4 MP "+C.RESET)

        elif acao.isdigit() and 2<=int(acao)<=len(j.habilidades)+1:
            nome_h=j.habilidades[int(acao)-2]
            aplicar_habilidade(j,ini,nome_h,log)

        elif acao=="i":
            if not j.inventario:
                log.append(C.CINZA+"  Inventario vazio! "+C.RESET); continue
            limpar(); linha()
            print(C.BOLD+C.AMARELO+"  INVENTARIO"+C.RESET); linha()
            for i,it in enumerate(j.inventario):
                d=ITENS.get(it,{}); print("  "+C.AMARELO+str(i+1)+C.RESET+
                "  "+d.get("emoji","")+" "+it+"  "+C.CINZA+d.get("desc","")+" "+C.RESET)
            print("  "+C.CINZA+"0  Cancelar"+C.RESET+"\n")
            try:
                idx=int(input(C.AMARELO+"  Usar: "+C.RESET))-1
                if idx<0: continue
                ok,msg=j.usar_item(idx)
                log.append((C.VERDE if ok else C.VERMELHO)+"  "+msg+C.RESET)
            except: pass
            continue

        elif acao=="s":
            menu_summons(j); continue
        elif pode_fugir and acao=="f":
            if random.random()<0.5:
                print(C.CINZA+"\n  Voce fugiu! "+C.RESET); pausar(); return "fuga"
            else:
                log.append(C.VERMELHO+"  Fuga falhou! "+C.RESET)
        else:
            log.append(C.VERMELHO+"  Acao invalida! "+C.RESET); continue

        if ini["hp_atual"]<=0: break
        aplicar_passivas_turno(j,ini,log)
        turno_inimigo(j,ini,log,rel)
        acao_pet(j,ini,log)
        agir_todos_summons(j,ini,log)
        # Checa quase morreu
        if j.hp<=10 and j.hp>0: j.quase_morreu=True

    limpar()
    if j.hp<=0:
        linha("=",52,C.VERMELHO)
        print(C.BOLD+C.VERMELHO+"\n  VOCE FOI DERROTADO...\n"+C.RESET)
        digitar(C.CINZA+"  A escuridao te envolve..."+C.RESET)
        linha("=",52,C.VERMELHO); pausar(); return "derrota"

    hud(j); linha("=",52,C.AMARELO)
    rar_ini = ini.get("raridade","Comum")
    r_dados = RARIDADES.get(rar_ini, RARIDADES["Comum"])
    nome_display = r_dados["cor"]+C.BOLD+r_dados["emoji"]+" "+ini["nome"]+" "+C.RESET
    print(C.BOLD+C.AMARELO+"\n  VITORIA! "+nome_display+C.AMARELO+" derrotado!\n"+C.RESET)
    xp_g=ini.get("xp",30); gold_g=ini.get("gold",10)+random.randint(0,15)
    # Double gold se arma tem efeito lendario
    if j.arma.get("efeito")=="double_gold":
        gold_g*=2
        print(C.AMARELO+C.BOLD+"  [Lendario] Double Gold! "+C.RESET)
    j.gold+=gold_g; ups=j.ganhar_xp(xp_g)
    print("  +"+C.AMARELO+str(xp_g)+C.RESET+" XP   +"+C.LARANJA+str(gold_g)+C.RESET+" Gold")
    if rar_ini not in ("Comum","Incomum"):
        print(r_dados["cor"]+"  Inimigo "+rar_ini+": bonus aplicado! "+C.RESET)
    for nv in ups:
        print(C.CIANO+C.BOLD+"\n  SUBIU PARA NIVEL "+str(nv)+"! HP e MP restaurados! "+C.RESET)
    j.vitorias+=1
    j.summons_ativos=[]
    for p in PASSIVAS.get(j.classe,[]):
        if p["gatilho"]=="pos_vitoria" and p["efeito"]:
            try: p["efeito"](j,[])
            except: pass
    rel.mostrar(ini_nome_rel)
    novas_q=checar_quests(j); notificar_quests(novas_q)
    novos_t=checar_titulos(j)
    for t in novos_t: print(C.AMARELO+C.BOLD+"  🏅 TITULO DESBLOQUEADO: "+t["emoji"]+" "+t["nome"]+" "+C.RESET)
    novas=checar_conquistas(j); notificar_conquistas(novas)
    linha("=",52,C.AMARELO); pausar(); return "vitoria"

# ─────────────────────────────────────────
#  LOJAS
# ─────────────────────────────────────────
def loja_itens(j):
    itens_loja=["Pocao Pequena","Pocao Media","Pocao Grande",
                "Eter Pequeno","Eter Medio","Eter Grande","Antidoto","Elixir Menor"]
    while True:
        limpar(); titulo("LOJA DE ITENS","🧪",C.VERDE)
        print(C.LARANJA+"  Gold: "+str(j.gold)+" "+C.RESET+"\n")
        for i,nome in enumerate(itens_loja,1):
            d=ITENS[nome]; pode=C.LARANJA if j.gold>=d["valor"] else C.CINZA
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+d["emoji"]+" "+nome+
                  "  ["+pode+str(d["valor"])+"g"+C.RESET+"]  "+C.CINZA+d["desc"]+" "+C.RESET)
        print("\n  "+C.CINZA+"0  Sair"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Comprar: "+C.RESET).strip()
        if esc=="0": break
        try:
            idx=int(esc)-1; nome=itens_loja[idx]; d=ITENS[nome]
            if j.gold<d["valor"]: print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET); pausar(); continue
            j.gold-=d["valor"]; j.inventario.append(nome)
            print(C.VERDE+"\n  "+d["emoji"]+" "+nome+" comprado! "+C.RESET); pausar()
        except: print(C.VERMELHO+"\n  Invalido! "+C.RESET); pausar()

def loja_equipamentos(j):
    while True:
        limpar(); titulo("LOJA DE EQUIPAMENTOS","⚔️",C.CIANO)
        print(C.LARANJA+"  Gold: "+str(j.gold)+" "+C.RESET)
        print(C.CINZA+"  Arma atual: "+j.arma["emoji"]+" "+j.arma["nome"]+" (ATK +"+str(j.arma["atk"])+")")
        print("  Armor atual: "+j.armadura["emoji"]+" "+j.armadura["nome"]+" (DEF +"+str(j.armadura["def"])+")"+C.RESET+"\n")
        print(C.BOLD+"  ARMAS:"+C.RESET)
        armas_disp=[a for a in ARMAS if a["tier"]>0 and (a["tipo"]=="todos" or a["tipo"]==j.classe)]
        for i,a in enumerate(armas_disp,1):
            pode=C.LARANJA if j.gold>=a["valor"] else C.CINZA
            atual=" [EQUIPADA]" if a["nome"]==j.arma["nome"] else ""
            rar_a=a.get("raridade","Comum"); r_a=RARIDADES.get(rar_a,RARIDADES["Comum"])
            ef_txt=" ("+EFEITOS_DESC[a["efeito"]]+")" if a.get("efeito") and a["efeito"] in EFEITOS_DESC else ""
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+r_a["cor"]+a["emoji"]+" "+a["nome"]+C.RESET+
                  " ATK+"+str(a["atk"])+"  ["+pode+str(a["valor"])+"g"+C.RESET+"]"+
                  C.CINZA+ef_txt+C.RESET+C.VERDE+atual+C.RESET)
        print()
        print(C.BOLD+"  ARMADURAS:"+C.RESET)
        arms_disp=[a for a in ARMADURAS if a["tier"]>0 and (a["tipo"]=="todos" or a["tipo"]==j.classe)]
        base=len(armas_disp)
        for i,a in enumerate(arms_disp,base+1):
            pode=C.LARANJA if j.gold>=a["valor"] else C.CINZA
            atual=" [EQUIPADA]" if a["nome"]==j.armadura["nome"] else ""
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+a["emoji"]+" "+a["nome"]+
                  " DEF+"+str(a["def"])+"  ["+pode+str(a["valor"])+"g"+C.RESET+"]"+C.VERDE+atual+C.RESET)
        print("\n  "+C.CINZA+"0  Sair"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Comprar: "+C.RESET).strip()
        if esc=="0": break
        try:
            idx=int(esc)-1
            if idx<len(armas_disp):
                a=armas_disp[idx]
                if j.gold<a["valor"]: print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET); pausar(); continue
                j.gold-=a["valor"]; j.arma=a
                print(C.VERDE+"\n  "+a["emoji"]+" "+a["nome"]+" equipada! "+C.RESET); pausar()
            else:
                a=arms_disp[idx-len(armas_disp)]
                if j.gold<a["valor"]: print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET); pausar(); continue
                j.gold-=a["valor"]; j.armadura=a
                print(C.VERDE+"\n  "+a["emoji"]+" "+a["nome"]+" equipada! "+C.RESET); pausar()
        except: print(C.VERMELHO+"\n  Invalido! "+C.RESET); pausar()

def loja_habilidades(j):
    disponiveis=HAB_DESBLOQUEAVEL.get(j.classe,[])
        
    while True:
        limpar(); titulo("LOJA DE HABILIDADES","✨",C.ROXO)
        print(C.LARANJA+"  Gold: "+str(j.gold)+" "+C.RESET+"\n")
        print(C.CINZA+"  Habilidades atuais: "+", ".join(j.habilidades)+C.RESET+"\n")
        tem_algo=False
        for i,(nome,custo) in enumerate(disponiveis,1):
            if nome in j.habilidades:
                print("  "+C.CINZA+str(i)+"  "+nome+" [JA APRENDIDA]"+C.RESET)
            else:
                tem_algo=True
                pode=C.LARANJA if j.gold>=custo else C.CINZA
                h=HABILIDADES.get(nome,{})
                print("  "+C.AMARELO+str(i)+C.RESET+"  "+nome+
                      "  ["+pode+str(custo)+"g"+C.RESET+"]  "+C.CINZA+h.get("desc","")+" "+C.RESET)
        if not tem_algo:
            print(C.VERDE+"\n  Todas as habilidades desbloqueadas! "+C.RESET)
        print("\n  "+C.CINZA+"0  Sair"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Desbloquear: "+C.RESET).strip()
        if esc=="0": break
        try:
            idx=int(esc)-1; nome,custo=disponiveis[idx]
            if nome in j.habilidades: print(C.CINZA+"\n  Ja aprendida! "+C.RESET); pausar(); continue
            if j.gold<custo: print(C.VERMELHO+"\n  Gold insuficiente! "+C.RESET); pausar(); continue
            j.gold-=custo; j.habilidades.append(nome)
            print(C.ROXO+C.BOLD+"\n  "+nome+" aprendida! "+C.RESET); pausar()
        except: print(C.VERMELHO+"\n  Invalido! "+C.RESET); pausar()

# ─────────────────────────────────────────
#  STATUS
# ─────────────────────────────────────────
def ver_status(j):
    limpar(); titulo("STATUS","📊",C.CIANO)
    print(C.BOLD+j.cor+"  "+j.emoji+" "+j.nome+"  — "+j.classe+"  "+C.RESET)
    print()
    print("  Nivel    "+C.AMARELO+C.BOLD+str(j.nivel)+" "+C.RESET)
    print("  XP       "+C.AMARELO+str(j.xp)+" "+C.RESET)
    print("  HP       "+C.VERDE+str(j.hp)+" "+C.RESET+"/"+str(j.hp_max))
    print("  MP       "+C.AZUL+str(j.mp)+" "+C.RESET+"/"+str(j.mp_max))
    print("  ATK      "+C.VERMELHO+str(j.atk)+" "+C.RESET+" (base "+str(j.atk_base)+" + arma "+str(j.arma["atk"])+")")
    print("  DEF      "+C.CIANO+str(j.defesa)+" "+C.RESET+" (base "+str(j.defesa_base)+" + armor "+str(j.armadura["def"])+")")
    print("  Gold     "+C.LARANJA+str(j.gold)+" "+C.RESET)
    print("  Vitorias "+C.AMARELO+str(j.vitorias)+" "+C.RESET+" ("+str(j.chefes)+" chefes)")
    print()
    print(C.BOLD+"  Equipamentos:"+C.RESET)
    rar_a=j.arma.get("raridade","Comum"); r_a=RARIDADES.get(rar_a,RARIDADES["Comum"])
    rar_b=j.armadura.get("raridade","Comum"); r_b=RARIDADES.get(rar_b,RARIDADES["Comum"])
    ef_a=(" | "+EFEITOS_DESC[j.arma["efeito"]]) if j.arma.get("efeito") and j.arma["efeito"] in EFEITOS_DESC else ""
    ef_b=(" | "+EFEITOS_DESC[j.armadura["efeito"]]) if j.armadura.get("efeito") and j.armadura["efeito"] in EFEITOS_DESC else ""
    print("  Arma:    "+r_a["cor"]+j.arma["emoji"]+" "+j.arma["nome"]+" ["+rar_a+"] ATK+"+str(j.arma["atk"])+ef_a+" "+C.RESET)
    print("  Armor:   "+r_b["cor"]+j.armadura["emoji"]+" "+j.armadura["nome"]+" ["+rar_b+"] DEF+"+str(j.armadura["def"])+ef_b+" "+C.RESET)
    print()
    print(C.BOLD+"  Habilidades:"+C.RESET)
    for h in j.habilidades:
        d=HABILIDADES.get(h,{}); print("  "+C.ROXO+h+C.RESET+"  ["+str(d.get("custo",0))+" MP]  "+C.CINZA+d.get("desc","")+" "+C.RESET)
    print()
    print(C.BOLD+"  Inventario ("+str(len(j.inventario))+" itens):"+C.RESET)
    if j.inventario:
        from collections import Counter
        for nome,qtd in Counter(j.inventario).items():
            d=ITENS.get(nome,{}); print("  "+d.get("emoji","")+" "+nome+" x"+str(qtd)+"  "+C.CINZA+d.get("desc","")+" "+C.RESET)
    else: print(C.CINZA+"  (vazio)"+C.RESET)
    linha(); pausar()

# ─────────────────────────────────────────
#  EXPLORAÇÃO
# ─────────────────────────────────────────
def menu_area(j, area_id):
    area=MAPA[area_id]; inimigos=INIMIGOS[area_id]
    chefe=next((c for c in CHEFES if c["area"]==area_id),None)
    bat=0; max_bat=area["bat"]; drops=DROPS_AREA[area_id]

    j.areas_visitadas.add(area_id)
    verificar_narrativa(j, area_id)
    j.clima_atual = sortear_clima()
    while bat<max_bat:
        limpar()
        # Cabeçalho da área (apenas uma vez por tela)
        linha("=",52,C.VERDE)
        print(C.BOLD+C.VERDE+"\n  "+area["emoji"]+"  "+area["nome"]+"  "+C.RESET)
        print(C.CINZA+"  "+area["desc"]+C.RESET)
        linha("=",52,C.VERDE)
        # Muda clima só a cada 2 batalhas
        if bat>0 and bat%2==0:
            j.clima_atual=sortear_clima()
        mostrar_clima_visual(j.clima_atual)
        print(C.CINZA+"\n  Batalhas: "+str(bat)+"/"+str(max_bat)+
              "  Gold: "+str(j.gold)+
              "  HP: "+str(j.hp)+"/"+str(j.hp_max)+"\n"+C.RESET)
        print("  "+C.AMARELO+"1"+C.RESET+"  Explorar (batalha)")
        print("  "+C.AMARELO+"2"+C.RESET+"  Loja de itens")
        print("  "+C.AMARELO+"3"+C.RESET+"  Loja de equipamentos")
        print("  "+C.AMARELO+"4"+C.RESET+"  Loja de habilidades")
        print("  "+C.AMARELO+"5"+C.RESET+"  Ver status")
        print("  "+C.AMARELO+"6"+C.RESET+"  Usar item")
        print("  "+C.AMARELO+"7"+C.RESET+"  Crafting 🔨")
        print("  "+C.AMARELO+"8"+C.RESET+"  Pets 🐾")
        print("  "+C.AMARELO+"9"+C.RESET+"  Arena 🏟️")
        print("  "+C.AMARELO+"10"+C.RESET+" Conquistas 🏆")
        print("  "+C.AMARELO+"11"+C.RESET+" Summons 🔮")
        print("  "+C.AMARELO+"12"+C.RESET+" Quests 📜")
        print("  "+C.AMARELO+"13"+C.RESET+" Facoes 🏰")
        print("  "+C.AMARELO+"14"+C.RESET+" Titulos 🏅")
        print("  "+C.AMARELO+"15"+C.RESET+" Dungeon 🏚️")
        print("  "+C.AMARELO+"16"+C.RESET+" Gerenciar inventario 🎒")
        print("  "+C.AMARELO+"17"+C.RESET+" Magias Passivas 🔮")
        print("  "+C.CINZA+"s"+C.RESET+"  Salvar jogo 💾")
        if bat==max_bat-1 and chefe:
            print(C.AMARELO+C.BOLD+"\n  Proximo: CHEFE "+chefe['emoji']+" "+chefe['nome']+"!"+C.RESET)
        print()
        esc=input(C.AMARELO+"  Escolha: "+C.RESET).strip()

        if esc=="1":
            # Evento aleatorio ou historia
            if random.random()<0.20:
                r=random.random()
                if r<0.4 and len(j.historias_vistas)<len(HISTORIA_EVENTOS):
                    evento_historia(j)
                else:
                    novas=evento_aleatorio(j); notificar_conquistas(novas)
            # Reputacao por batalhas
            ganhar_reputacao(j,[])
            ini_base=dict(random.choice(inimigos))
            ini=aplicar_raridade_inimigo(ini_base)
            # Avisa se raridade especial
            rar=ini.get("raridade","Comum")
            if rar not in ("Comum","Incomum"):
                r=RARIDADES[rar]
                print("\n"+r["cor"]+C.BOLD+"  "+r["emoji"]+" INIMIGO "+rar.upper()+" DETECTADO!"+C.RESET)
                if ini.get("efeito") and ini["efeito"] in EFEITOS_DESC:
                    print(C.CINZA+"  Efeito especial: "+EFEITOS_DESC[ini["efeito"]]+" "+C.RESET)
                pausar("  ENTER para batalhar...")
            res=batalha(j,ini)
            if res=="derrota": return "derrota"
            if res=="vitoria":
                bat+=1
                # Drop de item com raridade
                for nome_drop,chance in drops:
                    if random.random()<chance:
                        rar_drop=sortear_raridade()
                        j.inventario.append(nome_drop)
                        d=ITENS.get(nome_drop,{})
                        r_d=RARIDADES[rar_drop]
                        print(C.VERDE+"  Drop: "+r_d["cor"]+C.BOLD+r_d["emoji"]+" "+nome_drop+" ["+rar_drop+"]"+C.RESET)
                        pausar("  ENTER..."); break
                # Chance de drop de equip raro
                if random.random()<0.12:
                    pool_armas=[a for a in ARMAS if a["tier"]>0 and (a["tipo"]=="todos" or a["tipo"]==j.classe)]
                    if pool_armas:
                        base_arma=random.choice(pool_armas)
                        rar_eq=sortear_raridade()
                        eq=aplicar_raridade_equip(base_arma,rar_eq)
                        if eq["atk"]>j.arma["atk"]:
                            j.arma=eq
                            r_e=RARIDADES[rar_eq]
                            print(r_e["cor"]+C.BOLD+"  Drop Equip: "+r_e["emoji"]+" "+eq["nome"]+" ["+rar_eq+"] equipada! "+C.RESET)
                            pausar("  ENTER...")
        elif esc=="2": loja_itens(j)
        elif esc=="3": loja_equipamentos(j)
        elif esc=="4": loja_habilidades(j)
        elif esc=="5": ver_status(j)
        elif esc=="6":
            if not j.inventario: print(C.CINZA+"\n  Inventario vazio! "+C.RESET); pausar(); continue
            limpar(); linha()
            print(C.BOLD+C.AMARELO+"  INVENTARIO"+C.RESET); linha()
            for i,it in enumerate(j.inventario):
                d=ITENS.get(it,{}); print("  "+C.AMARELO+str(i+1)+C.RESET+"  "+d.get("emoji","")+" "+it+"  "+C.CINZA+d.get("desc","")+" "+C.RESET)
            print("  "+C.CINZA+"0  Cancelar"+C.RESET+"\n")
            try:
                idx=int(input(C.AMARELO+"  Usar: "+C.RESET))-1
                if idx<0: continue
                ok,msg=j.usar_item(idx)
                print((C.VERDE if ok else C.VERMELHO)+"\n  "+msg+C.RESET); pausar()
            except: pass
        elif esc=="7": tela_crafting(j)
        elif esc=="8": loja_pets(j)
        elif esc=="9": modo_arena(j)
        elif esc=="10": mostrar_conquistas(j)
        elif esc=="11": menu_summons(j)
        elif esc=="12": tela_quests(j)
        elif esc=="13": tela_facoes(j)
        elif esc=="14": mostrar_titulos(j)
        elif esc=="15": modo_dungeon(j)
        elif esc=="16": tela_inventario_gerenciar(j)
        elif esc=="17": mostrar_passivas(j)
        elif esc=="s":
            if salvar_jogo(j, areas_desbloqueadas if "areas_desbloqueadas" in dir() else ["floresta"]):
                print(C.VERDE+"\n  Jogo salvo! "+C.RESET); pausar()

    # Chefe
    if chefe:
        res=batalha(j,chefe,eh_chefe=True)
        if res=="derrota": return "derrota"
        j.chefes+=1
        # Drop garantido de equip após chefe
        armas_tier=j.chefes; arms=[a for a in ARMAS if a["tier"]==min(armas_tier,3) and (a["tipo"]=="todos" or a["tipo"]==j.classe)]
        if arms:
            rar_chefe=random.choice(["Raro","Epico","Lendario","Mitico"])
            drop_arma=aplicar_raridade_equip(random.choice(arms),rar_chefe)
            if drop_arma["atk"]>j.arma["atk"]:
                j.arma=drop_arma
                r_c=RARIDADES[rar_chefe]
                print(r_c["cor"]+C.BOLD+"\n  Drop do chefe: "+r_c["emoji"]+" "+drop_arma["nome"]+" ["+rar_chefe+"] equipada! "+C.RESET)
                pausar()

    return "vitoria"

def tela_mundo(j, areas_desbloqueadas):
    while True:
        limpar(); titulo("MAPA MUNDO","🗺️",C.AZUL)
        print(C.LARANJA+"  Gold: "+str(j.gold)+"  "+C.RESET+
              C.AMARELO+"Nivel: "+str(j.nivel)+"  "+C.RESET+
              C.VERDE+"Vitorias: "+str(j.vitorias)+" "+C.RESET+"\n")
        for i,aid in enumerate(areas_desbloqueadas,1):
            a=MAPA[aid]
            print("  "+C.AMARELO+str(i)+C.RESET+"  "+a["emoji"]+"  "+a["nome"])
            print(C.CINZA+"      "+a["desc"]+" "+C.RESET)
        print("\n  "+C.AMARELO+str(len(areas_desbloqueadas)+1)+C.RESET+"  Ver status")
        print("  "+C.CINZA+"0  Sair do jogo"+C.RESET+"\n")
        esc=input(C.AMARELO+"  Destino: "+C.RESET).strip()
        if esc=="0": return "sair"
        if esc==str(len(areas_desbloqueadas)+1): ver_status(j); continue
        try:
            idx=int(esc)-1; aid=areas_desbloqueadas[idx]
        except: continue

        res=menu_area(j,aid)
        if res=="derrota": return "derrota"

        # Desbloqueia próxima área
        prox=MAPA[aid]["prox"]
        for p in prox:
            if p not in areas_desbloqueadas:
                areas_desbloqueadas.append(p)
                a=MAPA[p]
                print(C.VERDE+C.BOLD+"\n  Nova area desbloqueada: "+a["emoji"]+" "+a["nome"]+"! "+C.RESET)
                pausar()

        # Recuperação entre áreas
        j.hp=min(j.hp_max,j.hp+int(j.hp_max*0.5))
        j.mp=min(j.mp_max,j.mp+int(j.mp_max*0.6))

        if not MAPA[aid]["prox"]:  # última área
            # Boss secreto pós-endgame
            res = encontro_bobafat(j)
            return res


# ─────────────────────────────────────────
#  BOSS SECRETO — BOBAFAT
# ─────────────────────────────────────────
BOBAFAT = {
    "nome": "bobafat",
    "emoji": "👁️",
    "area": "secreto",
    "xp": 9999,
    "gold": 9999,
    "fases": [
        {
            "hp": 999,
            "atk": 120,
            "def": 50,
            "fala": "...voce realmente achou que tinha acabado?",
            "especial": "Olhar do Vazio",
            "mult_esp": 3.5,
        },
        {
            "hp": 999,
            "atk": 160,
            "def": 70,
            "fala": "INTERESSANTE. mas nao e suficiente.",
            "especial": "Colapso da Realidade",
            "mult_esp": 5.0,
        },
        {
            "hp": 999,
            "atk": 200,
            "def": 90,
            "fala": "EU. NAO. MORRO.",
            "especial": "EXTINÇÃO TOTAL",
            "mult_esp": 8.0,
        },
    ],
}


def encontro_bobafat(j):
    limpar()
    time.sleep(0.5)
    linha("=", 52, C.CINZA)
    print(C.CINZA + "\n  ..." + C.RESET)
    time.sleep(1.2)
    digitar(C.CINZA + "  O Senhor das Trevas caiu.", 0.04)
    time.sleep(0.8)
    digitar(C.CINZA + "  Voce comecou a voltar para casa...", 0.04)
    time.sleep(0.8)
    digitar(C.CINZA + "  Mas algo nao estava certo.", 0.04)
    time.sleep(1.0)
    print()
    digitar(C.CINZA + "  O chao rachou.", 0.05)
    time.sleep(0.6)
    digitar(C.CINZA + "  Uma presenca antiga emergiu das sombras.", 0.05)
    time.sleep(0.8)
    print()
    linha("=", 52, C.CINZA)
    time.sleep(0.5)
    print(C.BOLD + C.ROXO + "\n  b o b a f a t  \n" + C.RESET)
    time.sleep(0.5)
    digitar(C.CINZA + "  ...voce realmente achou que tinha acabado?", 0.05)
    time.sleep(0.5)
    print()
    print(C.VERMELHO + C.BOLD + "  BOSS SECRETO DESBLOQUEADO!" + C.RESET)
    print(C.CINZA + "  3 fases. Sem fuga. Boa sorte." + C.RESET)
    linha("=", 52, C.CINZA)

    esc = input(C.AMARELO + "  Enfrentar bobafat? (s/n): " + C.RESET).strip().lower()
    if esc != "s":
        print(C.CINZA + "  ...ele deixou voce ir. Por enquanto." + C.RESET)
        pausar()
        return "vitoria"

    j.hp = j.hp_max
    j.mp = j.mp_max
    print(C.VERDE + "\n  Uma energia estranha restaurou suas forcas..." + C.RESET)
    pausar()

    res = batalha(j, BOBAFAT, eh_chefe=True)

    if res == "derrota":
        limpar()
        linha("=", 52, C.CINZA)
        digitar(C.CINZA + "  bobafat olhou para voce caido no chao.", 0.04)
        time.sleep(0.6)
        digitar(C.CINZA + "  Ele simplesmente... foi embora.", 0.04)
        time.sleep(0.6)
        digitar(C.CINZA + "  Alguns inimigos sao grandes demais para vencer.", 0.04)
        linha("=", 52, C.CINZA)
        pausar()
        return "vitoria"

    limpar()
    linha("=", 52, C.ROXO)
    print(C.BOLD + C.ROXO + "\n  BOBAFAT FOI DERROTADO!\n  VOCE E O MAIOR HEROI DE TODOS!\n" + C.RESET)
    time.sleep(0.5)
    digitar(C.CINZA + "  bobafat se dissolveu no nada.", 0.04)
    time.sleep(0.5)
    digitar(C.CINZA + "  Nao restou nem uma sombra.", 0.04)
    time.sleep(0.5)
    digitar(C.BRANCO + "  Ninguem vai acreditar em voce.", 0.04)
    time.sleep(0.5)
    digitar(C.CINZA + "  Mas voce sabe o que aconteceu.", 0.04)
    linha("=", 52, C.ROXO)
    j.chefes += 1
    j.derrotou_bobafat = True
    novas=checar_conquistas(j); notificar_conquistas(novas)
    pausar()
    encontro_o_conceito(j)
    return "vitoria"

# ─────────────────────────────────────────
#  INTRO E SELEÇÃO
# ─────────────────────────────────────────
LOGO=r"""
  ██████╗ ██████╗  ██████╗     ██╗██╗
  ██╔══██╗██╔══██╗██╔════╝    ██╔╝██║
  ██████╔╝██████╔╝██║  ███╗  ██╔╝ ██║
  ██╔══██╗██╔═══╝ ██║   ██║ ██╔╝  ╚═╝
  ██║  ██║██║     ╚██████╔╝██╔╝   ██╗
  ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝    ╚═╝
"""

def tela_final(j, vitoria):
    limpar()
    if vitoria:
        print(C.AMARELO+C.BOLD+"""
  ╔══════════════════════════════════════╗
  ║    VOCE SALVOU O MUNDO!              ║
  ║    O Senhor das Trevas foi vencido!  ║
  ╚══════════════════════════════════════╝
"""+C.RESET)
        digitar(C.CINZA+"  A escuridao se dissipou..."+C.RESET)
        digitar(C.CINZA+"  A paz voltou as terras..."+C.RESET)
        digitar(C.BRANCO+"  E o nome de "+j.nome+" entrou para a lenda."+C.RESET)
    print()
    linha("=",52,C.AMARELO)
    print("  Heroi    "+C.BOLD+j.cor+j.nome+" "+C.RESET+"("+j.classe+")")
    print("  Nivel    "+C.AMARELO+str(j.nivel)+" "+C.RESET)
    print("  Vitorias "+C.VERDE+str(j.vitorias)+" "+C.RESET+"("+str(j.chefes)+" chefes)")
    print("  XP Total "+C.AMARELO+str(j.xp)+" "+C.RESET)
    print("  Gold     "+C.LARANJA+str(j.gold)+" "+C.RESET)
    linha("=",52,C.AMARELO)
    pausar("  ENTER para sair...")

def mini_rpg_2():
    limpar()
    print(C.BOLD+C.AMARELO+LOGO+C.RESET)
    print(C.CINZA+"  Uma aventura epica em 10 regioes te aguarda..."+C.RESET+"\n")
    import os as _os2
    if _os2.path.exists("rpg2_save.json"):
        print(C.VERDE+"  Save encontrado! "+C.RESET)
        print("  "+C.AMARELO+"1"+C.RESET+"  Continuar jogo salvo")
        print("  "+C.AMARELO+"2"+C.RESET+"  Novo jogo")
        print("  "+C.CINZA+"3  Deletar save"+C.RESET+"\n")
        esc_start=input(C.AMARELO+"  Escolha: "+C.RESET).strip()
        if esc_start=="1":
            j_load, areas_load = carregar_jogo()
            if j_load:
                print(C.VERDE+"\n  Bem vindo de volta, "+j_load.nome+"! "+C.RESET); pausar()
                res=tela_mundo(j_load, areas_load)
                tela_final(j_load, res=="vitoria"); return
            else:
                print(C.VERMELHO+"  Erro ao carregar. Iniciando novo jogo."+C.RESET); pausar()
        elif esc_start=="3":
            deletar_save()
            print(C.CINZA+"  Save deletado."+C.RESET); pausar()
    else:
        pausar("  → ENTER para comecar...")

    limpar()
    print(C.CIANO+C.BOLD+"\n  Como se chama o heroi?\n"+C.RESET)
    nome=input(C.AMARELO+"  Nome: "+C.RESET).strip() or "Heroi"

    limpar(); titulo("ESCOLHA SUA CLASSE","",C.AMARELO)
    print()
    for k,cls in CLASSES.items():
        print("  "+C.BOLD+C.AMARELO+k+C.RESET+"  "+C.BOLD+cls["cor"]+cls["emoji"]+" "+cls["nome"]+"  "+C.RESET)
        print(C.CINZA+"     "+cls["desc"]+C.RESET)
        print("     HP "+C.VERDE+str(cls["hp"])+" "+C.RESET+
              " MP "+C.AZUL+str(cls["mp"])+" "+C.RESET+
              " ATK "+C.VERMELHO+str(cls["atk"])+" "+C.RESET+
              " DEF "+C.CIANO+str(cls["defesa"])+" "+C.RESET+
              " VEL "+C.AMARELO+str(cls["vel"])+" "+C.RESET+"\n")
    cls_id=""
    while cls_id not in CLASSES:
        cls_id=input(C.AMARELO+"  Sua classe: "+C.RESET).strip()

    j=Jogador(nome,cls_id)

    res=tela_mundo(j,["floresta"])
    tela_final(j, res=="vitoria")

if __name__=="__main__":
    mini_rpg_2()
