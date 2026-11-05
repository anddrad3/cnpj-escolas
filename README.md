# CNPJ Escolas — extrator 2.0.0

Extrai estabelecimentos **ativos na base de origem** cujo CNAE principal está na lista de ensino do script. Desenvolvido por Matheus Andrade para o Radar do [Voz do Professor](https://amerindia.alwaysdata.net/voz-do-professor/#/radar).

Inclui escolas, cursos, treinamento e outras atividades de ensino. **Não é o Censo Escolar**, não garante cobertura de todas as escolas, funcionamento atual nem oferta de vagas. Dados cadastrais podem estar desatualizados ou conter contatos de representantes.

## Fonte e execução

Baixe os arquivos originais na página de [Dados Públicos do CNPJ da Receita Federal](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj). Use os ZIPs de **Estabelecimentos**, **Empresas** e **Municípios** da mesma competência. Consulte também o [leiaute oficial](https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf/view). Não são necessários os arquivos de sócios (QSA).

Python 3.11 ou superior, somente biblioteca padrão. ZIPs são lidos sem descompactação; os candidatos ficam em SQLite temporário para limitar o uso de memória. Reserve espaço para esse arquivo temporário e para o CSV. A base completa pode levar vários minutos.

```sh
python extrair_escolas.py --dados dados_cnpj --saida escolas-v2.csv --relatorio escolas-v2.json
python -m unittest -v test_extrator.py
```

Os arquivos de saída existentes nunca são sobrescritos. Originais permanecem intactos. CSV usa UTF-8 com BOM para abertura no Excel; importe CNPJ e CEP como **texto**, preservando zeros iniciais. Os valores são dados cadastrais externos: não habilite conteúdo ativo/fórmulas ao abrir arquivos de terceiros em planilhas.

## Regras verificáveis

- Somente `situacao_cadastral = 02`. Baixadas, inaptas, suspensas, nulas e outras situações ficam fora. Isso vale para o retrato da Receita utilizado, não para uma consulta em tempo real.
- Apenas as 27 UFs brasileiras; cadastros `EX` ficam fora.
- CNAE **principal**, conforme a lista `CNAES` no código. CNAEs secundários não são considerados.
- `nome_exibicao` usa **nome fantasia primeiro**. Exemplo: razão social “José da Silva Ltda.” e fantasia “Escolinha Arco-Íris” → “Escolinha Arco-Íris”.
- Sem nome fantasia, admite-se razão social de pessoa jurídica que não seja empresário individual. Para natureza `2135`, não se usa nome civil como substituto; a razão social não é exportada. Se fantasia coincidir com esse nome civil, também não se publica.
- Sem empresa correspondente ou sem nome publicável, o registro é excluído e contado no relatório. Não inventamos o nome da escola. Um nome fantasia pode, ele próprio, identificar uma pessoa; a regra não constitui anonimização nem identifica automaticamente todos os nomes civis.
- CPF/CNPJ reconhecíveis nos nomes são removidos. Não são extraídos sócios, documentos de sócios, capital social ou dados bancários.
- O relatório registra versão, contagens, arquivos de origem, tamanho e SHA-256 do CSV. A data de geração é diferente da competência dos arquivos da Receita.

Além dos campos anteriores, o CSV 2.0 inclui `nome_exibicao`, `origem_nome`, `situacao_cadastral`, `data_situacao_cadastral`, `natureza_juridica` e `versao_extrator`. A data da situação é a data do evento cadastral, não uma certificação de vigência. O CNPJ é mantido no arquivo de trabalho para reconciliação e retiradas; o Radar não o exibe nem o devolve na API.

## Correções, retirada e LGPD

**Dados públicos também podem ser dados pessoais.** Telefone, e-mail, endereço e nome podem identificar uma pessoa física, especialmente empresário individual. A publicação da Receita não concede permissão irrestrita para novos usos. Consulte a [orientação da ANPD](https://www.gov.br/anpd/pt-br/acesso-a-informacao/perguntas-frequentes) e a [LGPD vigente](https://www2.camara.leg.br/legin/fed/lei/2018/lei-13709-14-agosto-2018-787077-normaatualizada-pl.html).

A finalidade no Voz do Professor é localizar contatos de estabelecimentos de educação. Não usar a base para prospecção abusiva ou criação de perfis de pessoas. O responsável pelo tratamento deve documentar finalidade, necessidade, base legal, transparência, retenção e atendimento aos titulares; este código não certifica conformidade jurídica. Para a pesquisa acadêmica, recomenda-se validação com o encarregado de dados da instituição.

Pedidos de correção ou retirada do Radar: **vozdoprofessoroficial@gmail.com**, identificando o estabelecimento e o endereço, sem enviar documentos pessoais desnecessários. Uma correção no Radar não altera o cadastro da Receita. O operador pode manter uma lista **privada** de CNPJs a excluir, um por linha:

```sh
python extrair_escolas.py --dados dados_cnpj --saida escolas-revisadas.csv --relatorio revisao.json --excluir exclusoes.txt
```

A lista não deve ir para o GitHub. A retirada requer nova importação no site; não é automática. Cópias anteriormente baixadas por terceiros não podem ser recolhidas por este script.

## Versões

Código e notas em [Releases](https://github.com/anddrad3/cnpj-escolas/releases). Consulte [CHANGELOG.md](CHANGELOG.md). A licença MIT se aplica ao código, não substitui as obrigações sobre os dados da Receita e a LGPD. Arquivos da Receita e saídas volumosas ficam fora do histórico Git.
