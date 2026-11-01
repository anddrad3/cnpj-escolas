# CNPJ Escolas

Script em Python que extrai da base pública de CNPJ da Receita Federal todas as escolas, faculdades e cursos ativos do Brasil (ou dos estados escolhidos) e gera um CSV com contato e endereço.


## O que ele faz

- Lê os arquivos `.zip` da Receita direto, sem precisar descompactar
- Filtra estabelecimentos pelos CNAEs de ensino (creche, fundamental, médio, superior, técnico, idiomas, música, etc.)
- Junta a razão social e o nome do município
- Gera um `escolas.csv` pronto para abrir no Excel ou importar em um banco de dados

## Requisitos

- Python 3.8 ou mais novo
- Nenhuma biblioteca extra (só a biblioteca padrão)

## Como usar

1. Baixe a pasta do mês mais recente em [Dados Abertos do CNPJ](LINK_DA_RECEITA).
2. Coloque estes arquivos numa pasta chamada `dados_cnpj`, ao lado do script:
   - `Estabelecimentos0.zip` a `Estabelecimentos9.zip`
   - `Empresas0.zip` a `Empresas9.zip`
   - `Municipios.zip`
3. Rode:

   ```
   python extrair_escolas.py
   ```

4. O resultado sai em `escolas.csv`.

O processamento pode levar de 10 a 30 minutos, dependendo do computador.

## Configuração

No topo do `extrair_escolas.py`:

| Opção | O que faz |
|---|---|
| `CNAES` | Tipos de ensino incluídos. Apague os que não quiser. |
| `SO_ATIVAS` | `True` mantém só empresas com situação cadastral ativa. |
| `USAR_CNAE_SECUNDARIO` | `True` inclui empresas que têm ensino só como atividade secundária. |
| `UFS` | Ex.: `{"SP", "MG"}` para limitar estados. `None` = Brasil todo. |

## Colunas do resultado

`cnpj`, `razao_social`, `nome_fantasia`, `cnae`, `tipo_ensino`, `endereco`, `bairro`, `cep`, `municipio`, `uf`, `telefone`, `telefone2`, `email`

## Observações

- O CNPJ é gravado como texto, já preparado para o CNPJ alfanumérico.
- Para empresário individual, a razão social é o nome da pessoa física, então o campo fica em branco.
- Os dados são públicos e atualizados mensalmente pela Receita Federal. Os arquivos baixados e o CSV gerado não fazem parte deste repositório.

## Download dos dados prontos

[Baixar a versão mais recente](https://github.com/SEU_USUARIO/cnpj-escolas/releases/latest)
