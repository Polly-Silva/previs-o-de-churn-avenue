# -*- coding: utf-8 -*-
"""Projeto_DEX_G03_shap220822.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WBbNuvz9oBXj84LcWLPjciAmncvYzjVg

# Projeto DEX

#1. Business Understanding

#2. Data Understanding

##Importando bibliotecas
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn
from sklearn.ensemble import RandomForestClassifier


import warnings
warnings.filterwarnings("ignore")

pip install shap

#pip install -q pyngrok
#!pip install -q pyspark

"""##Funções"""

def concat_info(df1, df2, axis=0):
  """Concatena dois dataframes e imprime uma descrição
  do dataframe final."""

  # Concatenando os dataframes
  df_concatenado = pd.concat((df1, df2), axis=axis)

  # Filtrando clientes que realizaram mais de 3 evasões
  # idx_drop = df_concatenado[df_concatenado['AccountID'].isin(drop_evasions['index'])].index
  # df_concatenado = df_concatenado.drop(index=idx_drop)

  # Calculando a porcentagem de Ids únicos
  pct_df1 = round((df1["AccountID"].nunique()/df1.shape[0])*100, 2)
  pct_df2 = round((df2["AccountID"].nunique()/df2.shape[0])*100, 2)
  pct_concatenado = round((df_concatenado["AccountID"].nunique()/df_concatenado.shape[0])*100, 2)

  # Imprimindo o shape e pct das partes e do todo
  print('_'*50 + '\n')

  print(f'Dimensões do dataframe 1: {df1.shape} \nPct de IDs únicos: {pct_df1}%\n')
  print(f'Dimensões do dataframe 2: {df2.shape} \nPct de IDs únicos: {pct_df2}%\n')
  print(f'Dimensões do dataframe completo: {df_concatenado.shape} \nPct de IDs únicos: {pct_concatenado}%')

  # Imprimindo as informações gerais do df final
  print('_'*50 + '\n')

  df_concatenado.info()
  print('_'*50 + '\n')

  return df_concatenado     # Retornando o df concatenado

"""## Importando o dataset

Alterar para o drive do grupo ou de quem estiver rodando.
"""

from google.colab import drive
drive.mount('/content/drive')

# Dados de contas de evasão
dfe_accounts = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/evaded_accounts/accounts.csv')
dfe_monthly = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/evaded_accounts/monthly_custody.csv')
dfe_movement = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/evaded_accounts/movement.csv')
dfe_orders = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/evaded_accounts/orders.csv')
dfe_evasion = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/evaded_accounts/evasion.csv')

# Dados de contas ativas
dfa_accounts = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/active_accounts/active_accounts.csv')
dfa_monthly = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/active_accounts/monthly_custody_active_accounts.csv')
dfa_movement = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/active_accounts/movement_active_accounts.csv')
dfa_orders = pd.read_csv('/content/drive/MyDrive/Projeto Dex - Avenue/Dados Avenue Atualizados/active_accounts/orders_active_accounts.csv')

"""##Concatenando as tabelas (evasão + ativos) & Descrição inicial

### Tabela Evasion

Para essa tabela não foi feita a concatenação, pois só temos os valores para o grupo Churn.
"""

dfe_evasion.head(3)

dfe_evasion.info()

"""Convertendo o formato da coluna 'Date'"""

dfe_evasion['Date'] = pd.to_datetime(dfe_evasion['Date'], infer_datetime_format=True)

"""Número de clientes que realizaram mais de 1 evasão."""

dfe_evasion['AccountID'].duplicated().sum()

"""Clientes que realizaram mais de 3 evasões"""

drop_evasions = dfe_evasion['AccountID'].value_counts().reset_index()
drop_evasions = drop_evasions[drop_evasions['AccountID'] > 3]
drop_evasions

"""65 clientes realizaram mais de 3 evasões. Estes registros serão excluídos da análise (Especulação de mercado)

Removendo clientes com mais de 3 evasões da tabela dfe_evasions
"""

idx_drop = dfe_evasion[dfe_evasion['AccountID'].isin(drop_evasions['index'])].index
dfe_evasion = dfe_evasion.drop(index=idx_drop)
dfe_evasion

