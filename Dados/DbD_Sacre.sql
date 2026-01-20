CREATE TABLE `artigos` (
  `Id_Artigo` integer PRIMARY KEY,
  `id_projeto` integer,
  `Titulo` varchar(255),
  `Resumo` text,
  `Abstract` text,
  `Pasta_PDF` varchar(255)
);

CREATE TABLE `pesquisadores` (
  `id_pesquisador` integer PRIMARY KEY,
  `nome` varchar(50),
  `link_internet` varchar(255)
);

CREATE TABLE `artigos_autores` (
  `id_artigo_autor` integer PRIMARY KEY,
  `id_artigo` integer,
  `id_autor` integer
);

CREATE TABLE `wps` (
  `id_wp` integer PRIMARY KEY,
  `wp` integer,
  `titulo` text,
  `descricao` text,
  `id_gerente` integer,
  `id_colaboradores` intger
);

CREATE TABLE `colaboradores` (
  `id_colaboradores` integer PRIMARY KEY,
  `id_autor` integer
);

CREATE TABLE `projetos_wps` (
  `id_projeto` integer PRIMARY KEY,
  `id_wp` integer,
  `titulo` text,
  `id_autor` integer,
  `resumo` text,
  `objetivos` text
);

CREATE TABLE `arq_resultados` (
  `id_arq_res` integer PRIMARY KEY,
  `id_projeto` integer,
  `descricao` text,
  `nome_arq` varchar(30)
);

CREATE TABLE `resultados_quim` (
  `id_resultado` int AUTO_INCREMENT PRIMARY KEY,
  `id_ponto` integer,
  `id_Campanha` integer,
  `id_WP` integer,
  `tipo_resultado` varchar(30),
  `nome_amostra` varchar(30),
  `data` date,
  `parametro` varchar(30),
  `simbolo` varchar(20),
  `unidade` varchar(10),
  `flag` varchar(1),
  `resultado` float,
  `erro` float,
  `lab` varchar(30),
  `obs` text,
  `profund_inicial_solo` float,
  `profund_final_solo` float
);



CREATE TABLE `Campanhas` (
  `id_Campanha` integer AUTO_INCREMENT PRIMARY KEY,
  `id_WP` integer,
  `cod_Campanha` varchar(20),
  `data_inicio` date,
  `data_fim` date,
  `tipo_Campanha` varchar(50),
  `Obs` text
);

CREATE TABLE `pontos_monitorados` (
  `id_ponto` integer AUTO_INCREMENT PRIMARY KEY ,
  `cod_ponto` varchar(20),
  `id_WP` integer,
  `tipo_amostra` varchar(30),
  `coord_x` float,
  `coord_y` float,
  `coord_z` float,
  `latitude` decimal(18,15),
  `longitude` decimal(18,15),
  `profundidade` float,
  `data_instalacao` varchar(30),
  `tipo_estacao` varchar(30),
  `obs` text
);

CREATE TABLE `tb_acoes` (
  `id_acao` integer PRIMARY KEY,
  `nome_acao` varchar(50)
);

CREATE TABLE `tb_mananciais` (
  `id_manancial` integer PRIMARY KEY,
  `id_acao` integer,
  `nome_manancial` varchar(50)
);

CREATE TABLE `tb_ativ_mananciais` (
  `id_ativ_man` integer PRIMARY KEY,
  `id_manancial` integer
);

ALTER TABLE `artigos` ADD FOREIGN KEY (`Id_Artigo`) REFERENCES `artigos_autores` (`id_artigo`);

ALTER TABLE `pesquisadores` ADD FOREIGN KEY (`id_pesquisador`) REFERENCES `artigos_autores` (`id_autor`);

ALTER TABLE `artigos` ADD FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `wps` ADD FOREIGN KEY (`id_gerente`) REFERENCES `pesquisadores` (`id_pesquisador`);

ALTER TABLE `colaboradores` ADD FOREIGN KEY (`id_colaboradores`) REFERENCES `wps` (`id_colaboradores`);

ALTER TABLE `colaboradores` ADD FOREIGN KEY (`id_autor`) REFERENCES `pesquisadores` (`id_pesquisador`);

ALTER TABLE `projetos_wps` ADD FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `projetos_wps` ADD FOREIGN KEY (`id_autor`) REFERENCES `pesquisadores` (`id_pesquisador`);

ALTER TABLE `arq_resultados` ADD FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `resultados_quim` ADD FOREIGN KEY (`id_WP`) REFERENCES `wps` (`wp`);

ALTER TABLE `resultados_quim` ADD FOREIGN KEY (`id_Campanha`) REFERENCES `Campanha` (`id_Campanha`);

ALTER TABLE `resultados_quim` ADD FOREIGN KEY (`id_ponto`) REFERENCES `pontos_monitorados` (`id_Ponto`);

ALTER TABLE `tb_mananciais` ADD FOREIGN KEY (`id_manancial`) REFERENCES `tb_ativ_mananciais` (`id_manancial`);

ALTER TABLE `tb_acoes` ADD FOREIGN KEY (`id_acao`) REFERENCES `tb_mananciais` (`id_acao`);
