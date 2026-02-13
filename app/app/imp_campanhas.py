import csv
import mysql.connector
from datetime import datetime
from funcoes_app import conectar_banco

# Função para importar os dados do CSV para a tabela MySQL
def importar_campanhas(nome_arquivo_csv, nome_tabela):
    try:
        # Conecta ao banco de dados
        conn = conectar_banco()
        cursor = conn.cursor()

        # Abre o arquivo CSV
        with open(nome_arquivo_csv, mode='r', encoding='utf-8') as csvfile:
            leitor_csv = csv.reader(csvfile)
            headers = next(leitor_csv)  # Pula o cabeçalho

            # Prepara o comando de inserção no MySQL
            query_insert = f"""
            INSERT INTO {nome_tabela} 
            (cod_Campanha, data_inicio, data_fim, tipo_Campanha, id_WP, Obs)
            VALUES (%s, %s, %s, %s, %s, %s)
            """

            # Lê e insere cada linha do CSV
            dados = []
            for linha in leitor_csv:
                try:
                    # Extrai os valores das colunas do CSV
                    cod_Campanha = linha[0].strip()  # Código da campanha
                    data_inicio = None
                    if linha[1].strip() != '':
                        try:
                            # Converta data_inicio no formato YYYY-MM-DD
                            data_inicio = datetime.strptime(linha[1].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Erro na conversão de data_inicio: {linha[1]} (linha {leitor_csv.line_num})")
                            continue  # Ignora a linha com erro de data

                    data_fim = None
                    if linha[2].strip() != '':
                        try:
                            # Converta data_fim no formato YYYY-MM-DD
                            data_fim = datetime.strptime(linha[2].strip(), '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Erro na conversão de data_fim: {linha[2]} (linha {leitor_csv.line_num})")
                            continue  # Ignora a linha com erro de data

                    tipo_Campanha = linha[3].strip()  # Tipo da campanha
                    id_WP = int(linha[4].strip()) if linha[4].strip() != '' else -99  # WP
                    Obs = linha[5].strip() if linha[5].strip() != '' else None  # Observação

                    # Adiciona a linha aos dados para inserção
                    dados.append((cod_Campanha, data_inicio, data_fim, tipo_Campanha, id_WP, Obs))
                except Exception as e:
                    print(f"Erro inesperado ao processar a linha {leitor_csv.line_num}: {e}")
                    continue  # Ignora a linha e segue com as próximas

            # Executa a inserção dos dados no banco
            if dados:  # Apenas tenta a inserção se houver dados válidos
                cursor.executemany(query_insert, dados)
                conn.commit()  # Confirma as alterações no banco de dados
                print(f"{cursor.rowcount} registros inseridos com sucesso!")
            else:
                print("Nenhum registro válido para inserir!")

    except mysql.connector.Error as erro:
        print(f"Erro ao inserir os dados no MySQL: {erro}")
    except Exception as erro_geral:
        print(f"Ocorreu um erro: {erro_geral}")
    finally:
        # Fecha a conexão com o banco
        if conn.is_connected():
            cursor.close()
            conn.close()

# Nome do arquivo CSV
nome_arquivo = "D:/SACRE/SSD/Dados/campanhas.csv"
# Nome da tabela no banco (deve ser a mesma do CSV)
nome_tabela = "Campanhas"

# Chama a função para importar os dados
importar_campanhas(nome_arquivo, nome_tabela)