"""Removendo clientes com mais de 3 evasões das outras tabelas"""

idx_eacc = dfe_accounts[dfe_accounts['AccountID'].isin(drop_evasions['index'])].index
idx_emes = dfe_monthly[dfe_monthly['AccountID'].isin(drop_evasions['index'])].index
idx_emov = dfe_movement[dfe_movement['AccountID'].isin(drop_evasions['index'])].index
idx_eord = dfe_orders[dfe_orders['AccountID'].isin(drop_evasions['index'])].index
idx_aacc = dfa_accounts[dfa_accounts['AccountID'].isin(drop_evasions['index'])].index
idx_ames = dfa_monthly[dfa_monthly['AccountID'].isin(drop_evasions['index'])].index
idx_amov = dfa_movement[dfa_movement['AccountID'].isin(drop_evasions['index'])].index
idx_aord = dfa_orders[dfa_orders['AccountID'].isin(drop_evasions['index'])].index

dfe_accounts = dfe_accounts.drop(index=idx_eacc)
dfe_monthly = dfe_monthly.drop(index=idx_emes)
dfe_movement = dfe_movement.drop(index=idx_emov)
dfe_orders = dfe_orders.drop(index=idx_eord)
dfa_accounts = dfa_accounts.drop(index=idx_aacc)
dfa_monthly = dfa_monthly.drop(index=idx_ames)
dfa_movement = dfa_movement.drop(index=idx_amov)
dfa_orders = dfa_orders.drop(index=idx_aord)

"""Resolvemos criar uma coluna com informações que auxiliem o modelo a prever casos de clientes que realizam mais de uma evasão.

A coluna criada corresponde ao número de Evasões anteriores a data em questão.


"""

def get_previous_evasion(df):
  df_ordenado = df.sort_values(by=['AccountID', 'Date'])
  df_ordenado['PreviousEvasions'] = 0
  id_atual = 'string'
  evasoes_previas = 0

  for idx in df_ordenado.index:
    id_loop = df_ordenado.loc[idx]['AccountID']
    if id_atual != id_loop:
      evasoes_previas = 1
      id_atual = id_loop
    else:
      df_ordenado.loc[idx, 'PreviousEvasions'] = evasoes_previas
      evasoes_previas += 1
    #print(idx)
  return df_ordenado

dfe_evasion = get_previous_evasion(dfe_evasion)
dfe_evasion

"""Validando o resultado"""

dfe_evasion.query("AccountID == '+7SYGFKJkHNigbsnw582VQ=='")

"""###Tabelas Accounts

Visão geral
"""

dfe_accounts.head(3)

"""O país de todos os clientes (PersonMailingCountry) é Brasil, logo não faz sentido manter esta coluna.

Será removida nas etapas seguintes.
"""

dfe_accounts['PersonMailingCountry'].value_counts()

"""Acrescentando a coluna Evaded aos dataframes Accounts.


*   Cliente ativo = 0
*   Cliente que evadiu = 1


"""

dfe_accounts['Evaded'] = 1    # Atribuindo 1 aos clientes que evadiram
dfa_accounts['Evaded'] = 0    # Atribuindo 0 aos clientes ativos

"""Concatenando os dois dataframes"""

acc = concat_info(dfe_accounts, dfa_accounts)

acc.head(3)

acc.describe()

acc.describe(include='object')

"""### Tabela Movement

Visão geral
"""

dfe_movement.head(3)

"""O significado da coluna HistoricId não ficou claro, talvez seja melhor removê-la."""

dfe_movement['HistoricId'].unique()

dfe_movement['Evaded'] = 1    # Atribuindo 1 aos clientes que evadiram
dfa_movement['Evaded'] = 0    # Atribuindo 0 aos clientes ativos

"""Concatenando os dois dataframes."""

mov = concat_info(dfe_movement, dfa_movement)

"""Outras tabelas também tem a informação de datas.

Em cada tabela a data tem um contexto, por isso adicionei o sufixo ao nome da coluna. Ex: Date -> DateMovement
"""

