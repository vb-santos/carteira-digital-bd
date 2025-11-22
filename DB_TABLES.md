# Documentação: Criar Tabelas no DataGrip (Console MySQL)
#### 1. Abrindo o console do MySQL no DataGrip

- Abra o DataGrip.
- Clique no + no canto superior esquerdo do Datagrip.
- Selecione Data Source -> MySQL.
- Baixe os drivers.
- Coloque as credenciais definidas no .env e teste a conexão.
- Abra a aba de Console para digitar comandos SQL.

#### 2. Criando as tabelas
##### 2.1 Tabela carteira
``` sql
CREATE TABLE carteira
(
    endereco_carteira  VARCHAR(32) NOT NULL PRIMARY KEY,
    hash_chave_privada VARCHAR(64) NOT NULL,
    data_criacao       DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    status             ENUM ('ATIVA', 'BLOQUEADA') NOT NULL,
    CONSTRAINT carteira_hash_chave_privada_uindex UNIQUE (hash_chave_privada)
);
```

##### 2.2 Tabela moeda
``` sql
CREATE TABLE moeda
(
    id_moeda SMALLINT NOT NULL PRIMARY KEY,
    codigo   VARCHAR(4) NOT NULL,
    nome     VARCHAR(50) NOT NULL,
    tipo     ENUM ('FIDUCIÁRIA', 'CRIPTO') NOT NULL,
    CONSTRAINT MOEDA_pk_2 UNIQUE (codigo),
    CONSTRAINT MOEDA_pk_3 UNIQUE (nome)
);
```

##### 2.3 Tabela saldo_carteira

``` sql
CREATE TABLE saldo_carteira
(
    endereco_carteira VARCHAR(32) NOT NULL,
    id_moeda          SMALLINT NOT NULL,
    saldo             DECIMAL NULL,
    data_atualizacao  DATETIME DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (endereco_carteira, id_moeda),
    CONSTRAINT saldo_carteira_endereco_fk FOREIGN KEY (endereco_carteira)
        REFERENCES carteira (endereco_carteira)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT saldo_carteira_id_moeda_fk FOREIGN KEY (id_moeda)
        REFERENCES moeda (id_moeda)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);
```

##### 2.4 Tabela deposito_saque

``` sql
CREATE TABLE deposito_saque
(
    id_movimento      BIGINT AUTO_INCREMENT PRIMARY KEY,
    endereco_carteira VARCHAR(32) NOT NULL,
    id_moeda          SMALLINT NOT NULL,
    tipo              ENUM ('DEPOSITO', 'SAQUE') NULL,
    valor             DECIMAL NOT NULL,
    taxa_valor        DECIMAL NULL,
    data_hora         DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT deposito_saque_endereco_carteira_fk FOREIGN KEY (endereco_carteira)
        REFERENCES carteira (endereco_carteira),
    CONSTRAINT deposito_saque_id_moeda_fk FOREIGN KEY (id_moeda)
        REFERENCES moeda (id_moeda)
);
```

#### 3. Exemplos de preenchimento das tabelas
##### 3.1 Inserir moedas
``` sql
INSERT INTO moeda (id_moeda, codigo, nome, tipo)
VALUES
(1, 'USD', 'Dólar', 'FIDUCIÁRIA'),
(2, 'BTC', 'Bitcoin', 'CRIPTO'),
(3, 'ETH', 'Ethereum', 'CRIPTO');
```

##### 3.2 Inserir carteiras
``` sql
INSERT INTO carteira (endereco_carteira, hash_chave_privada, status)
VALUES
('a2a6cf793e0e940706d19cbc5866cfb8', 'ac2d1d01d8b22bfce90145af8e2e7a9fb5807a26b49ece5c8acf34d6aee2e4e2', 'ATIVA'),
('5ef83ac052d884f0cd86a8f876165513', 'ba45ccec895ca76d693afe6c187ac2746ad09c781cab8e1f3bc7d8a0c0f1e7bb', 'BLOQUEADA');
```

##### 3.3 Inserir saldo das carteiras
``` sql
INSERT INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
VALUES
('a2a6cf793e0e940706d19cbc5866cfb8', 1, 100.0),
('a2a6cf793e0e940706d19cbc5866cfb8', 2, 0.5),
('5ef83ac052d884f0cd86a8f876165513', 1, 50.0);
```

##### 3.4 Inserir depósitos / saques
``` sql
INSERT INTO deposito_saque (endereco_carteira, id_moeda, tipo, valor, taxa_valor)
VALUES
('a2a6cf793e0e940706d19cbc5866cfb8', 1, 'DEPOSITO', 100.0, 0.0),
('a2a6cf793e0e940706d19cbc5866cfb8', 2, 'DEPOSITO', 0.5, 0.0);
```

## OBS: Apesar de poder preencher diretamente via banco, recomendo preencher via documentação da API

---

#### Para fins de padronização, acesse o arquivo data.sql e tente subir os dados no banco através dele. Esse arquivo é responsável por:

- Criar as tabelas.
- Preencher as tabelas com os dados corretos.
