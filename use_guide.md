
# Guia de Uso: Analisador de Tickets de Suporte

Este guia detalha todas as funcionalidades do Analisador de Tickets de Suporte, incluindo configuração inicial, uso diário e solução de problemas comuns.

## Resumo

### Primeiros Passos
- Configuração do Token API
- Configuração de Horário Comercial
- Gestão de Feriados

### Funcionamento Básico
- Busca de Tickets de Suporte
- Análise de Tickets
- Visualização de Resultados

### Recursos Avançados
- Classificação Manual de Interações
- Calculadora de Tempo
- Exportação de Dados (csv)

### Conceitos Importantes
- Lógica de Cálculo de Tempo
- Classificação de Interações
- Tempo Comercial x Tempo Total

### Solução de Problemas
- Erros Comuns
- Limites da API
- Perguntas Frequentes

---

## Primeiros Passos

### Configuração do Token API

1. Abra o painel de configurações clicando no ícone ⚙️, posicionado no canto superior direito (ou em "Configurações no canto inferior direito").
2. Na seção "API Token", cole seu token de acesso.
3. Clique em **Salvar**.

> **Nota:** Para obter o token da API do TomTicket, acesse: Configurações > API > Gerar Token (https://tomticket.tomticket.com/kb/introducao/criacao-do-token-de-acesso).

### Configuração de Horário Comercial

1. No painel de configurações, clique em **Horários**.
2. Configure os horários comerciais por dia da semana.
3. É possível adicionar múltiplos intervalos por dia (ex: 08:00-12:00 e 14:00-18:00).
4. Deixe em branco os dias não úteis.
5. Clique em **Salvar**.

**Exemplo padrão:**
- Segunda a Sexta: 08h00-12h00, 14h00-18h00
- Sábado e Domingo: Sem horário comercial

### Gestão de Feriados

1. Vá em **Feriados** no painel de configurações.
2. Para adicionar um feriado:
   - Selecione a data no calendário
   - Insira uma descrição
   - Clique em **Adicionar Feriado**
3. Para excluir, clique em **Excluir** ao lado do item.
4. Clique em **Importar Feriados Nacionais** para carregar feriados automaticamente.

**Nota:** É de estrema importância o cadastro correto de feriados, pois serão utilizados nos cálculos dos tempos que consideram dias e horários comercias. O uso incorreto poderá ocasionar divergências!

---

## Funcionamento Básico

### Busca de Tickets

1. Na aba **Filtros de Pesquisa**, defina:
   - Período
   - Situação
   - Prioridade
   - Categoria

   **Dica:** Nno filtre 'Período', a data final deve ser inferior a data atual.

2. Clique em **Pesquisar Tickets**.

> **Dica:** Use períodos curtos para resultados mais rápidos (limite da API: 50 tickets por consulta).

### Análise de Tickets

1. Na aba **Resultados**, selecione os tickets desejados.
2. Clique em **Analisar Selecionados**.
3. Escolha entre:
   - **Ver Resumo**
   - **Classificar Interações**

### Visualização de Resultados

Inclui:
- Tempo total e comercial (cliente e suporte)
- Tempo em status
- Tempo até primeiro status

Passe o mouse sobre os valores para detalhes.

---

## Recursos Avançados

### Classificação Manual de Interações

1. Após análise, clique em **Classificar Interações**.
2. Selecione o ticket.
3. Navegue pelas interações.
4. Para reclassificar:
   - `C`: Cliente
   - `A`: Suporte
   - `B`: Bug
   - `I`: Ignorar
5. Marque como **Analisado** e clique em **Aplicar Alterações**.

> Importante: A classificação afeta os cálculos. Veja *Lógica de Cálculo de Tempo*.
> Importante: Após a classificação e a aplicação das alterações clicando em **Aplicar Alterações**, a tela de Resumo será aberta. Nesse momento, os dados poderão ser exportados. Se essa tela for fechada, as classificaçõe serão perdidas e deverão ser refeitas, ou seja, **o sistema não grava os resultados nem armazena as alterações!** 

### Calculadora de Tempo (utilitário)

1. Clique em **Calculadora de Tempos/Período**.
2. Insira datas e horários (AAAA-MM-DD HH:MM).
3. Clique em **Calcular**.

Resultados:
- Diferença total
- Tempo em horário comercial

Você pode acumular múltiplos cálculos.

### Exportação de Dados

1. Clique em **Exportar para CSV** na tela de resultados.
2. Escolha o local de salvamento.

Inclui:
- Resumo da análise
- Intervalos entre interações
- Lista de interações

> Importante: Também é possível exportar um ticket individual na tela de **Classificar Interações**. Nessa tela, a exportação é individual por ticket selecionado, e o arquivo exportado terá todas as informações de classificação, datas, descrição, alterações, tempos, etc.
> **Dica:** Use esse esportação para manter um backup do registro das classificações dos tickets, para consultas futuras, auditoria e etc.

---

## Conceitos Importantes

### Lógica de Cálculo de Tempo

- O tempo entre interações é atribuído a quem tinha o ticket no início.
  
**Exemplo:**
- 10:00 Cliente cria (`C`)
- 11:00 Suporte responde (`A`)
- 14:00 Cliente responde (`C`)

**Atribuição:**
- 10:00–11:00: Suporte
- 11:00–14:00: Cliente

**Classificações Especiais:**
- `B`: Bug
- `I`: Ignorar

### Classificação de Interações

Tipos:
- `C`: Cliente
- `A`: Suporte
- `B`: Bug
- `I`: Ignorar

A classificação automática pode ser ajustada manualmente.

### Tempo Comercial x Tempo Total

- **Tempo Total**: todo o tempo entre interações
- **Tempo Comercial**: apenas o tempo em horário comercial

Tempo comercial exclui:
- Fora do expediente
- Finais de semana
- Feriados

---

## Solução de Problemas

### Erros Comuns

**Token inválido**
- Verifique o token inserido
- Gere um novo token se necessário

**Parâmetros inválidos**
- Verifique formatos e filtros

**Sem resultados**
- Verifique se há tickets disponíveis
- Tente com apenas um ticket

### Limites da API

- Máx. 50 tickets por consulta
- Máx. 100 requisições por minuto
- Timeout após 30s

> O sistema tenta automaticamente novas tentativas ao atingir limites.

### Perguntas Frequentes

**P: Por que os tempos calculados são diferentes do TomTicket?**  
R: O app usa lógica de posse e horário comercial.

**P: É possível analisar dados antigos?**  
R: Sim, se acessíveis pela API.

**P: Como resolver o erro de limite de requisições?**  
R: Reduza a quantidade de tickets analisados por vez.

**P: Os dados são salvos localmente?**  
R: Apenas configurações; os resultados **precisam ser exportados** para manter um backup local.

**P: Como recalcular após reclassificar?**  
R: Clique em **Recalcular Tempos** após ajustes. 

**P: Na tela de Classificação dos Tickets, como identificar as alterações feitas até o momento, no ticket selecionado?**  
R: Clique na aba **Lista de Interações** e verifique na na lista as colunas `Tipo Original` e `Classificação Atual`. Nessas colunas, quando uma alteração for feita, estaão com valores diferentes e destaca em amarelo. 

**P: Na tela de Classificação dos Tickets, como posso voltar um ticket para o status orignal, desfazendo as alterções de classificação?**  
R: Clique na aba **Lista de Interações** e verifique na na lista as colunas `Tipo Original` e `Classificação Atual`. Essas colunas irão indicar as alterações feitas até o momento, marcando a coluna `Classificação Atual` em amarelo. Para desfazer as alterações, clique no botão `Resetar para Original`. Essa ação afeta apenas o ticket selecionado. 

**P: Na tela de Classificação dos Tickets, como posso verificar os tempos calculados para o cliente, suporte, etc?**  
R: Na parte inferior da tela de **Classificação de Interações** é exibido uma sessão `Comparação de Métricas de Tempos`. A sessão exibe dinamicamente os cáclulos separados por Cliente, Suporte, Bug e Ignorado, conabilizadas por Tempo Comercial e Tempo Normal. A coluna `Orignal` exibe o cálculo automático inicial (se mantem estática). Já a coluna `Após Reclassificação`, é atualizada a cada alteração de classificação (inicialmente carregado igualmente com os valores da coluna Original). A coluna `Diferençã` exibe as diferêncas a cada alteração de classificação (positiva ou negativa). A coluna `Preview` exibe o resultado final após as alterações (gerlamente igual a coluna Após Reclassificação).

---

Para mais informações ou suporte, entre em contato com o desenvolvedor [thiago.paraizo@scalait.com](mailto:thiago.paraizo@scalait.com).