mov['Date'] = pd.to_datetime(mov['Date'], infer_datetime_format=True)
mov = mov.rename(columns={'Date': 'DateMovement'})

mov.head(3)

mov.describe()

mov.describe(include='object')

"""Adicionando colunas com evasões prévias"""

# Criando tabela com datas de evasões de cada cliente
datas_evasoes = dfe_evasion.groupby(by='AccountID')['Date'].unique().reset_index()
datas_evasoes

datas_evasoes.loc[17985, ['Date']][0][1]

# Adicionando as datas de evasões à tabela de movimentações
mov_test = mov.merge(datas_evasoes, how='left', on='AccountID', suffixes=('', '_evasoes'))
#mov['DateMovement_delta'] = (mov['DateMovement_last'] - mov['DateMovement']).dt.days
mov_test

# Função que retorna o número de evasões prévias para cada linha
def previous_evasion(row):
  if row['Evaded'] == 1 and len(row['Date']) == 1:
    if row['DateMovement'] <= row['Date'][0]:
      return 0
  if row['Evaded'] == 1 and len(row['Date']) == 2:
    if row['DateMovement'] <= row['Date'][0]:
      return 0
    if row['DateMovement'] <= row['Date'][1]:
      return 1
  if row['Evaded'] == 1 and len(row['Date']) == 3:
    if row['DateMovement'] <= row['Date'][0]:
      return 0
    if row['DateMovement'] <= row['Date'][1]:
      return 1
    if row['DateMovement'] <= row['Date'][2]:
      return 2

# Rodando a função - Criando uma nova coluna com o número de evasões prévias
mov_test['previous_results'] = mov_test.apply(previous_evasion, axis=1)
mov_test

#Dropando registros com data de movimentação posterior a evasão
idx = mov_test[mov_test['previous_results'].isnull() & mov_test['Evaded'] == 1].index
mov = mov_test.drop(index=idx)

"""As movimentações após evasões foram removidas, pois teoricamente são de clientes que evadiram e retornaram (estão ativos novamente) ou podem ser reflexos da evasão. Por isso, não faz sentido manter esses dados no modelo."""

#Preenchendo clientes sem evasões com 0
mov['previous_results'].fillna(0, inplace=True)

mov.isnull().sum()

mov.head()

mov['previous_results'].value_counts()

mov.shape

"""Filtro dos 15 dias"""

def last_day(dataframe, id, n_evasoes, data):
  results = dataframe.groupby([id, n_evasoes])[data].max().reset_index()
  return results

"""O objetivo dessa função é fornecer a data mais recente de cada cliente a depender do número de evasões prévias."""

last_mov = last_day(mov, 'AccountID', 'previous_results', 'DateMovement')
last_mov.head(3)

mov

mov.info()

mov = mov.merge(last_mov, how='left', on=['AccountID', 'previous_results'], suffixes=('', '_last'))
mov['DateMovement_delta'] = (mov['DateMovement_last'] - mov['DateMovement']).dt.days
mov.head(3)

"""Foram geradas duas novas colunas:
* data da última movimentação para o cliente
* intervalo entre movimentação daquela linha e a última movimentação do cliente.
"""

mov = mov[mov['DateMovement_delta'] >= 15]
mov

"""### Tabela Month

Visão geral
"""

dfe_monthly.head(3)

"""Tipos únicos de ativos/contas presentes na tabela."""

# Symbol
dfe_monthly['Symbol'].nunique()

"""Aparentemente nenhuma coluna precisa ser removida."""

dfe_monthly['Evaded'] = 1
dfa_monthly['Evaded'] = 0

"""Concatenando os dois dataframes."""

mes = concat_info(dfe_monthly, dfa_monthly)

mes['Date'] = pd.to_datetime(mes['Date'], infer_datetime_format=True)
mes = mes.rename(columns={'Date': 'DateMes'})

mes.head(3)

mes.describe()

mes.describe(include='object')

"""Função 1 - Contagem de evasoes previas"""

mes = mes.merge(datas_evasoes, how='left', on='AccountID', suffixes=('', '_evasoes'))
#mov['DateMovement_delta'] = (mov['DateMovement_last'] - mov['DateMovement']).dt.days
mes

