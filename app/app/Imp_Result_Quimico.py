import pandas as pd
import mysql.connector
from mysql.connector import Error
from funcoes_app import conectar_banco


# Função para importar dados do CSV para o MySQL
def import_csv_to_mysql(file_path, connection):
    # Carregar o arquivo CSV
    # df = pd.read_csv(file_path, delimiter=',', encoding='utf-8')
    df = pd.read_csv(file_path, delimiter=',', encoding='latin1') 

    # Renomear colunas para garantir que 'Collection_date' seja renomeado como 'data'
    df.rename(columns={
        'tipo_resultado': 'tipo_resultado',
        'id_station': 'id_ponto',
        'id_campanha': 'id_Campanha',
        'Sample_name': 'nome_amostra',
        'Collection_date': 'data',  # Renomear para 'data'
        'Start_depth': 'profund_inicial_solo',
        'End_depth': 'profund_final_solo',
        'Parameter': 'parametro',
        'Symbol': 'simbolo',
        'Unit': 'unidade',
        'Result': 'resultado',
        'Error': 'erro',
        'Lab': 'lab',
        'WP': 'wp',
        'Obs': 'obs'
    }, inplace=True)

    # Converter a coluna 'data' para o formato 'YYYY-MM-DD', preenchendo valores inválidos com '1900-01-01'
    if 'data' in df.columns:  # Verificar se a coluna 'data' existe
        df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y', errors='coerce')
        df['data'] = df['data'].fillna(pd.Timestamp('1900-01-01')).dt.strftime('%Y-%m-%d')
    else:
        raise KeyError("A coluna 'Collection_date' não foi encontrada no arquivo CSV.")

    # Tratar a coluna 'Result' para configurar 'Flag' e ajustar valores
    def process_result(row):
        try:
            # Caso o valor seja uma string e comece com "<" ou ">"
            if isinstance(row, str):
                if row.strip().startswith('<'):
                    return float(row.strip().replace('<', '').replace(',', '.')), '<'
                elif row.strip().startswith('>'):
                    return float(row.strip().replace('>', '').replace(',', '.')), '>'
                else:
                    # Tentar converter strings numéricas padrão
                    return float(row.replace(',', '.')), ' '
            # Se o valor já for numérico
            return float(row), ' '  # String vazia para o campo 'Flag'

        # Caso a conversão falhe (ex.: valor como 'LD')
        except (ValueError, AttributeError):
            return 0.0, 'L'  # Substituir valor inválido por 0.0 e flag 'LD'

    # Aplicar a transformação na coluna 'Resultado'
    df[['resultado', 'flag']] = df['resultado'].apply(lambda x: pd.Series(process_result(x)))

    # Adicionar a coluna 'Erro' com valores padrões (já que não é fornecida no CSV)
    df['erro'] = 0.0

    # Substituir NaN por valores padrão:
    # - Strings vazias para texto ('')
    # - Números 0 (float ou int) para campos numéricos
    df = df.fillna({
        'id_ponto': 0,
        'id_Campanha': 0,
        'wp': 0,
        'nome_amostra': '',
        'parametro': '',
        'simbolo': '',
        'unidade': '',
        'flag': ' ',
        'resultado': 0,
        'erro': 0,
        'lab': '',
        'obs': '',
        'profund_inicial_solo': 0.0,
        'profund_final_solo': 0.0
    })

    # Preparar a consulta de inserção
    insert_query = """
        INSERT INTO resultados_quim (
            id_ponto, id_Campanha, id_WP, tipo_resultado, 
            nome_amostra, data, parametro, simbolo, unidade, 
            flag, resultado, erro, lab, obs, 
            profund_inicial_solo, profund_final_solo
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Converter o DataFrame como uma lista de tuplas para o MySQL
    data_to_insert = df[[
        'id_ponto', 'id_Campanha', 'wp', 'tipo_resultado',
        'nome_amostra', 'data', 'parametro', 'simbolo', 'unidade',
        'flag', 'resultado', 'erro', 'lab', 'obs',
        'profund_inicial_solo', 'profund_final_solo'
    ]].values.tolist()

    # Verificar os dados preparados antes da inserção
    print("Exemplo de dados preparados para inserção:")
    print(data_to_insert[:3])  # Exibe as 3 primeiras linhas apenas para conferência

    # Inserir os dados no banco de dados
    cursor = connection.cursor()
    try:
        cursor.executemany(insert_query, data_to_insert)
        connection.commit()
        print(f"{cursor.rowcount} registros foram inseridos com sucesso na tabela resultados_quim.")
    except Error as e:
        print(f"Erro ao inserir os dados no MySQL: {e}")
    finally:
        cursor.close()

# Configuração principal
if __name__ == "__main__":
    # Caminho do arquivo CSV
    file_path = "D:/SACRE/SSD/Dados/resultados_quim.csv"  # Substitua pelo caminho do CSV

    # import chardet

    # # Detectar a codificação do arquivo
    # with open("D:/SACRE/SSD/Dados/resultados_agua.csv", "rb") as file:
    #     result = chardet.detect(file.read())
    #     print(f"Codificação detectada: {result['encoding']}")


    # Conectar ao banco e importar os dados
    connection = conectar_banco()
    if connection:
        try:
            import_csv_to_mysql(file_path, connection)
        finally:
            connection.close()