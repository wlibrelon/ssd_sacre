CREATE TABLE `wps` (
  `id_wp` integer PRIMARY KEY,
  `wp` integer,
  `titulo` text,
  `descricao` text,
  `id_gerente` integer,
  `num_lista_colab` integer
);

CREATE TABLE `projetos_wps` (
  `id_projeto` integer PRIMARY KEY,
  `id_wp` integer,
  `titulo` text,
  `id_autor` integer,
  `resumo` text,
  `objetivos` text
);

CREATE TABLE `colaboradores` (
  `id_colaborador` integer PRIMARY KEY,
  `nome` varchar(50),
  `link_internet` varchar(255),
  `formacao` varchar(100)
);

CREATE TABLE `lista_colab` (
  `id_lista_colab` integer PRIMARY KEY,
  `id_colaborador` integer,
  `num_lista` integer
);

CREATE TABLE `arq_resultados` (
  `id_arq_res` integer PRIMARY KEY,
  `id_projeto` integer,
  `descricao` text,
  `nome_arq` varchar(30)
);

CREATE TABLE `artigos` (
  `id_Artigo` integer PRIMARY KEY,
  `id_projeto` integer,
  `Titulo` varchar(255),
  `Resumo` text,
  `Abstract` text,
  `Pasta_PDF` varchar(255)
);

CREATE TABLE `artigos_autores` (
  `id_artigo_autor` integer PRIMARY KEY,
  `id_artigo` integer,
  `id_autor` integer
);

CREATE TABLE `resultados` (
  `id_resultado` integer PRIMARY KEY,
  `id_ponto` integer,
  `id_campanha` integer,
  `id_wp` integer,
  `res_quimico` varchar(30),
  `nome_amostra` varchar(30),
  `data` date,
  `parametro` varchar(30),
  `simbolo` varchar(20),
  `unidade` varchar(10),
  `controle` varchar(1),
  `resultado` float,
  `erro` float,
  `lab` varchar(30),
  `obs` text,
  `prof_inicial_solo` float,
  `prof_final_solo` float
);

CREATE TABLE `campanha` (
  `id_campanha` integer PRIMARY KEY,
  `id_wp` integer,
  `cod_campanha` varchar(20),
  `data_inicio` date,
  `data_fim` date,
  `tipo_campanha` varchar(30),
  `obs` text
);

CREATE TABLE `pontos_monitoramento` (
  `id_ponto` integer PRIMARY KEY,
  `codigo` varchar(20),
  `descricao` varchar(30),
  `id_wp` integer,
  `tipo_amostra` varchar(30),
  `coord_x` float,
  `coord_y` float,
  `coord_z` float,
  `profundidade` float,
  `instalacao` varchar(30),
  `tipo_estacao` varchar(30),
  `obs` text
);

ALTER TABLE `projetos_wps` ADD FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `lista_colab` ADD FOREIGN KEY (`num_lista`) REFERENCES `wps` (`num_lista_colab`);

ALTER TABLE `wps` ADD FOREIGN KEY (`id_gerente`) REFERENCES `colaboradores` (`id_colaborador`);

ALTER TABLE `arq_resultados` ADD FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `artigos` ADD FOREIGN KEY (`id_projeto`) REFERENCES `projetos_wps` (`id_projeto`);

ALTER TABLE `artigos` ADD FOREIGN KEY (`id_Artigo`) REFERENCES `artigos_autores` (`id_artigo`);

ALTER TABLE `colaboradores` ADD FOREIGN KEY (`id_colaborador`) REFERENCES `artigos_autores` (`id_autor`);

ALTER TABLE `resultados` ADD FOREIGN KEY (`id_wp`) REFERENCES `wps` (`id_wp`);

ALTER TABLE `resultados` ADD FOREIGN KEY (`id_campanha`) REFERENCES `campanha` (`id_campanha`);

ALTER TABLE `resultados` ADD FOREIGN KEY (`id_ponto`) REFERENCES `pontos_monitoramento` (`id_ponto`);