def previous_evasion(row):
  if row['Evaded'] == 1 and len(row['Date']) == 1:
    if row['DateMes'] <= row['Date'][0]:
      return 0
  if row['Evaded'] == 1 and len(row['Date']) == 2:
    if row['DateMes'] <= row['Date'][0]:
      return 0
    if row['DateMes'] <= row['Date'][1]:
      return 1
  if row['Evaded'] == 1 and len(row['Date']) == 3:
    if row['DateMes'] <= row['Date'][0]:
      return 0
    if row['DateMes'] <= row['Date'][1]:
      return 1
    if row['DateMes'] <= row['Date'][2]:
      return 2

mes['previous_results'] = mes.apply(previous_evasion, axis=1)
mes

mes['previous_results'].isnull().sum()

#Dropando registros com data de movimentação posterior a evasão
idx = mes[mes['previous_results'].isnull() & mes['Evaded'] == 1].index
mes = mes.drop(index=idx)

"""Os registros após evasões foram removidos, pois os clientes que evadiram e retornaram (estão ativos novamente) ou podem ser reflexos da evasão. Por isso, não faz sentido manter esses dados no modelo."""

#Preenchendo clientes sem evasões com 0
mes['previous_results'].fillna(0, inplace=True)

"""Função 2 - 15 dias"""

last_mes = last_day(mes, 'AccountID', 'previous_results', 'DateMes')
last_mes.head(3)

mes = mes.merge(last_mes, how='right', on=['AccountID', 'previous_results'], suffixes=('', '_last'))
mes['DateMes_delta'] = (mes['DateMes_last'] - mes['DateMes']).dt.days
mes.head(3)

mes = mes[mes['DateMes_delta'] >= 15]
mes

"""### Tabela Orders

Visão geral
"""

dfe_orders.head(3)

"""O grupo de clientes que evadem tem o volume de ordens bem menor, se comparado a clientes ativos.

Além disso, a proporção de compra e venda é bem diferente. Clientes que evadem 'vendem' proporcionalmente bem mais do que clientes que não evadem.

É necessário investigar se esse comportamento ocorre precocemente ou se é apenas um reflexo da decisão de evadir. Ou seja, a maior porporção de vendas(BuySell=S) seria uma causa ou efeito?
"""

dfe_orders['Evaded'] = 1
dfa_orders['Evaded'] = 0

"""Concatenando os dois dataframes"""

ord = concat_info(dfe_orders, dfa_orders)

ord['Date'] = pd.to_datetime(ord['Date'], infer_datetime_format=True)
ord = ord.rename(columns={'Date': 'DateOrders'})

ord.describe()

ord.describe(include='object')

"""Função 1"""

ord = ord.merge(datas_evasoes, how='left', on='AccountID', suffixes=('', '_evasoes'))
#mov['DateMovement_delta'] = (mov['DateMovement_last'] - mov['DateMovement']).dt.days
ord

def previous_evasion(row):
  if row['Evaded'] == 1 and len(row['Date']) == 1:
    if row['DateOrders'] <= row['Date'][0]:
      return 0
  if row['Evaded'] == 1 and len(row['Date']) == 2:
    if row['DateOrders'] <= row['Date'][0]:
      return 0
    if row['DateOrders'] <= row['Date'][1]:
      return 1
  if row['Evaded'] == 1 and len(row['Date']) == 3:
    if row['DateOrders'] <= row['Date'][0]:
      return 0
    if row['DateOrders'] <= row['Date'][1]:
      return 1
    if row['DateOrders'] <= row['Date'][2]:
      return 2

#Rodando a função
ord['previous_results'] = ord.apply(previous_evasion, axis=1)
ord

#Dropando registros com data de movimentação posterior a evasão
idx = ord[ord['previous_results'].isnull() & ord['Evaded'] == 1].index
ord = ord.drop(index=idx)

#Preenchendo clientes sem evasões com 0
ord['previous_results'].fillna(0, inplace=True)

"""Funçao 2"""

