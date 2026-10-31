import csv, glob, io, os, zipfile

PASTA = "dados_cnpj"     # pasta com os .zip baixados
SAIDA = "escolas.csv"

# CNAEs de ensino (7 dígitos, sem pontuação). Apague os que não quiser.
CNAES = {
    "8511200": "Educação infantil - creche",
    "8512100": "Educação infantil - pré-escola",
    "8513900": "Ensino fundamental",
    "8520100": "Ensino médio",
    "8531700": "Educação superior - graduação",
    "8532500": "Educação superior - graduação e pós",
    "8533300": "Educação superior - pós e extensão",
    "8541400": "Educação profissional técnica de nível médio",
    "8542200": "Educação profissional tecnológica",
    "8591100": "Ensino de esportes",
    "8592901": "Ensino de dança",
    "8592902": "Ensino de artes cênicas",
    "8592903": "Ensino de música",
    "8592999": "Ensino de arte e cultura (outros)",
    "8593700": "Ensino de idiomas",
    "8599603": "Treinamento em informática",
    "8599605": "Cursos preparatórios para concursos",
    "8599699": "Outras atividades de ensino",
}

SO_ATIVAS = True              # situação cadastral 02 = ativa
USAR_CNAE_SECUNDARIO = False  # True = inclui quem tem ensino só como atividade secundária
UFS = None                    # ex.: {"SP", "MG"} para limitar estados; None = Brasil todo


def ler_zip(caminho):
    """Lê o CSV de dentro do .zip linha a linha, sem descompactar no disco."""
    with zipfile.ZipFile(caminho) as z:
        for nome in z.namelist():
            with z.open(nome) as f:
                texto = io.TextIOWrapper(f, encoding="latin-1", newline="")
                yield from csv.reader(texto, delimiter=";", quotechar='"')


def arquivos(prefixo):
    """Acha os .zip pelo começo do nome, sem diferenciar maiúsculas/minúsculas."""
    todos = glob.glob(os.path.join(PASTA, "*.zip"))
    achados = sorted(a for a in todos
                     if os.path.basename(a).lower().startswith(prefixo.lower()))
    if not achados:
        raise SystemExit(f"Nenhum arquivo '{prefixo}*.zip' encontrado em '{PASTA}'.")
    return achados


# 1) Tabela de municípios
municipios = {}
for arq in arquivos("Municipios"):
    for linha in ler_zip(arq):
        municipios[linha[0]] = linha[1].title()

# 2) Filtra os estabelecimentos
escolas, basicos = [], set()
for arq in arquivos("Estabelecimentos"):
    print("Lendo", arq)
    for c in ler_zip(arq):
        if len(c) < 28:
            continue
        if SO_ATIVAS and c[5] != "02":
            continue
        if UFS and c[19] not in UFS:
            continue
        cnae = c[11]
        if cnae not in CNAES:
            if not USAR_CNAE_SECUNDARIO:
                continue
            sec = [s for s in c[12].split(",") if s in CNAES]
            if not sec:
                continue
            cnae = sec[0]

        telefone = f"({c[21]}) {c[22]}" if c[22] else ""
        telefone2 = f"({c[23]}) {c[24]}" if c[24] else ""
        endereco = " ".join(p for p in [c[13], c[14]] if p).strip()
        if c[15]:
            endereco += f", {c[15]}"
        if c[16]:
            endereco += f" - {c[16]}"

        escolas.append({
            "cnpj": c[0] + c[1] + c[2],   # texto: CNPJs novos podem ter letras
            "cnpj_basico": c[0],
            "nome_fantasia": c[4].strip(),
            "cnae": cnae,
            "tipo_ensino": CNAES[cnae],
            "endereco": endereco.strip(),
            "bairro": c[17].strip(),
            "cep": c[18],
            "municipio": municipios.get(c[20], c[20]),
            "uf": c[19],
            "telefone": telefone,
            "telefone2": telefone2,
            "email": c[27].strip().lower(),
        })
        basicos.add(c[0])

print(f"{len(escolas)} estabelecimentos encontrados")

# 3) Busca a razão social só das empresas filtradas
razao = {}
for arq in arquivos("Empresas"):
    print("Lendo", arq)
    for c in ler_zip(arq):
        if c and c[0] in basicos:
            # Natureza 2135 = Empresário Individual: a razão social é o nome da pessoa
            razao[c[0]] = "" if c[2] == "2135" else c[1].strip()

# 4) Grava o resultado
campos = ["cnpj", "razao_social", "nome_fantasia", "cnae", "tipo_ensino",
          "endereco", "bairro", "cep", "municipio", "uf",
          "telefone", "telefone2", "email"]
with open(SAIDA, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
    w.writeheader()
    for e in escolas:
        e["razao_social"] = razao.get(e["cnpj_basico"], "")
        w.writerow(e)

print("Pronto:", SAIDA)