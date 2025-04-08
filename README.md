
# Analisador de Tickets de Suporte

## Sobre o Projeto

O **Analisador de Tickets de Suporte** é uma ferramenta desktop desenvolvida para análise de métricas de tempo e interações em tickets de suporte. Integrada com a API do TomTicket, esta aplicação permite:

- Buscar tickets por diferentes critérios (datas, protocolo, prioridade)
- Analisar tempo de resposta e tempo de resolução
- Calcular tempo gasto com cliente vs. tempo gasto com suporte
- Calcular tempo em horário comercial, excluindo finais de semana e feriados
- Classificar e reclassificar interações para análises personalizadas
- Exportar resultados para CSV

Esta aplicação é ideal para equipes de suporte técnico que desejam realizar análises de atendimento, identificar gargalos e otimizar processos de atendimento ao cliente.

## Recursos Principais

- **Análise de Tempo**: Cálculo detalhado de tempo total e tempo em horário comercial para cada ticket.
- **Visualização de Interações**: Visualização das interações do ticket em formato de linha do tempo.
- **Reclassificação**: Possibilidade de reclassificar interações para cálculos personalizados.
- **Filtros Avançados**: Busca por datas, protocolo, cliente, prioridade e muito mais.
- **Horário Comercial Configurável**: Define horários de trabalho para cada dia da semana.
- **Gestão de Feriados**: Cadastro e importação de feriados para exclusão de cálculos.
- **Calculadora de Tempo**: Ferramenta para cálculos rápidos de intervalos de tempo.
- **Exportação em CSV**: Exportação completa das análises para uso em outros sistemas.

## Requisitos

- Python 3.8 ou superior
- PyQt5 5.15 ou superior
- Pandas 2.0 ou superior
- Requests 2.30 ou superior
- Dateutil (versão compatível com Python)

## Instalação

### Usando o Executável

Para usuários do Windows, disponibilizamos um executável que não requer instalação do Python ou dependências:

1. Baixe o arquivo `TicketAnalyzer.exe` na área de releases
2. Execute o arquivo diretamente — não é necessária instalação

### Instalação para Desenvolvedores

Para desenvolvedores ou usuários que desejam executar a partir do código-fonte:

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/ticket-analyzer.git
cd ticket-analyzer
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Execute a aplicação:
```bash
python ticket_analyzer.py
```

## Configuração

Ao iniciar o aplicativo pela primeira vez, você precisará:

- Configurar o token da API do TomTicket
- Definir os horários comerciais para cada dia da semana
- Configurar feriados (opcional)

Para mais detalhes, consulte o **Guia de Uso**.

## Créditos

Desenvolvido por **Scala Stefanini - Thiago Paraizo** para análise de tickets do sistema TomTicket.
Para mais informações ou suporte, entre em contato com o desenvolvedor [thiago.paraizo@scalait.com](mailto:thiago.paraizo@scalait.com).

## Licença

Este projeto está licenciado sob a **Licença MIT**.
