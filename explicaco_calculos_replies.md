Explicação dos Cálculos de Tempo com Cliente e Suporte
Visão Geral
Os cálculos de "Time with Client", "Time with Support", "Business Time with Client" e "Business Time with Support" são baseados na análise das interações (replies) no ticket. Essas métricas mostram quanto tempo o ticket passou "com o cliente" versus "com a equipe de suporte", considerando tanto o tempo total quanto apenas o tempo em horário comercial.
Método de Cálculo
Lógica Fundamental

A premissa básica é que o remetente atual determina com quem o ticket está agora
O tempo entre duas interações é atribuído à parte que tinha o ticket no início desse período

Passo a Passo

Ordenação das Interações:

Todas as interações (replies) são ordenadas cronologicamente por data


Estado Inicial:

Assumimos que o ticket começa "com o cliente" (após a criação do ticket)
Definimos a data de criação do ticket como ponto de partida (last_dt = creation_dt)
Definimos o último remetente como 'C' (cliente) (last_sender = 'C')


Para cada interação sequencial:

Obtemos a data da interação atual (current_dt)
Identificamos o tipo de remetente ('C' para cliente ou 'A' para atendente/suporte)
Calculamos o tempo total entre a interação anterior e a atual: time_diff = (current_dt - last_dt)
Calculamos o tempo em horário comercial entre essas datas: business_time = calculator.calculate_business_time(last_dt, current_dt)


Atribuição do Tempo:

Se o último remetente foi 'C' (cliente):

O tempo foi gasto "com o suporte" (o suporte estava trabalhando no ticket)
Adicionamos o tempo a time_with_support e business_time_with_support


Se o último remetente foi 'A' (atendente):

O tempo foi gasto "com o cliente" (o cliente estava analisando ou respondendo)
Adicionamos o tempo a time_with_client e business_time_with_client




Atualização para próxima iteração:

Atualizamos a última data para a data atual (last_dt = current_dt)
Atualizamos o último remetente para o remetente atual (last_sender = sender_type)



Exemplo Prático
Para um ticket com as seguintes interações:

Criação do ticket pelo cliente (C) em 10/04/2023 às 09:00
Primeira resposta do atendente (A) em 10/04/2023 às 11:00
Resposta do cliente (C) em 11/04/2023 às 14:00
Resposta final do atendente (A) em 11/04/2023 às 16:00

O cálculo seria:

Entre 09:00 e 11:00 (2h): Tempo com Suporte (último remetente era 'C')
Entre 11:00 e 14:00 (3h): Tempo com Cliente (último remetente era 'A')
Entre 14:00 e 16:00 (2h): Tempo com Suporte (último remetente era 'C')

Resultando em:

Time with Client: 3h (total)
Time with Support: 4h (total)

Para o cálculo de "Business Time", é aplicada a mesma lógica, mas considerando apenas as horas que caem dentro do horário comercial definido e excluindo feriados.
Diferença para os Cálculos de Status
É importante notar que este cálculo difere do "Time in Status", que mede o tempo gasto em cada status (como "Em andamento", "Pausado", etc.). O cálculo de tempo com cliente/suporte se concentra em quem está atuando no ticket, enquanto os status mostram em que etapa do processo o ticket se encontra.