last_ord = last_day(ord, 'AccountID', 'previous_results','DateOrders')
last_ord.head()

ord = ord.merge(last_ord, how='right', on=['AccountID', 'previous_results'], suffixes=('', '_last'))
ord['DateOrders_delta'] = (ord['DateOrders_last'] - ord['DateOrders']).dt.days
ord.head()

ord = ord[ord['DateOrders_delta'] >= 15]
ord

"""### Resumo - dimensões

Embora o número de registros nas tabelas 'accounts' seja similar (~18.000) entre os conjuntos de clientes ativos e de evasão, nota-se que para as outras tabelas existem discrepâncias.

Clientes ativos tem


*   ~5 vezes mais registros na tabela month
*   ~2,3 vezes mais registros na tabela movements
*   ~2,2 vezes mais registros na tabela Orders

### Resumo - contagem de IDs únicos

O número de clientes ativos únicos é similar nas diferentes tabelas(~19.000).
Porém, os clientes que realizaram evasão tem uma menor 'participação' na tabela Month e Orders, são aproximadamente 18.000 contas, mas apenas 14.000 possuem dados de posição mensal e apenas 9637 possuem dados de ordens.


Isso pode indicar que parte dos clientes que realizaram evasão nem chegaram a utilizar a conta americana e comprar ativos.

### Resumo - contagem de nulos e tratamentos definidos

Tratamento definido para a tabela Accounts (acc):

*   Function = Tratamento escolhido: preencher com 'OTHER'
*   ('MonthlyIncome', 'NetWorth', 'TotalInvested') =  Tratamento: preencher com Mediana
*    PersonMailingCountry = Exclusão da coluna inteira, todos valores são 'BRA'
*   Evaded = Essa coluna foi adicionada para diferenciação dos grupos.

A tabela Movements também possui nulos, mas em menor proporção(<10):


*   AmountTtotalDol = Tratamento: Drop(linha)

Questões em aberto:


*   Remover coluna com 'HistoricId' ?
*   Remover registros que possuem valores monetário muito baixos (ex: salário= 0.1)?

#3. Data preparation

##Tratamento de nulos
"""

accounts = acc
movements = mov
monthly = mes
orders = ord

accounts.isnull().sum()

movements.isnull().sum()

monthly.isnull().sum()

orders.isnull().sum()

"""###Tabela: Account

Coluna: Function
"""

#acc['Function'].fillna('OTHER', inplace=True)

"""Coluna: PersonMailingCountry"""

# acc.drop('PersonMailingCountry', axis=1, inplace=True)
acc.drop(['PersonMailingCountry', 'Function', 'MonthlyIncome', 'NetWorth', 'TotalInvested'], axis=1, inplace=True)

"""Colunas 'MonthlyIncome', 'NetWorth', 'TotalInvested':"""

#acc[['MonthlyIncome', 'NetWorth', 'TotalInvested']] = acc[['MonthlyIncome', 'NetWorth', 'TotalInvested']].fillna(acc[['MonthlyIncome', 'NetWorth', 'TotalInvested']].median())

"""Resultado - Contagem de Nulos"""

acc.isnull().sum()

"""###Tabela Movement

Coluna: HistoricId
"""

mov.drop(['HistoricId', 'Date'], axis=1, inplace=True)

"""Apenas as colunas 'HistoricID' e 'Date' foram dropadas(nulos ou não agregam ao modelo)

Coluna: AmountTotalDol

Removi as linhas com valores nulos pois eram apenas menos de 10.

Resultado - Contagem de Nulos
"""

mov.isnull().sum()

"""##Busca por dados inconsistentes (valores negativos)"""

acc.select_dtypes('number').min()

mes.select_dtypes('number').min()

mov.select_dtypes('number').min()

ord.select_dtypes('number').min()

dfe_accounts.select_dtypes('number').min()

dfe_monthly.select_dtypes('number').min()

dfe_movement.select_dtypes('number').min()

dfe_movement.select_dtypes('number').min()

"""Obs: Nem todos valores negativos são inconsistentes, depende da natureza/significado da variável.

Avaliar em maiores detalhes e verificar a necessidade de tratar registros com valores muitos baixos. Ex: salário(MonthlyIncome)= $0.01.

##Construct Data

###Tabela Movement (mov)
"""

