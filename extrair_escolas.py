"""Extrator de estabelecimentos ativos de educação do CNPJ. Python 3.11+, sem dependências."""
import argparse, csv, hashlib, io, json, re, sqlite3, tempfile, unicodedata, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

VERSION = "2.0.0"
UFS = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
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

FIELDS = ["cnpj", "razao_social", "nome_fantasia", "nome_exibicao", "origem_nome",
          "situacao_cadastral", "data_situacao_cadastral", "natureza_juridica", "versao_extrator",
          "cnae", "tipo_ensino", "endereco", "bairro", "cep", "municipio", "uf", "telefone", "telefone2", "email"]

def clean_name(value):
    value = re.sub(r'(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)', '', value)
    value = re.sub(r'(?<!\d)\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}(?!\d)', '', value)
    value = re.sub(r'^\s*\d{2}\.\d{3}\.\d{3}\s+', '', value)
    value = ' '.join(value.split()).strip(' -')[:250]
    if not any(c.isalnum() for c in value):
        return ''
    if value.upper() in {'NAO INFORMADO', 'NÃO INFORMADO', 'SEM NOME', 'SEM NOME FANTASIA', 'NAO TEM', 'NÃO TEM', 'S/N', 'SN', 'MEI', 'NULL', 'NONE'}:
        return ''
    return value

def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if c.isalnum())

def choose_name(fantasy, legal, nature):
    fantasy, legal = clean_name(fantasy), clean_name(legal)
    if not nature:
        return '', ''  # Sem Empresas não podemos verificar empresário individual.
    if nature == '2135':
        if not fantasy or normalized(fantasy) == normalized(legal):
            return '', ''
        return fantasy, 'nome_fantasia'
    return (fantasy, 'nome_fantasia') if fantasy else (legal, 'razao_social') if legal else ('', '')

def archives(folder, prefix):
    found = sorted(p for p in folder.glob('*.zip') if p.name.lower().startswith(prefix.lower()))
    if not found:
        raise ValueError(f'Nenhum {prefix}*.zip encontrado em {folder}')
    return found

def rows(path):
    with zipfile.ZipFile(path) as bundle:
        for item in bundle.infolist():
            if not item.is_dir():
                with bundle.open(item) as binary:
                    yield from csv.reader(io.TextIOWrapper(binary, encoding='latin-1', newline=''), delimiter=';')

