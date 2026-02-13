-- CREATE DATABASE ssd_db
-- CHARACTER SET utf8mb4
-- COLLATE utf8mb4_unicode_ci;

USE ssd_db;

CREATE TABLE `wps` (
  `id_wp` INTEGER AUTO_INCREMENT PRIMARY KEY,
  `wp` INTEGER,
  `titulo` TEXT,
  `descricao` TEXT,
  `menu` varchar(20),
  `id_gerente` INTEGER
) ENGINE=InnoDB;

CREATE TABLE `projetos_wps` (
  `id_projeto`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_wp` INTEGER,
  `titulo` TEXT,
  `id_autor` INTEGER,
  `resumo` TEXT,
  `objetivos` TEXT,
  INDEX `idx_id_wp` (`id_wp`) 
) ENGINE=InnoDB;

CREATE TABLE `colaboradores` (
  `id_colaborador` INTEGER AUTO_INCREMENT PRIMARY KEY,
  `nome` VARCHAR(50),
  `link_internet` VARCHAR(255),
  `formacao` VARCHAR(100)
) ENGINE=InnoDB;

CREATE TABLE `lista_colab` (
  `id_lista_colab`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_colaborador` INTEGER,
  `id_wp` INTEGER,
  INDEX `idx_id_colaborador` (`id_colaborador`),
  INDEX `idx_id_wp` (`id_wp`)
) ENGINE=InnoDB;

CREATE TABLE `arq_resultados` (
  `id_arq_res`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_projeto` INTEGER,
  `descricao` TEXT,
  `nome_arq` VARCHAR(30),
  INDEX `idx_id_projeto` (`id_projeto`)  
) ENGINE=InnoDB;

CREATE TABLE `artigos` (
  `id_Artigo`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_projeto` INTEGER,
  `titulo` VARCHAR(255),
  `resumo` TEXT,
  `abstract` TEXT,
  `doi` VARCHAR(50),
  `pasta_pdf` VARCHAR(255),
  `tipo` varchar(10),
  INDEX `idx_id_projeto` (`id_projeto`) 
) ENGINE=InnoDB;

CREATE TABLE `artigos_autores` (
  `id_artigo_autor`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_artigo` INTEGER,
  `id_autor` INTEGER,
  INDEX `idx_id_artigo` (`id_artigo`), 
  INDEX `idx_id_autor` (`id_autor`) 
) ENGINE=InnoDB;

CREATE TABLE `resultados` (
  `id_resultado`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_ponto` INTEGER,
  `id_campanha` INTEGER,
  `id_wp` INTEGER,
  `res_quimico` VARCHAR(30),
  `nome_amostra` VARCHAR(30),
  `data` DATE,
  `parametro` VARCHAR(30),
  `simbolo` VARCHAR(20),
  `unidade` VARCHAR(10),
  `controle` VARCHAR(1),
  `resultado` FLOAT,
  `erro` FLOAT,
  `lab` VARCHAR(30),
  `obs` TEXT,
  `prof_inicial_solo` FLOAT,
  `prof_final_solo` FLOAT,
  INDEX `idx_id_wp` (`id_wp`), 
  INDEX `idx_id_campanha` (`id_campanha`), 
  INDEX `idx_id_ponto` (`id_ponto`)  
) ENGINE=InnoDB;

CREATE TABLE `campanha` (
  `id_campanha`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `id_wp` INTEGER,
  `cod_campanha` VARCHAR(20),
  `data_inicio` DATE,
  `data_fim` DATE,
  `tipo_campanha` VARCHAR(30),
  `obs` TEXT,
  INDEX `idx_id_wp` (`id_wp`)  
) ENGINE=InnoDB;

CREATE TABLE `pontos_monitoramento` (
  `id_ponto`  INTEGER AUTO_INCREMENT PRIMARY KEY,
  `codigo` VARCHAR(20),
  `descricao` VARCHAR(30),
  `id_wp` INTEGER,
  `tipo_amostra` VARCHAR(30),
  `coord_x` FLOAT,
  `coord_y` FLOAT,
  `coord_z` FLOAT,
  `profundidade` FLOAT,
  `instalacao` VARCHAR(30),
  `tipo_estacao` VARCHAR(30),
  `obs` TEXT,
  INDEX `idx_id_wp` (`id_wp`) 
) ENGINE=InnoDB;

ALTER TABLE `projetos_wps` ADD CONSTRAINT `fk_projetos_wps_wps` FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `lista_colab` ADD CONSTRAINT `fk_id_wp_wps` FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `wps` ADD CONSTRAINT `fk_wps_colaboradores` FOREIGN KEY (`id_gerente`) REFERENCES `colaboradores` (`id_colaborador`);

ALTER TABLE `arq_resultados` ADD CONSTRAINT `fk_arq_resultados_projetos_wps` FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `artigos` ADD CONSTRAINT `fk_artigos_projetos_wps` FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `artigos_autores` ADD CONSTRAINT `fk_artigos_autores_artigos` FOREIGN KEY (`id_artigo`) REFERENCES `artigos` (`id_Artigo`);

ALTER TABLE `artigos_autores` ADD CONSTRAINT `fk_artigos_autores_colaboradores` FOREIGN KEY (`id_autor`) REFERENCES `colaboradores` (`id_colaborador`);

ALTER TABLE `lista_colab` ADD CONSTRAINT `fk_lista_colab_colaboradores` FOREIGN KEY (`id_colaborador`) REFERENCES `colaboradores` (`id_colaborador`);

ALTER TABLE `resultados` ADD CONSTRAINT `fk_resultados_wps` FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `resultados` ADD CONSTRAINT `fk_resultados_campanha` FOREIGN KEY (`id_campanha`) REFERENCES `campanha` (`id_campanha`);

ALTER TABLE `resultados` ADD CONSTRAINT `fk_resultados_pontos_monitoramento` FOREIGN KEY (`id_ponto`) REFERENCES `pontos_monitoramento` (`id_ponto`);

ALTER TABLE `campanha` ADD CONSTRAINT `fk_campanha_wps` FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `pontos_monitoramento` ADD CONSTRAINT `fk_pontos_monitoramento_wps` FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);