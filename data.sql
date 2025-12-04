-- 1. Criação das tabelas
CREATE TABLE
    IF NOT EXISTS carteira (
        endereco_carteira VARCHAR(32) NOT NULL PRIMARY KEY,
        hash_chave_privada VARCHAR(64) NOT NULL,
        data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        status ENUM ('ATIVA', 'BLOQUEADA') NOT NULL,
        CONSTRAINT carteira_hash_chave_privada_uindex UNIQUE (hash_chave_privada)
    );

CREATE TABLE
    IF NOT EXISTS moeda (
        id_moeda SMALLINT NOT NULL PRIMARY KEY,
        codigo VARCHAR(4) NOT NULL,
        nome VARCHAR(50) NOT NULL,
        tipo ENUM ('FIDUCIÁRIA', 'CRIPTO') NOT NULL,
        CONSTRAINT MOEDA_pk_2 UNIQUE (codigo),
        CONSTRAINT MOEDA_pk_3 UNIQUE (nome)
    );

CREATE TABLE
    IF NOT EXISTS saldo_carteira (
        endereco_carteira VARCHAR(32) NOT NULL,
        id_moeda SMALLINT NOT NULL,
        saldo DECIMAL(18, 4) NULL,
        data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (endereco_carteira, id_moeda),
        CONSTRAINT saldo_carteira_endereco_fk FOREIGN KEY (endereco_carteira) REFERENCES carteira (endereco_carteira) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT saldo_carteira_id_moeda_fk FOREIGN KEY (id_moeda) REFERENCES moeda (id_moeda) ON UPDATE CASCADE ON DELETE CASCADE
    );

CREATE TABLE
    IF NOT EXISTS deposito_saque (
        id_movimento BIGINT AUTO_INCREMENT PRIMARY KEY,
        endereco_carteira VARCHAR(32) NOT NULL,
        id_moeda SMALLINT NOT NULL,
        tipo ENUM ('DEPOSITO', 'SAQUE') NULL,
        valor DECIMAL(18, 4) NOT NULL,
        taxa_valor DECIMAL(18, 4) NULL,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        CONSTRAINT deposito_saque_endereco_carteira_fk FOREIGN KEY (endereco_carteira) REFERENCES carteira (endereco_carteira),
        CONSTRAINT deposito_saque_id_moeda_fk FOREIGN KEY (id_moeda) REFERENCES moeda (id_moeda)
    );

-- 2. Preenchimento das tabelas
INSERT IGNORE INTO moeda (id_moeda, codigo, nome, tipo)
VALUES
    (1, 'BTC', 'Bitcoin', 'CRIPTO'),
    (2, 'ETH', 'Ethereum', 'CRIPTO'),
    (3, 'SOL', 'Solana', 'CRIPTO'),
    (4, 'USD', 'Dólar Americano', 'FIDUCIÁRIA');

INSERT IGNORE INTO carteira (endereco_carteira, hash_chave_privada, status)
VALUES
    (
        'a2a6cf793e0e940706d19cbc5866cfb8',
        'ac2d1d01d8b22bfce90145af8e2e7a9fb5807a26b49ece5c8acf34d6aee2e4e2',
        'ATIVA'
    ),
    (
        '5ef83ac052d884f0cd86a8f876165513',
        'ba45ccec895ca76d693afe6c187ac2746ad09c781cab8e1f3bc7d8a0c0f1e7bb',
        'ATIVA'
    );

INSERT IGNORE INTO saldo_carteira (endereco_carteira, id_moeda, saldo)
VALUES
    ('a2a6cf793e0e940706d19cbc5866cfb8', 1, 100.0),
    ('a2a6cf793e0e940706d19cbc5866cfb8', 2, 1.0),
    ('5ef83ac052d884f0cd86a8f876165513', 1, 50.0);

-- 3. Exemplo de movimentações
CREATE TABLE
    IF NOT EXISTS conversao (
        id_conversao BIGINT AUTO_INCREMENT PRIMARY KEY,
        endereco_carteira VARCHAR(32) NOT NULL,
        id_moeda_origem SMALLINT NOT NULL,
        id_moeda_destino SMALLINT NOT NULL,
        valor_origem DECIMAL(18, 4) NOT NULL,
        valor_destino DECIMAL(18, 4) NULL,
        taxa_percentual DECIMAL(5, 2) NULL,
        cotacao_utilizada DECIMAL(18, 4) NULL,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        CONSTRAINT conversao_endereco_fk FOREIGN KEY (endereco_carteira) REFERENCES carteira (endereco_carteira) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT conversao_id_moeda_origem_fk FOREIGN KEY (id_moeda_origem) REFERENCES moeda (id_moeda) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT conversao_id_moeda_destino_fk FOREIGN KEY (id_moeda_destino) REFERENCES moeda (id_moeda) ON UPDATE CASCADE ON DELETE CASCADE
    );

CREATE UNIQUE INDEX conversao_id_conversao_uindex ON conversao (id_conversao);
CREATE INDEX conversao_endereco_carteira_index ON conversao (endereco_carteira);

CREATE TABLE
    IF NOT EXISTS transferencia (
        id_transferencia BIGINT AUTO_INCREMENT PRIMARY KEY,
        endereco_origem VARCHAR(32) NOT NULL,
        endereco_destino VARCHAR(32) NOT NULL,
        id_moeda SMALLINT NOT NULL,
        valor DECIMAL(18, 4) NOT NULL,
        taxa_valor DECIMAL(5, 2) NULL,
        data_hora DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        CONSTRAINT transferencia_endereco_origem_fk FOREIGN KEY (endereco_origem) REFERENCES carteira (endereco_carteira) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT transferencia_endereco_destino_fk FOREIGN KEY (endereco_destino) REFERENCES carteira (endereco_carteira) ON UPDATE CASCADE ON DELETE CASCADE,
        CONSTRAINT transferencia_id_moeda_fk FOREIGN KEY (id_moeda) REFERENCES moeda (id_moeda) ON UPDATE CASCADE ON DELETE CASCADE
    );

CREATE UNIQUE INDEX transferencia_id_transferencia_uindex ON transferencia (id_transferencia);
CREATE INDEX transferencia_endereco_origem_index ON transferencia (endereco_origem);
CREATE INDEX transferencia_endereco_destino_index ON transferencia (endereco_destino);