mov.head(3)

"""Agrupando os dados"""

mov_group = mov.groupby(by=['AccountID', 'previous_results']).agg({'AccountID': 'count',
                                 'DateMovement_delta': 'max',
                                 'AccountType': 'nunique',
                                 'Description': 'nunique',
                                 'AmountTotalDol': ['mean','sum']
}).reset_index()

"""Renomeando as colunas do df agrupado"""

mov_group.columns = ['_'.join(col).strip() if col[1] != "" else col[0] for col in mov_group.columns.values]

"""Resultado parcial"""

mov_group.head(3)

"""###Tabela Accounts(acc)"""

acc.columns

acc.head(3)

"""Criando duas novas colunas com a proporção da renda mensal e do patrimônio investidos no total."""

#acc['PctMonthlyInvested'] = acc['TotalInvested'] / acc['MonthlyIncome'] *100 #Proporção do salário investido em %
#acc['PctNetInvested'] = acc['TotalInvested'] / acc['NetWorth'] *100  #Proporção do patrimônio investido em %

"""Investigando a coluna de estado civil

###Tabela Monthly (mes)
"""

mes.head(3)

mes_group = mes.groupby(by=['AccountID', 'previous_results']).agg({'AccountID': 'count',
                                 'DateMes_delta': 'max',
                                 'ProductCategory': 'nunique',
                                 'Symbol': 'nunique',
                                 'TotalNetDol': ['mean', 'sum']
}).reset_index()

mes_group.columns = ['_'.join(col).strip() if col[1] != "" else col[0] for col in mes_group.columns.values]

mes_group.head()

"""###Tabela Orders (ord)"""

ord.head(3)

ord_group = ord.groupby(by=['AccountID', 'previous_results']).agg({'AccountID': 'count',
                                 'DateOrders_delta': 'max',
                                 'ProductCategory': 'nunique',
                                 'Symbol': 'nunique',
                                 'TotalExecutedVolume': ['mean','sum']
}).reset_index()

ord_group.columns = ['_'.join(col).strip() if col[1] != "" else col[0] for col in ord_group.columns.values]

"""##Integrando as tabelas

Primeiro fiz o merge par a par (tabela accounts e outras), para verificar a correlação de cada tabela com a variável 'Evaded' que estava apenas na tabela accounts.

Depois fiz o Merge de todas 4, são muitas colunas. Recomendo fazermos uma seleção antes da modelagem.

###MERGE ACC & MOV
"""

mov.head()

acc_mov_merge = pd.merge(acc, mov_group, how='left', on='AccountID')

"""Obs: 2 registros da tabela Accounts não constam na tabela Movement. Como são poucos, usei o 'inner' para retornar apenas os registros que constam em ambas e evitar a criação de nulos"""

acc_mov_merge.head()

corr = acc_mov_merge.corr()

cmap = sns.diverging_palette(250, 10, as_cmap=True)

fig = plt.figure(figsize=(20,15))
sns.heatmap(corr, cmap=cmap, annot=True);

"""### MERGE ACC & MOV"""

mes_group.info()

# Excluir essa parte (merge de apenas 2 tabelas)
#acc_mes_merge = pd.merge(acc, mes_group, how='left', on=['AccountID', 'previous_results'])

# corr = acc_mes_merge.corr()

# cmap = sns.diverging_palette(250, 10, as_cmap=True)

# fig = plt.figure(figsize=(20,15))
# sns.heatmap(corr, cmap=cmap, annot=True);

"""###MERGE ACC & ORD"""

acc_ord_merge = pd.merge(acc, ord_group, how='left', on='AccountID')

corr = acc_ord_merge.corr()

cmap = sns.diverging_palette(250, 10, as_cmap=True)

fig = plt.figure(figsize=(20,15))
sns.heatmap(corr, cmap=cmap, annot=True);

"""##MERGE GERAL"""

# df merge com 3 tabelas (accounts, movements, monthly)

