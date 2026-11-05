# Histórico

## 2.0.0 — 04/11/2026

- Mantém e torna auditável o filtro obrigatório de situação 02 (ativa), com status e data no CSV.
- Prioriza nome fantasia; não recupera nome civil de empresário individual como nome de escola. Exclui registros sem nome publicável e registra as contagens.
- Restringe a busca ao Brasil, preserva CNAE principal e evita duplicidade de CNPJ.
- Acrescenta versão, origem do nome, natureza jurídica e relatório com SHA-256.
- Adiciona interface de linha de comando, lista privada de exclusões, SQLite temporário, proteção contra sobrescrita e testes com bases sintéticas.
- Documenta fonte oficial, cobertura, atualização manual, cuidados com dados pessoais e canal de correção/retirada.

## 2026-10 — primeira publicação

- Extrator inicial e arquivo escolas.zip na release de outubro.
- O código já selecionava apenas situação 02 e omitia a razão social de empresário individual; o CSV não trazia metadados para revalidar essa regra.
- Muitos registros eram exportados sem nome. Use a versão 2.0 para novas integrações.
