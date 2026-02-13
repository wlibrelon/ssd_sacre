import csv
import mysql.connector
from datetime import datetime
from funcoes_app import conectar_banco

# Função para importar os dados do CSV para a tabela MySQL
def importar_csv_para_mysql(nome_arquivo_csv, nome_tabela):
    try:
        # Conecta ao banco de dados
        conn = conectar_banco()
        cursor = conn.cursor()
        
        # Abre o arquivo CSV
        with open(nome_arquivo_csv, mode='r', encoding='utf-8') as csvfile:
            leitor_csv = csv.reader(csvfile)
            headers = next(leitor_csv)  # Pula o cabeçalho
            
            # Prepara o comando de inserção no MySQL (ajustado para cod_ponto se for o nome no banco; mude para codigo se necessário)
            query_insert = f"""
            INSERT INTO {nome_tabela} 
            (cod_ponto, id_wp, tipo_amostra, coord_x, coord_y, coord_z, latitude, longitude, profundidade, data_instalacao, tipo_estacao, obs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Contador de linhas inseridas
            linhas_inseridas = 0
            
            # Lê e insere cada linha do CSV individualmente
            for linha_num, linha in enumerate(leitor_csv, start=2):  # Começa na linha 2 (após header)
                try:
                    # Atribuição com base na ordem assumida do CSV (ajuste índices se necessário)
                    cod_ponto = linha[0] if linha[0].strip() != '' else None  # Coluna 0: codigo/cod_ponto
                    id_wp = int(linha[1]) if linha[1].strip() != '' else -99  # Coluna 1: id_wp/wp
                    tipo_amostra = linha[2] if linha[2].strip() != '' else None  # Coluna 2: tipo_amostra
                    coord_x = float(linha[3]) if linha[3].strip() != '' else -99  # Coluna 3: coord_x
                    coord_y = float(linha[4]) if linha[4].strip() != '' else -99  # Coluna 4: coord_y
                    coord_z = float(linha[5]) if linha[5].strip() != '' else -99  # Coluna 5: coord_z
                    latitude = float(linha[6]) if linha[6].strip() != '' else -99  # Coluna 6: latitude
                    longitude = float(linha[7]) if linha[7].strip() != '' else -99  # Coluna 7: longitude
                    profundidade = float(linha[8]) if linha[8].strip() != '' else -99  # Coluna 8: profundidade
                    
                    # Converte a data para o formato adequado (YYYY-MM-DD)
                    data_instalacao = None
                    if linha[9].strip() != '':
                        try:
                            data_instalacao = datetime.strptime(linha[9], '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Erro na conversão da data na linha {linha_num}: {linha[9]} - Ignorando linha.")
                            continue
                    
                    tipo_estacao = linha[10] if linha[10].strip() != '' else None  # Coluna 10: tipo_estacao
                    obs = linha[11] if linha[11].strip() != '' else None  # Coluna 11: obs
                    
                    # Tupla com valores na ORDEM EXATA das colunas na query
                    dados_linha = (
                        cod_ponto, id_wp, tipo_amostra, coord_x, coord_y, coord_z, 
                        latitude, longitude, profundidade, data_instalacao, tipo_estacao, obs
                    )
                    
                    # Depuração: Mostra o que está sendo inserido
                    print(f"Linha {linha_num}: Inserindo longitude={longitude} no campo longitude, profundidade={profundidade} no campo profundidade, coord_y={coord_y} no campo coord_y")
                    
                    # Executa inserção para esta linha
                    cursor.execute(query_insert, dados_linha)
                    linhas_inseridas += 1
                
                except mysql.connector.Error as erro_mysql:
                    print(f"Erro MySQL na linha {linha_num}: {erro_mysql} - Ignorando linha.")
                    continue
                except Exception as erro_geral:
                    print(f"Erro geral na linha {linha_num}: {erro_geral} - Ignorando linha.")
                    continue
            
            conn.commit()  # Confirma as alterações no banco de dados
            print(f"Importação concluída! {linhas_inseridas} registros inseridos com sucesso.")
    
    except mysql.connector.Error as erro:
        print(f"Erro ao conectar ou inserir no MySQL: {erro}")
    except Exception as erro_geral:
        print(f"Ocorreu um erro geral: {erro_geral}")
    finally:
        # Fecha a conexão com o banco
        if conn.is_connected():
            cursor.close()
            conn.close()

# Nome do arquivo CSV
nome_arquivo = "D:/SACRE/SSD/Dados/pontos_monitorados.csv"
# Nome da tabela no banco
nome_tabela = "pontos_monitorados"

# Chama a função para importar os dados
importar_csv_para_mysql(nome_arquivo, nome_tabela)