acc_mov_mes_merge = pd.merge(acc_mov_merge, mes_group, how='left', on=['AccountID', 'previous_results'])

# df merge com todas tabelas (account, movements, monthly, orders)

df_final_merge = pd.merge(acc_mov_mes_merge, ord_group, how='left', on=['AccountID', 'previous_results'])

corr = df_final_merge.corr()

cmap = sns.diverging_palette(250, 10, as_cmap=True)

fig = plt.figure(figsize=(23,15))
sns.heatmap(corr, cmap=cmap, annot=True);

"""São muitas colunas. No momento rodamos o modelo com todas, mas é interessante selecionar as colunas, criar novos modelos e compará-los.

Depois iremos renomear as colunas, mas é possível entender o significado de cada observando o 'Groupby' de cada tabela.

Basicamente selecionamos algumas colunas de cada tabela e utilizamos as operações: nunique, count e mean.
"""

df_final_merge.info()

"""Após o Merge(Left), alguns registros ficaram com valores nulos pois eles estão presentes na tabela accounts mas não estavam nas tabelas monthly e orders.

Preenchi nulos com 0, depois podemos testar outras abordagens.
"""

#Teste
df_final_merge.head(3)

#teste
acc_mov_merge.head(3)

#teste
#Cria um novo dataframe com o merge da tabela Accounts e Movements + 5 colunas
#das tabelas Monthly e Orders ('AccountID_count_y', 'ProductCategory_nunique_x', 'Symbol_nunique_x', 'AccountID_count', 'Symbol_nunique_y')
df_modelo = pd.merge(acc_mov_merge, df_final_merge[['AccountID', 'previous_results', 'AccountID_count_y', 'ProductCategory_nunique_x', 'Symbol_nunique_x', 'AccountID_count', 'Symbol_nunique_y', 'DateOrders_delta_max' ]], how='left', on=['AccountID', 'previous_results'])

df_modelo.head(3)

#teste
df_modelo.info()

df_modelo = df_modelo.drop(columns=['AccountID','PersonMailingState', 'AmountTotalDol_mean', 'AmountTotalDol_sum'])

#teste
df_modelo = df_modelo.fillna(0)

df_modelo = pd.get_dummies(df_modelo, columns=['SubscriptionPlan', 'MaritalStatus'], drop_first=True)
df_modelo.head()

"""Essas são as variáveis utilizadas no modelo e suas correlações com o alvo (EVADED)"""

corr = df_modelo.corr()

cmap = sns.diverging_palette(250, 10, as_cmap=True)

fig = plt.figure(figsize=(16,10))
sns.heatmap(corr, cmap=cmap, annot=True);

"""#4.Modelling

Pré-processamento
"""

df_modelo.head()

df_modelo.shape

"""Removendo colunas com datas e dados textuais."""

#teste
x = df_modelo.drop(columns=['Evaded'])

y = df_modelo['Evaded']

# x = df_final_merge.drop(columns=['Evaded', 'AccountID', 'Function', 'PersonMailingState', 'DateMovement_min',
#                                  'DateMovement_max', 'DateMes_min', 'DateMes_max', 'DateOrders_min', 'DateOrders_max'])

# y = df_final_merge['Evaded']

"""Importando as bibliotecas de modelagem + divisão treino/teste"""

from sklearn.metrics import accuracy_score, f1_score, roc_auc_score, plot_confusion_matrix
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.3, random_state=123)

"""Árvore de decisão"""

treed = DecisionTreeClassifier(random_state=123).fit(x_train, y_train)
y_tree = treed.predict(x_test)
print(f"Acurácia: {accuracy_score(y_test, y_tree)}")
print(f"F1 Score: {f1_score(y_test,y_tree)}")
print(f"ROC AUC: {roc_auc_score(y_test,y_tree)}")

"""Floresta aleatória"""

from sklearn.ensemble import RandomForestClassifier

rand = RandomForestClassifier().fit(x_train, y_train)

y_rand = rand.predict(x_test)

print(f"Acurácia: {accuracy_score(y_test, y_rand)}")
print(f"F1 Score: {f1_score(y_test,y_rand)}")
print(f"ROC AUC: {roc_auc_score(y_test,y_rand)}")

