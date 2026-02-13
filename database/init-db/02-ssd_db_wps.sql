CREATE DATABASE  IF NOT EXISTS `ssd_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `ssd_db`;
-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: ssd_db
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `wps`
--

LOCK TABLES `wps` WRITE;
/*!40000 ALTER TABLE `wps` DISABLE KEYS */;
INSERT INTO `wps` VALUES (1,1,'Contaminação por nitrogênio e vulnerabilidade às mudanças climáticas...','Fontes, destino e transporte de nitrogênio (N) e de outros contaminantes das águas subterrâneas urbanas e rurais.Por que o nitrogênio? Além de sua toxicidade, a contaminação por N fornece um indicador da extensão dos impactos  humanos e, devido à sua ocorrência sob muitas formas químicas, também caracteriza as mudanças nas condições geoquímicas ao longo do ciclo hidrológico.',5,'Work Package 1'),(2,2,'Soluções baseadas na natureza para incrementar a qualidade e quantidade dos recursos hídricos','Análise de serviços ecossistêmicos hídricos em áreas urbanas verdes e avaliação da eficiência de tratamentos usando Soluções Baseadas na Natureza (Nature-based-Solutions: NbS). Por que usar NbS?\n As NbS estão representadas por coberturas vegetais naturais usadas na remediação de água contaminada urbana (notadamente N e contaminantes emergentes). Elas induzem maior disponibilidade de água limpa em aquíferos por meio de Recarga Gerenciada de Aquíferos (Managed Aquifer Recharge: MAR).',5,'Work Package 2'),(3,3,'Sistema in situ e tratamento da contaminação das águas subterrâneas urbanas','Remediação da contaminação de aquíferos resultante de fontes não pontuais ou difusas, que representa hoje um dos maiores desafios na ciência ambiental.\n Como?\n Desenvolvendo novos materiais que serão usados em barreiras reativas permeáveis (PRB) projetadas para capturar e tratar plumas aquíferas.',5,'Work Package 3'),(4,4,'Uso conjuntivo de múltiplas fontes de água para abastecer a cidade e a agricultura','Caracterização hidrodinâmica dos aquíferos e rios, buscando o seu melhor aproveitamento para o abastecimento público e privado e a redução das vulnerabilidades hidroclimáticas em cidades e no campo.\n O que fazemos?\n Criamos e adaptamos técnicas como a Filtração de Margens de Rios (River Bank Filtration: RBF) e a MAR, bem como o uso planejado de um aquífero fóssil (Sistema Aquífero Guarani).\n Desenvolvemos uma estratégia de alocação dos recursos hídricos baseada no uso conjuntivo de águas superficiais e subterrâneas, incorporando produtores privados de água ao abastecimento público urbano e às áreas rurais.',5,'Work Package 4'),(5,5,'Métodos econômicos e políticos para incentivar a gestão sustentável das águas e melhorar a segurança hídrica','Conjunto de métodos, ferramentas e instrumentos políticos hidroeconômicos integrados, organizados em uma plataforma (HYMP), para apoiar e incentivar estratégias sustentáveis de uso e gerenciamento da água em um ambiente de incertezas climáticas.\n Por que o  HYMP? Ele unifica de forma original todos os resultados do SACRE e leva em conta os usos e serviços múltiplos das águas em uma escala de bacia hidrográfica, os impactos do clima e da mudança no uso da terra no suprimento e na qualidade da água.',5,'Work Package 5'),(6,6,'Investigação de processos do ciclo do nitrogênio em escala de poro','Processos hidrobiogeoquímicos que controlam a ocorrência das espécies nitrogenadas em escala de poro e, consequentemente, seu transporte e destino em escala de aquífero.\n  Por que escala de poro? A caracterização dos microambientes responsáveis pela atenuação do nitrato a nitrogênio ou a suas fases intermediárias (N2O e NO) auxiliará na compreensão do papel efetivo de mecanismos antrópicos e hidrobiogeoquímicos no controle da extensão da contaminação dos recursos hídricos por essas espécies.',5,'Work Package 6');
/*!40000 ALTER TABLE `wps` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-13 18:36:01
