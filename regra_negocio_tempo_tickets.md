
# Documentação de Regra de Negócio: Cálculo de Tempo com Cliente e Suporte

## Visão Geral

Os cálculos de **"Tempo com Cliente"**, **"Tempo com Suporte"**, **"Tempo Comercial com Cliente"** e **"Tempo Comercial com Suporte"** são baseados na análise das interações (replies) no ticket. Essas métricas mostram quanto tempo o ticket passou **com o cliente** versus **com a equipe de suporte**, considerando tanto o tempo total quanto apenas o tempo em horário comercial.

## Método de Cálculo

### Lógica Fundamental

- A premissa básica é que o remetente atual determina com quem o ticket está agora.
- O tempo entre duas interações é atribuído à parte que tinha o ticket no início desse período.

### Passo a Passo

1. **Ordenação das Interações**  
   Todas as interações (replies) são ordenadas cronologicamente por data.

2. **Estado Inicial**
   - Assumimos que o ticket começa *com o cliente* (após a criação do ticket).
   - Definimos a data de criação do ticket como ponto de partida (`last_dt = creation_dt`).
   - Definimos o último remetente como `'C'` (cliente) (`last_sender = 'C'`).

3. **Para cada interação sequencial:**
   - Obtemos a data da interação atual (`current_dt`).
   - Identificamos o tipo de remetente:
     - `'C'` para cliente
     - `'A'` para atendente/suporte
     - `'B'` para bug (problema técnico)
     - `'I'` para ignorado (não entra nos cálculos principais)
   - Calculamos o tempo total entre a interação anterior e a atual: `time_diff = current_dt - last_dt`
   - Calculamos o tempo em horário comercial entre essas datas: `business_time = calculator.calculate_business_time(last_dt, current_dt)`

4. **Atribuição do Tempo:**
   - Se o último remetente foi `'C'` (cliente):
     - O tempo foi gasto **com o suporte**.
     - Adiciona-se `time_diff` a `time_with_support` e `business_time` a `business_time_with_support`.
   - Se o último remetente foi `'A'` (atendente):
     - O tempo foi gasto **com o cliente**.
     - Adiciona-se `time_diff` a `time_with_client` e `business_time` a `business_time_with_client`.
   - Se o último remetente foi `'B'` (bug):
     - O tempo é classificado como **tempo com bug**.
   - Se o último remetente foi `'I'` (ignorado):
     - O tempo **não é contabilizado** nas métricas principais.

5. **Atualização para próxima iteração:**
   - Atualiza-se `last_dt` para `current_dt`.
   - Atualiza-se `last_sender` para o remetente atual.

## Exemplo Prático

Para um ticket com as seguintes interações:

- Criação do ticket pelo cliente (`C`) em **10/04/2023 às 09:00**
- Primeira resposta do atendente (`A`) em **10/04/2023 às 11:00**
- Resposta do cliente (`C`) em **11/04/2023 às 14:00**
- Resposta final do atendente (`A`) em **11/04/2023 às 16:00**

### Cálculo

- Entre 09:00 e 11:00 (2h): Tempo **com Suporte** (último remetente era 'C')
- Entre 11:00 e 14:00 (3h): Tempo **com Cliente** (último remetente era 'A')
- Entre 14:00 e 16:00 (2h): Tempo **com Suporte** (último remetente era 'C')

### Resultado Final

- **Tempo com Cliente:** 3h (total)
- **Tempo com Suporte:** 4h (total)

> Para o cálculo de *Tempo Comercial*, aplica-se a mesma lógica, mas considerando apenas as horas que caem dentro do horário comercial definido e excluindo feriados.

## Diferença para os Cálculos de Status

É importante notar que este cálculo **difere** do cálculo de **"Tempo em Status"**, que mede o tempo gasto em cada status do ticket (como "Em andamento", "Pausado", etc.).  
Enquanto o tempo em status mostra em que etapa o ticket está, o cálculo de tempo com cliente/suporte mostra **quem estava atuando sobre o ticket**.

---