plot_confusion_matrix(rand, x_test, y_test);

"""##Prevendo as probabilidades

O código da etapa anterior prevê a classe, para prever a probabilidade de classes utilizar "rand.predict_proba(x_test)"

Probabilidades de classes
"""

y_probs = rand.predict_proba(x_test)
y_probs

probabilidades = rand.predict_proba(x)
df_results = pd.DataFrame(probabilidades, columns=['prob_ativo', 'prob_churn'])
df_results['Evaded'] = y
df_results

"""##7. Exportando as tabelas"""

# #merge: accounts + mov_group
df_modelo.to_csv('df_final_merge.csv')

"""## 8.Shap"""

import shap

"""2 novos objetos foram criados: explainer e shap_values"""

explainer = shap.TreeExplainer(treed)
shap_values = explainer.shap_values(x_train, y_train)
expected_value = explainer.expected_value

shap_values

"""Foi utilizado xtrain porque é a variável utilizada pra criar o modelo. Portanto o objetivo é entender os padrões desse modelo e as relações que ele está capturando.
**expected_value** é a previsão média
"""

shap_values[1].shape

shap.initjs()
shap.force_plot(explainer.expected_value[1], shap_values[1][1,:],x_train.iloc[1,:])

"""**Sobre o gráfico acima:**
Probablidade de 0,85
Nos mostra o quanto cada feature contribuiu para essa probabilidade passar do valor base de 0,484 para 0,85.
***???AccountID_count_y ser o de maior expressão.***
"""

shap.initjs()
shap.force_plot(explainer.expected_value[1], shap_values[1][0,:],x_train.iloc[0,:])

#shap.force_plot(explainer.expected_value[1], shap_values[1], x_train)
#Esse gráfico não ta rodando aqui, está dizendo que a RAM não é suficiente, se alguém conseguir colocar ele mostra para nossos exemplos as previsões e mostrar por similaridades entre as features.

import xgboost

"""**summary_plot**
Mostra quais as features mais importantes.
Shap_values = o impacto na previsão do modelo. Pelo gráfico abaixo parece que todas impactam de forma parecida no modelo.
**???**Os dados do lado direito do eixo central mostra o quanto cada uma impacta na probabilidade de um cliente se tornar churn e no lado esquerno quanto diminui essa probabilidade.
**???** O fato de ter o acumulo de dados no centro quer dizer que o modelo não sabe pra qual lado escolher?
"""

shap.summary_plot(shap_values[1],  x_train, plot_type="dot", plot_size=(20,15))

x.columns ['AccountID_count_y', 'DateMovement_delta_max', 'DateOrders_delta_max', 'ProductCategory_nunique_x',
           'Age', 'AccountID_count_x', 'Symbol_nunique_y', 'Description_nunique', 'AccountID_count_y']

# Contribução de Importância das variáveis
shap.summary_plot(shap_values[1], x_train, plot_type="bar", plot_size=(20,15));

#Impacto das variáveis em uma predição específica do modelo versão Waterfall Plot
shap.plots._waterfall.waterfall_legacy(expected_value=expected_value[1], shap_values=shap_values[1][3].reshape(-1), feature_names=x_train.columns, show=True)

# Impacto das variáveis em uma predição específica do modelo versão Line Plot
shap.decision_plot(base_value=expected_value[1], shap_values=shap_values[1][3], features=x_train.iloc[3,:],highlight=0)

"""Os gráficos abaixo podem ser análisados 1 para cada feature.
Quanto maior os dados do eixo y maior a probabilidade de ser da classe 1.
"""

shap.dependence_plot("AccountID_count_y",shap_values[1], x_train, interaction_index = None)
#interaction_index = None foi usado para que o gráfico não colocasse 3 variáveis

shap.dependence_plot("Age",shap_values[1], x_train, interaction_index = None)

"""Esse gráfico da idade mostra sutilmente que quanto mais novo maior a probabilidade de se tornar churn. Mas os dados estão tão espalhados que é muito sútil essa interpretação, não parece muito definido essa informaçãp."""