def extract(folder, output, report_path=None, exclusions=None):
    if output.exists() or (report_path and report_path.exists()):
        raise ValueError('Use novos arquivos de saída. Os existentes não serão sobrescritos.')
    groups = {prefix: archives(folder, prefix) for prefix in ['Municipios', 'Estabelecimentos', 'Empresas']}
    excluded = set()
    if exclusions:
        excluded = {re.sub(r'[^A-Z0-9]', '', line.upper()) for line in exclusions.read_text(encoding='utf-8-sig').splitlines() if line.strip()}
        if any(len(cnpj) != 14 for cnpj in excluded):
            raise ValueError('Exclusões: informe um CNPJ de 14 posições por linha.')
    cities = {r[0]: r[1].title() for a in groups['Municipios'] for r in rows(a) if len(r) >= 2}
    output.parent.mkdir(parents=True, exist_ok=True)
    totals = Counter()
    wanted = set()
    with tempfile.TemporaryDirectory(prefix='cnpj-escolas-', dir=output.parent) as temporary:
        db = sqlite3.connect(str(Path(temporary)/'staging.sqlite'))
        db.execute('CREATE TABLE candidates(cnpj TEXT PRIMARY KEY, basic TEXT, record TEXT)')
        db.execute('CREATE TABLE companies(basic TEXT PRIMARY KEY, legal TEXT, nature TEXT)')
        for archive in groups['Estabelecimentos']:
            print('Estabelecimentos:', archive.name, flush=True)
            for c in rows(archive):
                totals['estabelecimentos_lidos'] += 1
                if len(c) < 28:
                    totals['linhas_invalidas'] += 1
                    continue
                if c[11] not in CNAES:
                    continue
                totals['educacao_cnae_principal'] += 1
                if c[5] != '02':
                    totals['educacao_nao_ativa_excluida'] += 1
                    continue
                if c[19] not in UFS:
                    totals['exterior_excluido'] += 1
                    continue
                cnpj = c[0]+c[1]+c[2]
                if cnpj in excluded:
                    totals['exclusoes_solicitadas'] += 1
                    continue
                address = ' '.join(p for p in [c[13], c[14]] if p).strip()
                address += ', '+c[15] if c[15] else ''
                address += ' - '+c[16] if c[16] else ''
                record = dict(cnpj=cnpj, nome_fantasia=c[4], cnae=c[11], tipo_ensino=CNAES[c[11]],
                  situacao_cadastral=c[5], data_situacao_cadastral=c[6], versao_extrator=VERSION,
                  endereco=address, bairro=c[17].strip(), cep=c[18], municipio=cities.get(c[20], c[20]), uf=c[19],
                  telefone=f'({c[21]}) {c[22]}' if c[22] else '', telefone2=f'({c[23]}) {c[24]}' if c[24] else '',
                  email=c[27].strip().lower())
                cursor = db.execute('INSERT OR IGNORE INTO candidates VALUES(?,?,?)', (cnpj,c[0],json.dumps(record,ensure_ascii=False)))
                if cursor.rowcount:
                    wanted.add(c[0]); totals['ativos_brasileiros_candidatos'] += 1
                else: totals['duplicados_excluidos'] += 1
            db.commit()
        for archive in groups['Empresas']:
            print('Empresas:', archive.name, flush=True)
            for c in rows(archive):
                if len(c) >= 3 and c[0] in wanted:
                    db.execute('INSERT OR IGNORE INTO companies VALUES(?,?,?)',(c[0],c[1],c[2]))
            db.commit()
        stage = Path(temporary)/'escolas.csv'
        with stage.open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=FIELDS)
            writer.writeheader()
            for raw, legal, nature in db.execute('SELECT a.record,b.legal,b.nature FROM candidates a LEFT JOIN companies b ON a.basic=b.basic ORDER BY a.cnpj'):
                row=json.loads(raw)
                name, origin=choose_name(row['nome_fantasia'],legal or '',nature or '')
                if not name:
                    totals['sem_nome_publicavel_excluidos'] += 1
                    if nature == '2135': totals['empresario_individual_sem_fantasia_excluido'] += 1
                    if not nature: totals['empresa_nao_localizada'] += 1
                    continue
                row.update(nome_fantasia=clean_name(row['nome_fantasia']),razao_social='' if nature=='2135' else clean_name(legal),
                           nome_exibicao=name,origem_nome=origin,natureza_juridica=nature)
                writer.writerow(row)
                totals['publicados'] += 1
                totals['nome_por_'+origin] += 1
            stream.flush()
        db.close()
        stage.replace(output)
    with output.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
    report = dict(versao=VERSION,gerado_em=datetime.now(timezone.utc).isoformat(),contagens=dict(totals),
      csv=output.name,sha256=digest,situacao='02 - ativa na base de origem; não é consulta cadastral em tempo real',
      cnaes=CNAES,fonte='Receita Federal - Dados Abertos CNPJ',
      arquivos=[dict(nome=p.name,bytes=p.stat().st_size) for group in groups.values() for p in group],
      politica_nome='Nome fantasia primeiro. Sem fantasia: razão social apenas se não for empresário individual (2135). Sem nome publicável, registro excluído.',
      limites='Inclui cursos e outras atividades de ensino. Não equivale ao Censo Escolar. Nome fantasia pode identificar pessoa física. Contatos cadastrais podem ser de representantes. Dados públicos não são isentos da LGPD.')
    if report_path: report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['contagens'],ensure_ascii=False),flush=True)
    return report

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados',type=Path,default=Path('dados_cnpj'))
    parser.add_argument('--saida',type=Path,default=Path('escolas.csv'))
    parser.add_argument('--relatorio',type=Path)
    parser.add_argument('--excluir',type=Path,help='Arquivo privado com um CNPJ por linha para retirada da publicação')
    args=parser.parse_args()
    extract(args.dados,args.saida,args.relatorio,args.excluir)
