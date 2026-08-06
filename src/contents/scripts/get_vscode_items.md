# Como os itens recentes do VS Code são obtidos

## Visão geral

O VS Code guarda o seu histórico de itens recentes numa base de dados SQLite
chamada `state.vscdb`. O maior desafio não é ler essa base de dados — é
**encontrá-la**, porque a sua localização varia conforme:

- a variante instalada (Code, Insiders, OSS, VSCodium)
- o tipo de instalação (pacote do sistema, Flatpak, portátil)
- se existe uma pasta de armazenamento partilhado personalizada

Por isso, a descoberta combina **três rotas complementares**, com prioridade
decrescente, implementadas em `vscode_db_locator.py`.

## As três rotas de descoberta

### 1. Override explícito (variável de ambiente)

Se a variável de ambiente `VSCODE_RECENTS_DB` estiver definida, o caminho
indicado é usado diretamente e tem prioridade máxima:

```python
explicit_db = os.environ.get("VSCODE_RECENTS_DB")
if explicit_db:
    candidates.append(("explicit env", Path(explicit_db).expanduser()))
```

Isto serve principalmente para depuração ou para forçar a leitura de uma
instalação específica.

### 2. Descoberta estática por variante (`VSCODE_REGISTRY`)

Para cada variante conhecida (Code, Insiders, OSS, VSCodium), o código gera
candidatos com base num registo central (`vscode_registry.py`), sem precisar
de percorrer o disco todo. Esta rota tem duas sub-partes:

#### 2a — Via `product.json`

`product.json` é um ficheiro de **metadados** que vem com a instalação do
VS Code — não é a base de dados em si. O que importa aqui é um campo
opcional chamado `sharedDataFolderName`, que indica o nome exato da pasta
(dentro da home do utilizador) onde essa instalação guarda o seu
armazenamento partilhado — e é lá que está o `state.vscdb` real.

Fluxo:

```

encontrar product.json (perto do executável, ou em caminhos conhecidos)
↓
ler o JSON
↓
extrair "sharedDataFolderName"
↓
construir: ~/<sharedDataFolderName>/sharedStorage/state.vscdb
```

Isto dá o caminho **exato** para essa instalação, mas só funciona se o
`product.json` existir e tiver essa chave.

#### 2b — Caminhos fixos de fallback (correm sempre)

Independentemente de 2a ter tido sucesso, o código adiciona sempre um
conjunto de caminhos "adivinhados", cobrindo os layouts mais comuns:

| Candidato                 | Caminho                                                                               |
| ------------------------- | ------------------------------------------------------------------------------------- |
| Shared (nome por omissão) | `~/<default_shared_dir>/sharedStorage/state.vscdb`                                    |
| Legacy config (XDG)       | `$XDG_CONFIG_HOME/<legacy_dir>/User/globalStorage/state.vscdb`                        |
| Legacy data (XDG)         | `$XDG_DATA_HOME/<legacy_dir>/User/globalStorage/state.vscdb`                          |
| Instalação portátil       | `$XDG_DATA_HOME/<legacy_dir>/user-data/User/globalStorage/state.vscdb`                |
| Flatpak                   | `~/.var/app/com.visualstudio.code/config/<legacy_dir>/User/globalStorage/state.vscdb` |

Estes caminhos servem de rede de segurança para quando `product.json` não
existe, não é legível, ou não tem `sharedDataFolderName`.

### 3. Scan genérico do sistema de ficheiros

Como último recurso, `discovered_state_dbs()` percorre diretórios comuns
(`XDG_CONFIG_HOME`, `XDG_DATA_HOME`, pastas partilhadas conhecidas, etc.) à
procura de **qualquer** ficheiro chamado `state.vscdb` cujo caminho sugira
pertencer a uma variante do VS Code (contém "Code", "vscode" ou "codium").

Esta rota tem a prioridade mais baixa e existe para apanhar instalações ou
layouts não modelados explicitamente nas rotas 1 e 2.

## Ordem final e deduplicação

`db_candidates()` junta os candidatos das três rotas por esta ordem —
explícito → por variante (2a antes de 2b) → scan genérico — e remove
duplicados por caminho, mantendo sempre a primeira ocorrência (ou seja, a
de maior prioridade).

1. explicit env

2.

- a. <variante> shared (via product.json, se existir)
- b. <variante> shared (nome por omissão)

```
  <variante> legacy config
  <variante> legacy data
  <variante> portable
  <variante> flatpak config
```

3. discovered (scan genérico)

## Depois de encontrada a base de dados

Uma vez identificados os caminhos candidatos, `extract_items.py` trata da
leitura em si:

1. Copia o `.vscdb` para um diretório temporário (nunca abre o ficheiro
   original em curso — o VS Code pode tê-lo bloqueado)
2. Lê apenas a chave `history.recentlyOpenedPathsList` da tabela `ItemTable`.
   O valor guardado não é texto simples: pode vir como **bytes** (é
   preciso descodificar UTF-8/UTF-16 primeiro) e o conteúdo em si é uma
   **string JSON** com um array `entries`
3. Descodifica esses bytes, faz parsing do JSON e converte cada entrada
   (`fileUri` / `folderUri` / `workspace.configPath`) num item normalizado
   (`name`, `path`, `kind`, `source`, `exists`)
4. Agrega os itens de todas as bases de dados encontradas, remove
   duplicados por caminho e filtra os que já não existem no disco
   (a menos que `include_missing` seja pedido)

## Resumo detalhado

| Conceito            | O que é                                                                                                                                    | Onde vive                                                 |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| `state.vscdb`       | A base de dados SQLite real; guarda o histórico como chave-valor, com o valor em JSON (por vezes bytes) que é preciso extrair/descodificar | Localização variável — é o que se está a tentar encontrar |
| `product.json`      | Metadados da instalação; pode indicar o nome da pasta partilhada                                                                           | Perto do executável ou em caminhos conhecidos do registo  |
| `VSCODE_RECENTS_DB` | Override manual do caminho da base de dados                                                                                                | Variável de ambiente                                      |
| `VSCODE_REGISTRY`   | Registo estático com os caminhos/labels conhecidos por variante                                                                            | `vscode_registry.py`                                      |
