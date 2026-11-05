import csv, io, json, tempfile, unittest, zipfile
from pathlib import Path
from extrair_escolas import choose_name, clean_name, extract

class ExtractorTests(unittest.TestCase):
    def test_brand_precedes_legal_and_owner_is_not_fallback(self):
        self.assertEqual(choose_name('Escolinha Arco Iris', 'Jose da Silva Ltda', '2062'), ('Escolinha Arco Iris', 'nome_fantasia'))
        self.assertEqual(choose_name('', 'Jose da Silva 12345678901', '2135'), ('', ''))
        self.assertEqual(choose_name('JOSE DA SILVA', 'Jose da Silva 123.456.789-01', '2135'), ('', ''))
        self.assertEqual(choose_name('Arco Iris', 'Jose da Silva', '2135'), ('Arco Iris', 'nome_fantasia'))
        self.assertEqual(choose_name('', 'Colegio Exemplo Ltda', '2062'), ('Colegio Exemplo Ltda', 'razao_social'))
        self.assertEqual(choose_name('Escola desconhecida', '', ''), ('', ''))
        self.assertEqual(choose_name('*****', 'Jose da Silva', '2135'), ('', ''))
        self.assertEqual(choose_name('...', 'Colegio Exemplo Ltda', '2062'), ('Colegio Exemplo Ltda', 'razao_social'))
        self.assertEqual(clean_name('ESCOLA 12.345.678/0001-99'), 'ESCOLA')

    def test_zip_pipeline_active_status_names_and_exclusions(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            def archive(name, rows):
                stream=io.StringIO(newline='')
                csv.writer(stream,delimiter=';').writerows(rows)
                with zipfile.ZipFile(root/name,'w') as z: z.writestr('dados.csv',stream.getvalue().encode('latin-1'))
            records=[]
            for n,status,fantasy,uf in [(1,'02','Escola Arco Iris','SP'),(2,'08','Escola Baixada','SP'),(3,'04','Inapta','SP'),(4,'02','','SP'),(5,'02','','SP'),(6,'02','Exterior','EX'),(7,'02','Jose da Silva','SP'),(8,'02','Retirada','SP'),(9,'02','Sem empresa','SP'),(10,'02','Curso Ativo','SP')]:
                row=['']*30
                row[0]=f'{n:08}'; row[1]='0001';row[2]='00';row[4]=fantasy;row[5]=status;row[6]='20250101'
                row[11]='8513900';row[14]='Rua Teste';row[15]='10';row[18]='14400000';row[19]=uf;row[20]='6219';row[21]='16';row[22]='999999999';row[27]='contato@example.org'
                records.append(row)
            archive('Municipios0.zip',[['6219','FRANCA']])
            archive('Estabelecimentos0.zip',records)
            archive('Empresas0.zip',[[f'{n:08}', 'Jose da Silva 12345678901' if n in [4,7] else 'Colegio Exemplo Ltda','2135' if n in [4,7] else '2062'] for n in range(1,11) if n != 9])
            (root/'excluir.txt').write_text('00000008000100',encoding='utf-8')
            report=extract(root,root/'escolas.csv',root/'manifesto.json',root/'excluir.txt')
            with (root/'escolas.csv').open(encoding='utf-8-sig',newline='') as f: results=list(csv.DictReader(f))
            self.assertEqual([r['cnpj'] for r in results], ['00000001000100','00000005000100','00000010000100'])
            self.assertEqual({r['situacao_cadastral'] for r in results},{'02'})
            self.assertEqual(results[0]['nome_exibicao'],'Escola Arco Iris')
            self.assertEqual(results[1]['nome_exibicao'],'Colegio Exemplo Ltda')
            self.assertEqual(report['contagens']['educacao_nao_ativa_excluida'],2)
            self.assertEqual(report['contagens']['empresa_nao_localizada'],1)
            self.assertEqual(report['contagens']['empresario_individual_sem_fantasia_excluido'],2)
            self.assertEqual(json.loads((root/'manifesto.json').read_text(encoding='utf-8'))['versao'],'2.0.0')
            with self.assertRaises(ValueError): extract(root,root/'escolas.csv')

if __name__=='__main__': unittest.main()
