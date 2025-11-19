CREATE TABLE `artigos` (
  `Id_Artigo` integer PRIMARY KEY,
  `id_projeto` intger,
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
  `Objetivos` text
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

ALTER TABLE `tb_mananciais` ADD FOREIGN KEY (`id_manancial`) REFERENCES `tb_ativ_mananciais` (`id_manancial`);

ALTER TABLE `tb_acoes` ADD FOREIGN KEY (`id_acao`) REFERENCES `tb_mananciais` (`id_acao`);
