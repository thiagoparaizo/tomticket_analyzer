import csv
import datetime
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit, 
                            QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                            QCheckBox, QMessageBox, QGroupBox, QFormLayout, QSpinBox,
                            QTimeEdit, QDialog, QScrollArea, QFileDialog, QGridLayout, QTextEdit, QSplitter, QFrame )
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QSize
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QIcon


class InteractionPairTableView(QTableWidget):
    """Tabela personalizada que mostra pares de interações consecutivas com o tempo entre elas"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.current_ticket = None
        
    def initUI(self):
        # Configurar tabela
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            "Intervalo", "Remetente", "De (Data/Hora)", "Para (Data/Hora)", 
            "Tempo Decorrido", "Tempo Comercial", "Atribuído a", 
            "Reclassificar", "Detalhes"
        ])
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(7, QHeaderView.Fixed)
        self.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        
        # Tamanhos específicos
        self.setColumnWidth(0, 80)  # Intervalo
        self.setColumnWidth(7, 420)  # Reclassificar
        self.setColumnWidth(8, 80)  # Detalhes
        
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        
    def load_ticket_data(self, ticket_data, calculator):
        """Carrega dados do ticket na tabela de pares de interações"""
        self.current_ticket = ticket_data
        self.calculator = calculator
        
        if not ticket_data or 'interactions' not in ticket_data:
            return
            
        interactions = [i for i in ticket_data['interactions'] if i.get('date')]
        # Ordena por data
        interactions.sort(key=lambda x: x['date'])
        
        # Resetar tabela
        self.setRowCount(0)
        
        if not interactions:
            return

        # Determinar a data final para cálculos (data atual ou de fechamento do ticket)
        is_finished = False
        end_date = self._get_end_date_for_calculations(interactions)

        # Verifica end_date do ticket
        if ticket_data.get('end_date'):
            try:
                is_finished = True
            except:
                pass
        
        # Verifica situation do ticket
        situation_id = ticket_data.get('situation', {}).get('id')
        if situation_id in [4, 5]:  # Cancelada ou Finalizada
            is_finished = True
            try:
                situation_date = self.parse_datetime(ticket_data.get('situation', {}).get('apply_date'))
                if situation_date:
                    end_date = situation_date
            except:
                pass
        
        # Criar linhas para cada par de interações incluindo o último
        for i in range(len(interactions)):
            from_interaction = interactions[i]
            
            if i < len(interactions) - 1:
                # Intervalo entre duas interações
                to_interaction = interactions[i+1]
                time_diff = (to_interaction['date'] - from_interaction['date']).total_seconds()
                business_time = calculator.calculate_business_time(from_interaction['date'], to_interaction['date'])
            else:
                # Último intervalo - da última interação até end_date
                to_interaction = {'date': end_date, 'sender': 'Sistema', 'sender_type': 'S', 
                                'message': 'Final do ticket' if is_finished else 'Estado atual'}
                time_diff = (end_date - from_interaction['date']).total_seconds()
                business_time = calculator.calculate_business_time(from_interaction['date'], end_date)
            
            # Determinar a quem este tempo é atribuído
            current_classification = from_interaction.get('classification', from_interaction.get('sender_type', ''))
            
            if current_classification == 'C':
                attributed_to = "Suporte"
                attribution_color = QColor(125, 131, 221)  # Verde claro
            elif current_classification == 'A':
                attributed_to = "Cliente"
                attribution_color = QColor(52, 237, 140)  # Azul claro
            elif current_classification == 'B':
                attributed_to = "Bug"
                attribution_color = QColor(255, 235, 162)  # Vermelho claro
            elif current_classification == 'I':
                attributed_to = "Ignorado"
                attribution_color = QColor(192, 192, 192)   # Cinza claro
            else:
                attributed_to = "Desconhecido"
                attribution_color = QColor(255, 255, 255)  # Branco
                
            # Tipo Original (De) - Expandido ao invés de abreviado
            from_type = from_interaction.get('sender_type', '')
            if from_type == 'C':
                displayed_type = "Cliente"
            elif from_type == 'A':
                displayed_type = "Atendente"
            elif from_type == 'B':
                displayed_type = "Bug"
            elif from_type == 'I':
                displayed_type = "Ignorado"
            else:
                displayed_type = "Desconhecido"
            
            # Adicionar linha
            row = self.rowCount()
            self.insertRow(row)
            
            # Intervalo
            interval_item = QTableWidgetItem(f"#{i+1}")
            interval_item.setTextAlignment(Qt.AlignCenter)
            interval_item.setData(Qt.UserRole, (i, i+1 if i < len(interactions) - 1 else -1))  # Índices das interações
            self.setItem(row, 0, interval_item)
            
            # Remetente (De)
            sender_item_str = f"{from_interaction.get('sender', '')} ({displayed_type.upper()})"
            from_sender_item = QTableWidgetItem(sender_item_str)
            from_sender_item.setToolTip(f"Tipo: {current_classification}")
            self.setItem(row, 1, from_sender_item)
            
            # De (Data/Hora)
            from_date_item = QTableWidgetItem(from_interaction['date'].strftime("%Y-%m-%d %H:%M:%S"))
            from_date_item.setToolTip(f"Remetente: {from_interaction.get('sender', '')}\nTipo: {from_interaction.get('sender_type', '')}")
            self.setItem(row, 2, from_date_item)
            
            # Para (Data/Hora)
            to_date_str = to_interaction['date'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(to_interaction['date'], datetime.datetime) else str(to_interaction['date'])
            to_date_item = QTableWidgetItem(to_date_str)
            to_tip = f"Remetente: {to_interaction.get('sender', '')}"
            if i == len(interactions) - 1:
                to_tip += f"\nÚltimo intervalo ({('Final do ticket' if is_finished else 'Estado atual')})"
            self.setItem(row, 3, to_date_item)
            to_date_item.setToolTip(to_tip)
            
            # Tempo Decorrido
            time_diff_str = self.format_time(time_diff)
            time_diff_item = QTableWidgetItem(time_diff_str)
            time_diff_item.setToolTip(f"{time_diff/3600:.2f} horas")
            self.setItem(row, 4, time_diff_item)
            
            # Tempo Comercial
            business_time_str = self.format_time(business_time)
            business_time_item = QTableWidgetItem(business_time_str)
            business_time_item.setToolTip(f"{business_time/3600:.2f} horas comerciais")
            self.setItem(row, 5, business_time_item)
            
            # Atribuído a
            attributed_item = QTableWidgetItem(attributed_to)
            attributed_item.setBackground(attribution_color)
            attributed_item.setTextAlignment(Qt.AlignCenter)
            attributed_item.setToolTip(f"Baseado na classificação: {current_classification}")
            self.setItem(row, 6, attributed_item)
            
            # Colorir a linha inteira baseado na atribuição
            for col in range(self.columnCount()):
                if self.item(row, col):
                    self.item(row, col).setBackground(attribution_color)
        
        # Adicionar widgets para as colunas de ação
        self._add_action_widgets()
    
    def _get_end_date_for_calculations(self, interactions):
        """Determina a data final apropriada para cálculos"""
        # Verifica se há data de fechamento no ticket
        if hasattr(self, 'current_ticket') and self.current_ticket:
            if self.current_ticket.get('end_date'):
                try:
                    return datetime.datetime.strptime(self.current_ticket['end_date'], "%Y-%m-%d %H:%M:%S") 
                except:
                    pass
        
        # Se não houver data de fechamento, usa a data atual
        return datetime.datetime.now()
       
    def parse_datetime(self, datetime_str):
        """Analisa string de datetime da API"""
        if not datetime_str:
            return None
        try:
            if '-03:00' in datetime_str:
                dt_str = datetime_str.split('-03:00')[0].strip()
            elif '-0300' in datetime_str:
                dt_str = datetime_str.split('-0300')[0].strip()
            else:
                dt_str = datetime_str
            return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        
    def _add_action_widgets(self):
        """Adiciona widgets de ação (botões) para cada linha da tabela"""
        for row in range(self.rowCount()):
            # Obter índices das interações
            interval_indices = self.item(row, 0).data(Qt.UserRole)
            
            # Criar widget para reclassificação
            reclass_widget = QWidget()
            reclass_layout = QHBoxLayout(reclass_widget)
            reclass_layout.setContentsMargins(2, 2, 2, 2)
            reclass_layout.setSpacing(2)
            
            # Botões para reclassificação
            btn_client = QPushButton("SUPORTE")
            btn_client.setStyleSheet("background-color:rgb(125, 131, 221)")
            btn_client.setToolTip("Atribuir tempo ao Suporte")
            btn_client.setFixedWidth(100)
            btn_client.clicked.connect(lambda _, r=row, t='C': self.reclassify_interval(r, t))
            
            btn_agent = QPushButton("CLIENTE")
            btn_agent.setStyleSheet("background-color:rgb(52, 237, 140)")
            btn_agent.setToolTip("Atribuir tempo ao Cliente")
            btn_agent.setMaximumWidth(100)
            btn_agent.clicked.connect(lambda _, r=row, t='A': self.reclassify_interval(r, t))
            
            btn_bug = QPushButton("BUG")
            btn_bug.setStyleSheet("background-color:rgb(255, 235, 162)")
            btn_bug.setToolTip("Classificar como Bug")
            btn_bug.setMaximumWidth(100)
            btn_bug.clicked.connect(lambda _, r=row, t='B': self.reclassify_interval(r, t))
            
            btn_ignore = QPushButton("IGNORAR")
            btn_ignore.setStyleSheet("background-color:rgb(192, 192, 192)")
            btn_ignore.setToolTip("Classificar como Ignorado")
            btn_ignore.setMaximumWidth(100)
            btn_ignore.clicked.connect(lambda _, r=row, t='I': self.reclassify_interval(r, t))
            
            # Adicionar botões ao layout
            reclass_layout.addWidget(btn_client)
            reclass_layout.addWidget(btn_agent)
            reclass_layout.addWidget(btn_bug)
            reclass_layout.addWidget(btn_ignore)
            
            self.setCellWidget(row, 7, reclass_widget)
            
            # Criar widget para detalhes
            details_widget = QWidget()
            details_layout = QHBoxLayout(details_widget)
            details_layout.setContentsMargins(2, 2, 2, 2)
            
            # Botão para detalhes
            btn_details = QPushButton("Detalhes")
            btn_details.clicked.connect(lambda _, r=row: self.show_interval_details(r))
            details_layout.addWidget(btn_details)
            
            self.setCellWidget(row, 8, details_widget)
            
            # Colorir a linha inteira baseado na atribuição
            attribution = self.item(row, 6).text()
            if attribution == "Cliente":
                color = QColor(52, 237, 140)  # Azul claro
            elif attribution == "Suporte":
                color = QColor(125, 131, 221)  # Verde claro
            elif attribution == "Bug":
                color = QColor(255, 235, 162)  # Vermelho claro
            elif attribution == "Ignorado":
                color = QColor(192, 192, 192)   # Cinza claro
            else:
                color = QColor(255, 255, 255)  # Branco

            # Aplica a cor a todas as células da linha
            for col in range(self.columnCount()):
                if self.item(row, col):
                    self.item(row, col).setBackground(color)
    
    # Na classe InteractionPairTableView:

    def reclassify_interval(self, row, new_classification):
        """Reclassifica uma interação com base na linha da tabela"""
        if not self.current_ticket:
            return
        
        # Obter índices das interações
        interval_indices = self.item(row, 0).data(Qt.UserRole)
        if not interval_indices or len(interval_indices) != 2:
            return
        
        from_idx = interval_indices[0]
        
        # Atualizar a classificação da interação "De"
        interactions = self.current_ticket.get('interactions', [])
        if 0 <= from_idx < len(interactions):
            interactions[from_idx]['classification'] = new_classification
            
            # Atualizar a visualização
            if new_classification == 'C':
                attributed_to = "Suporte"
                attribution_color = QColor(125, 131, 221)
            elif new_classification == 'A':
                attributed_to = "Cliente"
                attribution_color = QColor(52, 237, 140)
            elif new_classification == 'B':
                attributed_to = "Bug"
                attribution_color = QColor(255, 230, 230)
            elif new_classification == 'I':
                attributed_to = "Ignorado"
                attribution_color = QColor(192, 192, 192) 
            else:
                attributed_to = "Desconhecido"
                attribution_color = QColor(255, 255, 255)
            
            # Atualizar item na tabela
            attributed_item = self.item(row, 6)
            attributed_item.setText(attributed_to)
            attributed_item.setBackground(attribution_color)
            attributed_item.setToolTip(f"Baseado na classificação: {new_classification}")
            
            # Emitir sinal de que houve alteração
            # Modificação aqui: Procurar o diálogo correto
            dialog = None
            parent = self.parent()
            
            # Percorre a hierarquia de widgets até encontrar InteractionClassifierDialogUpdated
            while parent:
                if isinstance(parent, QDialog):  # ou verificar especificamente para InteractionClassifierDialogUpdated
                    if hasattr(parent, 'on_classification_changed'):
                        dialog = parent
                        break
                parent = parent.parent()
            
            if dialog and hasattr(dialog, 'on_classification_changed'):
                dialog.on_classification_changed()
            else:
                # Se não encontrar, ao menos recalcular os tempos para refletir a alteração
                print("Aviso: Não foi possível encontrar o método on_classification_changed. Usando fallback.")
                # Marcar como modificado diretamente
                if dialog:
                    dialog.modified = True
                    
            # Colorir a linha inteira baseado na nova atribuição
            if attributed_to == "Cliente":
                color = QColor(52, 237, 140)  # Azul claro
            elif attributed_to == "Suporte":
                color = QColor(125, 131, 221)  # Verde claro
            elif attributed_to == "Bug":
                color = QColor(255, 235, 162)  # Vermelho claro
            elif attributed_to == "Ignorado":
                color = QColor(192, 192, 192)   # Cinza claro
            else:
                color = QColor(255, 255, 255)  # Branco

            # Aplica a cor a todas as células da linha
            for col in range(self.columnCount()):
                item = self.item(row, col)
                if item:
                    item.setBackground(color)
                    
            
        
    def show_interval_details(self, row):
        """Mostra detalhes das interações no intervalo selecionado"""
        if not self.current_ticket:
            return
            
        # Obter índices das interações
        interval_indices = self.item(row, 0).data(Qt.UserRole)
        if not interval_indices or len(interval_indices) != 2:
            return
            
        from_idx, to_idx = interval_indices
        
        # Obter as interações
        interactions = self.current_ticket.get('interactions', [])
        if 0 <= from_idx < len(interactions) and 0 <= to_idx < len(interactions):
            from_interaction = interactions[from_idx]
            to_interaction = interactions[to_idx]
            
            # Criar diálogo de detalhes
            dialog = InteractionPairDetailsDialog(from_interaction, to_interaction, self.calculator, self)
            dialog.exec_()
    
    def format_time(self, seconds):
        """Formata segundos para HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class InteractionPairDetailsDialog(QDialog):
    """Diálogo para mostrar detalhes de um par de interações"""
    
    def __init__(self, from_interaction, to_interaction, calculator, parent=None):
        super().__init__(parent)
        self.from_interaction = from_interaction
        self.to_interaction = to_interaction
        self.calculator = calculator
        
        self.setWindowTitle("Detalhes do Intervalo")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        
        # Criar splitter para dividir a tela
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo - Interação "De"
        left_panel = QGroupBox("Interação de Origem")
        left_layout = QVBoxLayout(left_panel)
        
        # Informações básicas
        left_info = self.create_interaction_info_widget(self.from_interaction)
        left_layout.addWidget(left_info)
        
        # Conteúdo da mensagem
        left_message = QTextEdit()
        left_message.setReadOnly(True)
        left_message.setHtml(self.from_interaction.get('message', ''))
        left_layout.addWidget(QLabel("Conteúdo:"))
        left_layout.addWidget(left_message)
        
        # Painel direito - Interação "Para"
        right_panel = QGroupBox("Interação de Destino")
        right_layout = QVBoxLayout(right_panel)
        
        # Informações básicas
        right_info = self.create_interaction_info_widget(self.to_interaction)
        right_layout.addWidget(right_info)
        
        # Conteúdo da mensagem
        right_message = QTextEdit()
        right_message.setReadOnly(True)
        right_message.setHtml(self.to_interaction.get('message', ''))
        right_layout.addWidget(QLabel("Conteúdo:"))
        right_layout.addWidget(right_message)
        
        # Adicionar painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 350])
        
        # Adicionar splitter ao layout principal
        layout.addWidget(splitter)
        
        # Calcular tempo entre as interações
        time_diff = (self.to_interaction['date'] - self.from_interaction['date']).total_seconds()
        business_time = self.calculator.calculate_business_time(
            self.from_interaction['date'], 
            self.to_interaction['date']
        )
        
        # Formatar tempos
        time_diff_str = self._format_time_with_days(time_diff)
        business_time_str = self._format_time_with_days(business_time)
        
        
        # Determinar a quem este tempo é atribuído
        current_classification = self.from_interaction.get('classification', self.from_interaction.get('sender_type', ''))
        
        if current_classification == 'C':
            attributed_to = "Suporte"
        elif current_classification == 'A':
            attributed_to = "Cliente"
        elif current_classification == 'B':
            attributed_to = "Bug"
        elif current_classification == 'I':
            attributed_to = "Ignorado"
        else:
            attributed_to = "Desconhecido"
            
        # Painel inferior - Informações do intervalo (destacado)
        interval_panel = QGroupBox("📊 Informações do Intervalo - Destaque")
        interval_panel.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 15px;
                border: 2px solid #2c7be5;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 18px;
                background-color: #f8f9fa;
            }
            QLabel {
                font-size: 13px;
            }
            .highlight {
                font-weight: bold;
                color: #2c7be5;
                font-size: 14px;
            }
        """)

        interval_layout = QGridLayout(interval_panel)
        interval_layout.setVerticalSpacing(12)
        interval_layout.setHorizontalSpacing(20)

        # Adicionar ícones (opcional)
        icon_size = QSize(16, 16)
        time_icon = QLabel()
        time_icon.setPixmap(QIcon(":/icons/clock.png").pixmap(icon_size))
        business_icon = QLabel()
        business_icon.setPixmap(QIcon(":/icons/business.png").pixmap(icon_size))

        # Posicionamento dos elementos
        row = 0
        for label, value, icon, is_important in [
            ("Tempo Total:", time_diff_str, time_icon, True),
            ("Tempo Comercial:", business_time_str, business_icon, True),
            ("Classificação Atual:", self.from_interaction.get('classification', 'Não definida'), None, False),
            ("Atribuído a:", attributed_to, None, True)
        ]:
            lbl = QLabel(f"<b>{label}</b>")
            val = QLabel(value)
            
            if is_important:
                val.setProperty("class", "highlight")
                if icon:
                    interval_layout.addWidget(icon, row, 0, Qt.AlignRight)
                    interval_layout.addWidget(lbl, row, 1)
                    interval_layout.addWidget(val, row, 2)
                else:
                    interval_layout.addWidget(lbl, row, 1)
                    interval_layout.addWidget(val, row, 2)
            else:
                interval_layout.addWidget(lbl, row, 1)
                interval_layout.addWidget(val, row, 2)
            
            row += 1

        layout.addWidget(interval_panel)
        
        # Botão de fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
    def create_interaction_info_widget(self, interaction):
        """Cria widget com informações básicas de uma interação"""
        widget = QWidget()
        form = QFormLayout(widget)
        
        # Data/Hora
        date_str = interaction['date'].strftime("%Y-%m-%d %H:%M:%S")
        form.addRow("Data/Hora:", QLabel(date_str))
        
        # Remetente
        sender = interaction.get('sender', 'Desconhecido')
        form.addRow("Remetente:", QLabel(sender))
        
        # Tipo Original
        sender_type = interaction.get('sender_type', 'Desconhecido')
        form.addRow("Tipo Original:", QLabel(sender_type))
        
        # Classificação Atual
        classification = interaction.get('classification', sender_type)
        form.addRow("Classificação Atual:", QLabel(classification))
        
        # Status
        status = interaction.get('status', 'Desconhecido')
        form.addRow("Status:", QLabel(status))
        
        # Anexos
        has_attachments = "Sim" if interaction.get('has_attachments') else "Não"
        form.addRow("Tem Anexos:", QLabel(has_attachments))
        
        return widget
        
    def _format_time_with_days(self, seconds):
        """Formata segundos incluindo dias quando aplicável"""
        days = int(seconds // (3600 * 24))
        remaining = seconds % (3600 * 24)
        
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        secs = int(remaining % 60)
        
        if days > 0:
            return f"{days} dias, {hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"


class InteractionClassifierDialogUpdated(QDialog):
    """Versão aprimorada do diálogo para classificação manual de interações de tickets"""
    
    def __init__(self, tickets_data, parent=None):
        super().__init__(parent)
        self.tickets_data = tickets_data  # Lista de análises de tickets
        self.current_ticket_index = 0
        self.modified = False  # Flag para indicar se houve modificações
        
        self.setWindowTitle("Classificador de Interações")
        self.setMinimumSize(1000, 700)
        self.setWindowState(Qt.WindowMaximized)
        
        self.init_ui()
        self.load_current_ticket()
        
    def init_ui(self):
        """Inicializa os componentes da UI"""
        layout = QVBoxLayout()
        
        # Seção superior - Seletor de ticket e botões
        top_layout = QHBoxLayout()
        
        # Layout do seletor de tickets - Versão aprimorada
        ticket_selector_layout = QHBoxLayout()
        ticket_selector_layout.setContentsMargins(0, 0, 0, 0)  # Remove margens padrão
        ticket_selector_layout.setSpacing(10)  # Espaço entre elementos

        # Label com estilo
        ticket_label = QLabel("Selecionar Ticket:")
        ticket_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2C3E50;
                padding: 2px 0;
            }
        """)
        ticket_selector_layout.addWidget(ticket_label)

        # ComboBox estilizado
        self.ticket_selector = QComboBox()
        self.ticket_selector.setStyleSheet("""
            QComboBox {
                min-width: 300px;
                padding: 5px;
                border: 1px solid #BDC3C7;
                border-radius: 4px;
                background: white;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                min-width: 300px;
            }
        """)

        # Preenche o combobox
        for i, ticket in enumerate(self.tickets_data):
            self.ticket_selector.addItem(f"{ticket.get('protocol', '')} - {ticket.get('subject', '')}", i)
            
        self.ticket_selector.currentIndexChanged.connect(self.on_ticket_changed)
        ticket_selector_layout.addWidget(self.ticket_selector, 1)  # Adiciona stretch factor 1

        # Adiciona espaço flexível antes do checkbox (se necessário)
        ticket_selector_layout.addStretch()
        
        # Adiciona ao layout principal com espaçamento
        top_layout.addLayout(ticket_selector_layout)
        top_layout.setSpacing(15)  # Espaço entre linhas do top_layout
        
        # Botões de recálculo e exportação
        recalculate_btn = QPushButton("Recalcular Tempos")
        recalculate_btn.clicked.connect(self.recalculate_times)
        top_layout.addWidget(recalculate_btn)
        
        calculator_btn = QPushButton("Calculadora de Tempos/Período")
        calculator_btn.clicked.connect(self.open_time_calculator)
        top_layout.addWidget(calculator_btn)
        
        export_btn = QPushButton("Exportar para CSV")
        export_btn.clicked.connect(self.export_to_csv)
        top_layout.addWidget(export_btn)
        
        # Botão de ajuda
        help_btn = QPushButton("Ajuda sobre Cálculos")
        help_btn.setIcon(QIcon.fromTheme("help-contents"))
        help_btn.clicked.connect(self.show_help)
        top_layout.addWidget(help_btn)
        
        layout.addLayout(top_layout)
        
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 5px; padding: 3px;")
        header_layout = QGridLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setHorizontalSpacing(10)
        header_layout.setVerticalSpacing(2)
        header_frame.setLayout(header_layout)

        # Campos de informação
        self.header_protocol = QLabel("")
        self.header_protocol.setStyleSheet("font-weight: bold;")
        self.header_subject = QLabel("")
        self.header_subject.setStyleSheet("font-weight: bold;")
        self.header_customer = QLabel("")
        self.header_creation = QLabel("")
        self.header_status = QLabel("")
        self.header_status.setStyleSheet("font-weight: bold;")
        self.header_sla = QLabel("")
        self.header_end_label = QLabel("Encerrado:")
        self.header_end = QLabel("")

        # Linha 1
        header_layout.addWidget(QLabel("Protocolo:"), 0, 0)
        header_layout.addWidget(self.header_protocol, 0, 1)
        header_layout.addWidget(QLabel("Assunto:"), 0, 2)
        header_layout.addWidget(self.header_subject, 0, 3, 1, 3)

        # Linha 2
        header_layout.addWidget(QLabel("Cliente:"), 1, 0)
        header_layout.addWidget(self.header_customer, 1, 1)
        header_layout.addWidget(QLabel("Criado:"), 1, 2)
        header_layout.addWidget(self.header_creation, 1, 3)
        header_layout.addWidget(QLabel("Status:"), 1, 4)
        header_layout.addWidget(self.header_status, 1, 5)
        header_layout.addWidget(QLabel("SLA:"), 1, 6)
        header_layout.addWidget(self.header_sla, 1, 7)
        header_layout.addWidget(self.header_end_label, 1, 8)
        header_layout.addWidget(self.header_end, 1, 9)

        # Inicialmente oculta elementos opcionais
        self.header_end_label.setVisible(False)
        self.header_end.setVisible(False)

        layout.addWidget(header_frame)
        
        self.analyzed_checkbox = QCheckBox("Ticket Analisado")
        self.analyzed_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 5px;
                font-weight: bold;
                color: #2C3E50;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #BDC3C7;
                border-radius: 3px;
                background: white;
            }
            QCheckBox::indicator:unchecked:hover {
                border: 2px solid #7F8C8D;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #27AE60;
                border-radius: 3px;
                background: qradialgradient(
                    cx:0.5, cy:0.5, radius:0.4,
                    fx:0.5, fy:0.5,
                    stop:0 white, stop:0.5 white, stop:0.6 #27AE60
                );
                image: url(:/icons/checkmark.svg);
            }
            QCheckBox::indicator:checked:hover {
                border: 2px solid #219653;
            }
            QCheckBox::indicator:pressed {
                background-color: #D5F5E3;
            }
        """)
        self.analyzed_checkbox.stateChanged.connect(self.on_analyzed_changed)
        ticket_selector_layout.addWidget(self.analyzed_checkbox)
        
        # Inicializa dicionário para rastrear tickets analisados
        self.analyzed_tickets = {i: False for i in range(len(self.tickets_data))}
        
        # Tabs para diferentes visualizações
        self.tabs = QTabWidget()
        
        # Tab 1: Visualização por pares de interações (Nova visualização)
        self.pairs_tab = QWidget()
        pairs_layout = QVBoxLayout(self.pairs_tab)
        
        # Tabela de pares de interações
        self.pairs_table = InteractionPairTableView()
        pairs_layout.addWidget(self.pairs_table)
        
        self.tabs.addTab(self.pairs_tab, "Visualização por Intervalos")
        
        # Tab 2: Visualização tradicional (lista de interações)
        self.list_tab = QWidget()
        list_layout = QVBoxLayout(self.list_tab)
        
        # Filtros (movidos da versão original)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar:"))
        
        self.filter_type = QComboBox()
        self.filter_type.addItem("Todos os Tipos", "")
        self.filter_type.addItem("Cliente (C)", "C")
        self.filter_type.addItem("Suporte (A)", "A")
        self.filter_type.addItem("Bug (B)", "B")
        self.filter_type.addItem("Ignorar (I)", "I")
        self.filter_type.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_type)
        
        self.filter_status = QLineEdit()
        self.filter_status.setPlaceholderText("Filtrar por status...")
        self.filter_status.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.filter_status)
        
        clear_filter_btn = QPushButton("Limpar Filtros")
        clear_filter_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_filter_btn)
        
        list_layout.addLayout(filter_layout)
        
        # Splitter para tabela e visualização de mensagem
        splitter = QSplitter(Qt.Vertical)
        
        # Tabela de interações individuais (original)
        self.interaction_table = QTableWidget()
        self.interaction_table.setColumnCount(7)
        self.interaction_table.setHorizontalHeaderLabels([
            "Data/Hora", "Remetente", "Tipo Original", "Classificação Atual", 
            "Status", "Tem Anexo", "Prévia"
        ])
        self.interaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.interaction_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.interaction_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.interaction_table.setSelectionMode(QTableWidget.SingleSelection)
        self.interaction_table.selectionModel().selectionChanged.connect(self.on_interaction_selected)
        
        # Visualizador de mensagem
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        
        splitter.addWidget(self.interaction_table)
        splitter.addWidget(self.message_display)
        splitter.setSizes([400, 200])
        
        list_layout.addWidget(splitter)
        
        # Botões de classificação (movidos da versão original)
        classify_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Resetar para Original")
        reset_btn.clicked.connect(self.reset_classifications)
        classify_layout.addWidget(reset_btn)
        
        classify_as_client_btn = QPushButton("Classificar como Cliente (C)")
        classify_as_client_btn.clicked.connect(lambda: self.classify_selected("C"))
        classify_layout.addWidget(classify_as_client_btn)
        
        classify_as_support_btn = QPushButton("Classificar como Suporte (A)")
        classify_as_support_btn.clicked.connect(lambda: self.classify_selected("A"))
        classify_layout.addWidget(classify_as_support_btn)
        
        classify_as_bug_btn = QPushButton("Classificar como Bug (B)")
        classify_as_bug_btn.clicked.connect(lambda: self.classify_selected("B"))
        classify_layout.addWidget(classify_as_bug_btn)
        
        classify_as_ignore_btn = QPushButton("Ignorar (I)")
        classify_as_ignore_btn.clicked.connect(lambda: self.classify_selected("I"))
        classify_layout.addWidget(classify_as_ignore_btn)
        
        list_layout.addLayout(classify_layout)
        
        self.tabs.addTab(self.list_tab, "Lista de Interações")
        
        layout.addWidget(self.tabs)
        
        # Seção inferior - Comparação de métricas de tempo com preview
        metrics_group = QGroupBox("Comparação de Métricas de Tempo")
        metrics_layout = QGridLayout()

        # Cabeçalhos
        metrics_layout.addWidget(QLabel("Métrica"), 0, 0)
        metrics_layout.addWidget(QLabel("Original"), 0, 1)
        metrics_layout.addWidget(QLabel("Após Reclassificação"), 0, 2)
        metrics_layout.addWidget(QLabel("Diferença"), 0, 3)
        metrics_layout.addWidget(QLabel("Preview"), 0, 4)

        # Linhas para cada métrica
        metrics = [
            ("Tempo Comercial com Cliente", "business_time_with_client", "reclassified_business_time_with_client"),
            ("Tempo Comercial com Suporte", "business_time_with_support", "reclassified_business_time_with_support"),
            ("Tempo Comercial em Status de Bug", "", "reclassified_business_time_in_bug"),
            ("Tempo Comercial Ignorado", "", "reclassified_business_time_ignored"),
            ("Tempo com Cliente", "time_with_client", "reclassified_time_with_client"),
            ("Tempo com Suporte", "time_with_support", "reclassified_time_with_support"),
            ("Tempo em Status de Bug", "", "reclassified_time_in_bug"),
            ("Tempo Ignorado", "", "reclassified_time_ignored")
        ]

        self.metric_labels = {}

        current_row = 1  # Começa na linha 1 (após os cabeçalhos)

        for label, orig_key, new_key in metrics:
            metrics_layout.addWidget(QLabel(label), current_row, 0)
            
            # Valor original
            self.metric_labels[f"{orig_key}_orig"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{orig_key}_orig"], current_row, 1)
            
            # Novo valor
            self.metric_labels[f"{new_key}_new"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{new_key}_new"], current_row, 2)
            
            # Diferença
            self.metric_labels[f"{new_key}_diff"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{new_key}_diff"], current_row, 3)
            
            # Preview (simulação antes de confirmação)
            self.metric_labels[f"{new_key}_preview"] = QLabel("00:00:00")
            self.metric_labels[f"{new_key}_preview"].setStyleSheet("color: gray; font-style: italic;")
            metrics_layout.addWidget(self.metric_labels[f"{new_key}_preview"], current_row, 4)
            
            current_row += 1
            
            # Adicionar subtotal após "Tempo Comercial Ignorado" (4ª métrica)
            if label == "Tempo Comercial Ignorado":
                # Adicionar linha para separar as métricas comerciais e normais
                separator1 = QFrame()
                separator1.setFrameShape(QFrame.HLine)
                separator1.setFrameShadow(QFrame.Sunken)
                metrics_layout.addWidget(separator1, current_row, 0, 1, 5)
                current_row += 1

                # Adicionar linha de subtotal para tempos comerciais
                metrics_layout.addWidget(QLabel("<b>Subtotal Comercial:</b>"), current_row, 0)

                # Subtotal Comercial - Original
                self.subtotal_comercial_orig = QLabel("00:00:00")
                self.subtotal_comercial_orig.setStyleSheet("font-weight: bold; color: green;")
                metrics_layout.addWidget(self.subtotal_comercial_orig, current_row, 1)

                # Subtotal Comercial - Após Reclassificação
                self.subtotal_comercial_new = QLabel("00:00:00")
                self.subtotal_comercial_new.setStyleSheet("font-weight: bold; color: green;")
                metrics_layout.addWidget(self.subtotal_comercial_new, current_row, 2)

                # Subtotal Comercial - Preview
                self.subtotal_comercial_preview = QLabel("00:00:00")
                self.subtotal_comercial_preview.setStyleSheet("font-weight: bold; color: green; font-style: italic;")
                metrics_layout.addWidget(self.subtotal_comercial_preview, current_row, 4)
                
                current_row += 1

            # Adicionar subtotal após "Tempo Ignorado" (última métrica)
            elif label == "Tempo Ignorado":
                # Adicionar separador entre o subtotal comercial e as métricas normais
                separator2 = QFrame()
                separator2.setFrameShape(QFrame.HLine)
                separator2.setFrameShadow(QFrame.Sunken)
                metrics_layout.addWidget(separator2, current_row, 0, 1, 5)
                current_row += 1

                # Adicionar linha de subtotal para tempos normais
                metrics_layout.addWidget(QLabel("<b>Subtotal Normal:</b>"), current_row, 0)

                # Subtotal Normal - Original
                self.subtotal_normal_orig = QLabel("00:00:00")
                self.subtotal_normal_orig.setStyleSheet("font-weight: bold; color: blue;")
                metrics_layout.addWidget(self.subtotal_normal_orig, current_row, 1)

                # Subtotal Normal - Após Reclassificação
                self.subtotal_normal_new = QLabel("00:00:00")
                self.subtotal_normal_new.setStyleSheet("font-weight: bold; color: blue;")
                metrics_layout.addWidget(self.subtotal_normal_new, current_row, 2)

                # Subtotal Normal - Preview
                self.subtotal_normal_preview = QLabel("00:00:00")
                self.subtotal_normal_preview.setStyleSheet("font-weight: bold; color: blue; font-style: italic;")
                metrics_layout.addWidget(self.subtotal_normal_preview, current_row, 4)
                
                current_row += 1

        # Botão para atualizar preview
        preview_btn = QPushButton("Atualizar Preview")
        preview_btn.clicked.connect(self.update_preview)
        metrics_layout.addWidget(preview_btn, current_row, 4)

        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)

        # Botões inferiores
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        close_btn = QPushButton("Cancelar")
        close_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(close_btn)

        save_btn = QPushButton("Aplicar Alterações")
        save_btn.setStyleSheet("background-color:rgb(52, 237, 140)")
        save_btn.setToolTip("Aplicar as alterações dos tickets reclassificados.")
        save_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)
    
    def open_time_calculator(self):
        """Abre a calculadora de tempos"""
        # Obtém o calculador de horas comerciais
        calculator = None
        parent = self.parent()
        
        if hasattr(parent, 'calculator'):
            calculator = parent.calculator
        elif hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'calculator'):
            calculator = parent.analyzer.calculator
        
        if calculator:
            dialog = TimeCalculatorDialog(calculator, self)
            dialog.setWindowModality(Qt.NonModal)
            dialog.show()
        else:
            QMessageBox.warning(self, "Erro", "Calculadora de horário comercial não encontrada.")
    
    def on_analyzed_changed(self, state):
        """Atualiza o estado de análise do ticket atual"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            self.analyzed_tickets[self.current_ticket_index] = (state == Qt.Checked)
            self.update_ticket_selector_colors()

    def update_ticket_selector_colors(self):
        """Atualiza as cores dos itens no seletor de tickets"""
        for i in range(self.ticket_selector.count()):
            index = self.ticket_selector.itemData(i)
            if self.analyzed_tickets.get(index, False):
                self.ticket_selector.setItemData(i, QColor("#E0FFE0"), Qt.BackgroundRole)
            else:
                self.ticket_selector.setItemData(i, QColor("#FFE0E0"), Qt.BackgroundRole)

    def on_ticket_changed(self, index):
        """Sobrescrito para atualizar o checkbox ao mudar de ticket"""
        if index >= 0:
            self.current_ticket_index = self.ticket_selector.currentData()
            self.analyzed_checkbox.setChecked(self.analyzed_tickets.get(self.current_ticket_index, False))
            self.load_current_ticket()
       
    
    def load_current_ticket(self):
        """Carrega os dados do ticket atualmente selecionado"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            
            # AQUI: Adicione este código para atualizar o cabeçalho
            # Formatação de datas para exibição (remover timezone e deixar apenas data/hora)
            def format_date(date_str):
                if not date_str:
                    return "-"
                return date_str.split('-03:00')[0] if '-03:00' in date_str else date_str.split('-0300')[0]

            # Atualiza o cabeçalho
            self.header_protocol.setText(str(ticket.get('protocol', '')))
            self.header_subject.setText(str(ticket.get('subject', '')))
            self.header_customer.setText(str(ticket.get('customer_name', '')))
            self.header_creation.setText(format_date(ticket.get('creation_date', '')))
            self.header_status.setText(str(ticket.get('current_situation', '')))

            # Informações de SLA
            sla_deadline = ticket.get('sla', {}).get('deadline', {}).get('date')
            sla_accomplished = ticket.get('sla', {}).get('deadline', {}).get('accomplished')

            if sla_deadline:
                sla_text = f"Prazo: {format_date(sla_deadline)}"
                if sla_accomplished is not None:
                    sla_status = "✓" if sla_accomplished else "✗"
                    sla_color = "green" if sla_accomplished else "red"
                    sla_text += f" <span style='color:{sla_color};'>{sla_status}</span>"
                
                self.header_sla.setText(sla_text)
                self.header_sla.setToolTip("SLA cumprido" if sla_accomplished else "SLA não cumprido")
            else:
                self.header_sla.setText("-")

            # Data de encerramento, se disponível
            end_date = ticket.get('end_date')
            if end_date:
                self.header_end.setText(format_date(end_date))
                self.header_end_label.setVisible(True)
                self.header_end.setVisible(True)
            else:
                self.header_end_label.setVisible(False)
                self.header_end.setVisible(False)
            
            # Inicializa valores reclassificados com os originais se não existirem
            if 'reclassified_time_with_client' not in ticket:
                ticket['reclassified_time_with_client'] = ticket.get('time_with_client', 0)
            if 'reclassified_time_with_support' not in ticket:
                ticket['reclassified_time_with_support'] = ticket.get('time_with_support', 0)
            if 'reclassified_business_time_with_client' not in ticket:
                ticket['reclassified_business_time_with_client'] = ticket.get('business_time_with_client', 0)
            if 'reclassified_business_time_with_support' not in ticket:
                ticket['reclassified_business_time_with_support'] = ticket.get('business_time_with_support', 0)
            if 'reclassified_time_in_bug' not in ticket:
                ticket['reclassified_time_in_bug'] = 0
            if 'reclassified_business_time_in_bug' not in ticket:
                ticket['reclassified_business_time_in_bug'] = 0
            if 'reclassified_time_ignored' not in ticket:
                ticket['reclassified_time_ignored'] = 0
            if 'reclassified_business_time_ignored' not in ticket:
                ticket['reclassified_business_time_ignored'] = 0
            
            # Garantir que todas as interações têm classificação (inicialmente igual ao tipo original)
            for interaction in ticket.get('interactions', []):
                if 'classification' not in interaction:
                    interaction['classification'] = interaction.get('sender_type', '')
            
            # Obtém o calculador de horas comerciais
            calculator = None
            parent = self.parent()
            
            if hasattr(parent, 'calculator'):
                calculator = parent.calculator
            elif hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'calculator'):
                calculator = parent.analyzer.calculator
            
            # Carregar na nova visualização de pares
            if calculator:
                self.pairs_table.load_ticket_data(ticket, calculator)
                
            # Atualizar a visualização tradicional em lista
            self.update_interaction_table()
            
            # Atualizar métricas
            self.update_metrics_comparison()

    def on_classification_changed(self):
        """Chamado quando uma classificação é alterada na tabela de pares"""
        self.modified = True
        
        # Atualizar visualização tradicional em lista
        self.update_interaction_table()
        
        # Atualizar métricas
        self.recalculate_times()

    def reset_classifications(self):
        """Reseta todas as classificações para seus valores originais"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            interactions = ticket.get('interactions', [])
            
            # Reset each interaction's classification to its original type
            modified = False
            for interaction in interactions:
                if interaction.get('classification') != interaction.get('sender_type'):
                    interaction['classification'] = interaction.get('sender_type', '')
                    modified = True
            
            if modified:
                # Reset reclassified metrics to original values
                ticket['reclassified_time_with_client'] = ticket.get('time_with_client', 0)
                ticket['reclassified_time_with_support'] = ticket.get('time_with_support', 0)
                ticket['reclassified_business_time_with_client'] = ticket.get('business_time_with_client', 0)
                ticket['reclassified_business_time_with_support'] = ticket.get('business_time_with_support', 0)
                ticket['reclassified_time_in_bug'] = 0
                ticket['reclassified_business_time_in_bug'] = 0
                ticket['reclassified_time_ignored'] = 0
                ticket['reclassified_business_time_ignored'] = 0
                
                self.modified = True
                
                # Update the UI
                self.load_current_ticket()
                
                # Feedback
                QMessageBox.information(self, "Reset Completo", "Todas as classificações foram resetadas para seus valores originais.")
            else:
                QMessageBox.information(self, "Sem Alterações", "Nenhuma classificação foi alterada em relação aos valores originais.")

    def update_interaction_table(self):
        """Atualiza a tabela de interações com base nos filtros atuais"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            interactions = ticket.get('interactions', [])
            
            # Aplica filtros
            filter_type = self.filter_type.currentData()
            filter_status = self.filter_status.text().strip().lower()
            
            filtered_interactions = []
            for i, interaction in enumerate(interactions):
                # Filtro por tipo
                if filter_type and interaction.get('classification') != filter_type:
                    continue
                    
                # Filtro por status
                status = interaction.get('status', '')
                if filter_status and (not status or filter_status not in status.lower()):
                    continue
                    
                filtered_interactions.append((i, interaction))
                
            # Preenche a tabela
            self.interaction_table.setRowCount(len(filtered_interactions))
            
            for row, (orig_index, interaction) in enumerate(filtered_interactions):
                # Verifica se é uma interação virtual (criação do ticket)
                is_virtual = interaction.get('is_virtual', False)
                
                # Data/Hora
                date_item = QTableWidgetItem(interaction.get('date').strftime("%Y-%m-%d %H:%M:%S") if interaction.get('date') else "")
                date_item.setData(Qt.UserRole, orig_index)  # Armazena o índice original
                if is_virtual:
                    date_item.setBackground(QColor(192, 192, 192) )  # Fundo cinza claro para interações virtuais
                self.interaction_table.setItem(row, 0, date_item)
                
                # Remetente
                sender_item = QTableWidgetItem(interaction.get('sender', ''))
                if is_virtual:
                    sender_item.setText(f"{sender_item.text()} (Criação do Ticket)")
                    sender_item.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 1, sender_item)
                
                # Tipo Original
                type_item = QTableWidgetItem(interaction.get('sender_type', ''))
                if is_virtual:
                    type_item.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 2, type_item)
                
                # Classificação Atual
                class_item = QTableWidgetItem(interaction.get('classification', ''))
                if interaction.get('classification') != interaction.get('sender_type'):
                    class_item.setBackground(QColor(255, 255, 0))  # Destaca mudanças
                elif is_virtual:
                    class_item.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 3, class_item)
                
                # Status
                status_item = QTableWidgetItem(interaction.get('status', ''))
                if is_virtual:
                    status_item.setText("Ticket Criado")
                    status_item.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 4, status_item)
                
                # Tem anexos
                has_attach = QTableWidgetItem('Sim' if interaction.get('has_attachments') else 'Não')
                has_attach.setTextAlignment(Qt.AlignCenter)
                if is_virtual:
                    has_attach.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 5, has_attach)
                
                # Prévia da mensagem
                message = interaction.get('message', '')
                # Remover HTML para exibição na prévia
                preview = re.sub('<[^<]+?>', '', message)
                preview = preview[:100] + "..." if len(preview) > 100 else preview
                preview_item = QTableWidgetItem(preview)
                if is_virtual:
                    preview_item.setBackground(QColor(192, 192, 192) )
                self.interaction_table.setItem(row, 6, preview_item)

    def on_interaction_selected(self, selected, deselected):
        """Lida com seleção de interação"""
        indexes = selected.indexes()
        if indexes:
            row = indexes[0].row()
            orig_index = self.interaction_table.item(row, 0).data(Qt.UserRole)
            
            # Obtém a interação selecionada
            interaction = self.tickets_data[self.current_ticket_index]['interactions'][orig_index]
            
            # Exibe o conteúdo na área de visualização
            message = interaction.get('message', '')
            self.message_display.setHtml(message)

    def classify_selected(self, classification):
        """Classifica a interação selecionada"""
        selected_rows = self.interaction_table.selectionModel().selectedRows()
        if not selected_rows:
            return
            
        row = selected_rows[0].row()
        orig_index = self.interaction_table.item(row, 0).data(Qt.UserRole)
        
        # Atualiza a classificação
        self.tickets_data[self.current_ticket_index]['interactions'][orig_index]['classification'] = classification
        self.modified = True
        
        # Atualiza as visualizações
        self.update_interaction_table()
        
        # Atualiza a visualização de pares
        calculator = None
        parent = self.parent()
        
        if hasattr(parent, 'calculator'):
            calculator = parent.calculator
        elif hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'calculator'):
            calculator = parent.analyzer.calculator
            
        if calculator:
            # Recarrega a visualização de pares
            ticket = self.tickets_data[self.current_ticket_index]
            self.pairs_table.load_ticket_data(ticket, calculator)
        
        # Recalcula métricas
        self.recalculate_times()

    def apply_filters(self):
        """Aplica filtros à tabela de interações"""
        self.update_interaction_table()

    def clear_filters(self):
        """Limpa todos os filtros"""
        self.filter_type.setCurrentIndex(0)
        self.filter_status.clear()
        self.update_interaction_table()

    def update_preview(self):
        """Atualiza o preview das métricas recalculadas sem salvar as alterações"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            # Salva uma cópia do ticket atual
            ticket = self.tickets_data[self.current_ticket_index]
            interactions_backup = []
            
            # Faz backup das classificações atuais
            for interaction in ticket.get('interactions', []):
                interactions_backup.append(interaction.get('classification', ''))
            
            # Recalcula tempos (isso modifica o ticket)
            self.recalculate_times()
            
            # Salva os valores calculados como preview
            preview_metrics = {
                'reclassified_time_with_client': ticket.get('reclassified_time_with_client', 0),
                'reclassified_time_with_support': ticket.get('reclassified_time_with_support', 0),
                'reclassified_business_time_with_client': ticket.get('reclassified_business_time_with_client', 0),
                'reclassified_business_time_with_support': ticket.get('reclassified_business_time_with_support', 0),
                'reclassified_time_in_bug': ticket.get('reclassified_time_in_bug', 0),
                'reclassified_business_time_in_bug': ticket.get('reclassified_business_time_in_bug', 0),
                'reclassified_time_ignored': ticket.get('reclassified_time_ignored', 0),
                'reclassified_business_time_ignored': ticket.get('reclassified_business_time_ignored', 0)
            }
            
            # Calcular subtotais para preview
            comercial_preview_total = (
                preview_metrics['reclassified_business_time_with_client'] +
                preview_metrics['reclassified_business_time_with_support'] +
                preview_metrics['reclassified_business_time_in_bug'] +
                preview_metrics['reclassified_business_time_ignored']
            )
            
            normal_preview_total = (
                preview_metrics['reclassified_time_with_client'] +
                preview_metrics['reclassified_time_with_support'] +
                preview_metrics['reclassified_time_in_bug'] +
                preview_metrics['reclassified_time_ignored']
            )
            
            # Atualizar os labels de subtotal do preview
            self.subtotal_comercial_preview.setText(self.seconds_to_time_format(comercial_preview_total))
            self.subtotal_normal_preview.setText(self.seconds_to_time_format(normal_preview_total))
            
            # Atualiza visualização de preview
            for key, value in preview_metrics.items():
                time_str = self.seconds_to_time_format(value)
                if self.metric_labels.get(f"{key}_preview"):
                    self.metric_labels[f"{key}_preview"].setText(time_str)
                    
            # Feedback visual de que o preview foi atualizado
            for key in preview_metrics.keys():
                if self.metric_labels.get(f"{key}_preview"):
                    original_style = self.metric_labels[f"{key}_preview"].styleSheet()
                    self.metric_labels[f"{key}_preview"].setStyleSheet("color: blue; font-weight: bold;")
                    
                    # Restaura o estilo após um breve intervalo
                    QTimer.singleShot(1000, lambda label=self.metric_labels[f"{key}_preview"], style=original_style: 
                                    label.setStyleSheet(style))
            
            # Destacar também os subtotais do preview
            original_comercial_style = self.subtotal_comercial_preview.styleSheet()
            self.subtotal_comercial_preview.setStyleSheet("font-weight: bold; color: green; font-style: italic; background-color: #f0fff0;")
            QTimer.singleShot(1000, lambda: self.subtotal_comercial_preview.setStyleSheet(original_comercial_style))
            
            original_normal_style = self.subtotal_normal_preview.styleSheet()
            self.subtotal_normal_preview.setStyleSheet("font-weight: bold; color: blue; font-style: italic; background-color: #f0f8ff;")
            QTimer.singleShot(1000, lambda: self.subtotal_normal_preview.setStyleSheet(original_normal_style))

    def update_metrics_comparison(self):
        """Atualiza a seção de comparação de métricas"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            
            # Função para calcular diferença
            def calc_diff(new_val, old_val):
                try:
                    new_val = float(new_val or 0)
                    old_val = float(old_val or 0)
                    return new_val - old_val
                except (ValueError, TypeError):
                    return 0
            
            # Inicializa somatórios
            comercial_orig_total = 0
            comercial_new_total = 0
            normal_orig_total = 0
            normal_new_total = 0
            
            # Definir métricas comerciais
            comercial_metrics = [
                ("business_time_with_client", "reclassified_business_time_with_client"),
                ("business_time_with_support", "reclassified_business_time_with_support"),
                (None, "reclassified_business_time_in_bug"),
                (None, "reclassified_business_time_ignored")
            ]
            
            # Definir métricas normais (não comerciais)
            normal_metrics = [
                ("time_with_client", "reclassified_time_with_client"),
                ("time_with_support", "reclassified_time_with_support"),
                (None, "reclassified_time_in_bug"),
                (None, "reclassified_time_ignored")
            ]
            
            # Processar métricas comerciais
            for orig_key, new_key in comercial_metrics:
                # Original
                if orig_key:
                    orig_val = ticket.get(orig_key, 0)
                    comercial_orig_total += orig_val  # Adiciona ao total comercial
                    formatted_orig = self.seconds_to_time_format(orig_val)
                    self.metric_labels[f"{orig_key}_orig"].setText(formatted_orig)
                
                # Reclassificado
                new_val = ticket.get(new_key, 0)
                comercial_new_total += new_val  # Adiciona ao total comercial
                formatted_new = self.seconds_to_time_format(new_val)
                self.metric_labels[f"{new_key}_new"].setText(formatted_new)
                
                # Diferença
                if orig_key:
                    diff = calc_diff(new_val, ticket.get(orig_key, 0))
                    
                    # Formata a diferença
                    if diff == 0:
                        diff_text = "00:00:00"
                    else:
                        diff_abs = self.seconds_to_time_format(abs(diff))
                        diff_text = f"{'+' if diff > 0 else '-'}{diff_abs}"
                    
                    self.metric_labels[f"{new_key}_diff"].setText(diff_text)
                    
                    # Destaca diferenças
                    if diff < 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: red;")
                    elif diff > 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: green;")
                    else:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("")
            
            # Processar métricas normais
            for orig_key, new_key in normal_metrics:
                # Original
                if orig_key:
                    orig_val = ticket.get(orig_key, 0)
                    normal_orig_total += orig_val  # Adiciona ao total normal
                    formatted_orig = self.seconds_to_time_format(orig_val)
                    self.metric_labels[f"{orig_key}_orig"].setText(formatted_orig)
                
                # Reclassificado
                new_val = ticket.get(new_key, 0)
                normal_new_total += new_val  # Adiciona ao total normal
                formatted_new = self.seconds_to_time_format(new_val)
                self.metric_labels[f"{new_key}_new"].setText(formatted_new)
                
                # Diferença
                if orig_key:
                    diff = calc_diff(new_val, ticket.get(orig_key, 0))
                    
                    # Formata a diferença
                    if diff == 0:
                        diff_text = "00:00:00"
                    else:
                        diff_abs = self.seconds_to_time_format(abs(diff))
                        diff_text = f"{'+' if diff > 0 else '-'}{diff_abs}"
                    
                    self.metric_labels[f"{new_key}_diff"].setText(diff_text)
                    
                    # Destaca diferenças
                    if diff < 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: red;")
                    elif diff > 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: green;")
                    else:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("")
            
            # Atualiza os subtotais
            self.subtotal_comercial_orig.setText(self.seconds_to_time_format(comercial_orig_total))
            self.subtotal_comercial_new.setText(self.seconds_to_time_format(comercial_new_total))
            self.subtotal_normal_orig.setText(self.seconds_to_time_format(normal_orig_total))
            self.subtotal_normal_new.setText(self.seconds_to_time_format(normal_new_total))

    def seconds_to_time_format(self, seconds):
        """Converte segundos para formato HH:MM:SS"""
        if seconds is None:
            return "00:00:00"
            
        # Garante que o valor é um número
        try:
            seconds = float(seconds)
        except (ValueError, TypeError):
            return "00:00:00"
            
        # Converte para formato de tempo
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def recalculate_times(self):
        """Recalcula métricas de tempo com base nas classificações atuais"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            current_ticket = self.tickets_data[self.current_ticket_index]
            interactions = current_ticket.get('interactions', [])
            
            # Inicializa métricas
            time_with_client = 0
            time_with_support = 0
            time_in_bug = 0
            time_ignored = 0
            business_time_with_client = 0
            business_time_with_support = 0
            business_time_in_bug = 0
            business_time_ignored = 0
            
            # Obtém o calculador de horas comerciais
            calculator = None
            parent = self.parent()
            
            if hasattr(parent, 'calculator'):
                calculator = parent.calculator
            elif hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'calculator'):
                calculator = parent.analyzer.calculator
            
            if calculator:
                # Ordena interações por data
                sorted_interactions = sorted(
                    [i for i in interactions if i.get('date')],
                    key=lambda x: x.get('date')
                )
                
                # Obtém data de criação do ticket
                creation_dt = None
                if hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'parse_datetime') and current_ticket.get('creation_date'):
                    creation_dt = parent.analyzer.parse_datetime(current_ticket.get('creation_date'))
                else:
                    try:
                        dt_str = current_ticket.get('creation_date').rsplit('-', 1)[0].strip()
                        creation_dt = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Erro ao analisar data de criação: {e}")
                
                if not creation_dt:
                    print("Falha ao analisar data de criação")
                    return
                    
                # Verifica se o ticket está finalizado
                end_date = None
                is_finished = False
                
                # Verifica end_date
                if current_ticket.get('end_date'):
                    try:
                        dt_str = current_ticket.get('end_date').rsplit('-', 1)[0].strip()
                        end_date = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                        is_finished = True
                    except Exception as e:
                        print(f"Erro ao analisar data final: {e}")
                
                # Verifica situation
                situation_id = current_ticket.get('situation', {}).get('id')
                situation_date = None
                
                if situation_id in [4, 5]:  # Cancelada ou Finalizada
                    is_finished = True
                    try:
                        dt_str = current_ticket.get('situation', {}).get('apply_date', '').rsplit('-', 1)[0].strip()
                        situation_date = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Erro ao analisar data da situação: {e}")
                
                # Determina a data final para cálculos (pode ser a data atual)
                current_dt = datetime.datetime.now()
                if is_finished:
                    if end_date:
                        final_date = end_date
                    elif situation_date:
                        final_date = situation_date
                    else:
                        # Se não houver data de finalização, usa a data da última interação
                        if sorted_interactions:
                            final_date = sorted_interactions[-1].get('date')
                        else:
                            final_date = current_dt
                else:
                    final_date = current_dt
                
                if len(sorted_interactions) > 0:
                    # Inicializa com a primeira interação (ou criação do ticket)
                    last_dt = creation_dt
                    last_classification = 'C'  # Assumir que o ticket começa com o cliente
                    
                    # Processa todas as interações
                    for interaction in sorted_interactions:
                        current_dt = interaction.get('date')
                        current_classification = interaction.get('classification')
                        
                        # Calcula tempos
                        time_diff = (current_dt - last_dt).total_seconds()
                        business_time = calculator.calculate_business_time(last_dt, current_dt)
                        
                        # Atribui tempo com base na classificação anterior
                        if last_classification == 'C':
                            time_with_support += time_diff
                            business_time_with_support += business_time
                        elif last_classification == 'A':
                            time_with_client += time_diff
                            business_time_with_client += business_time
                        elif last_classification == 'B':
                            time_in_bug += time_diff
                            business_time_in_bug += business_time
                        elif last_classification == 'I':
                            time_ignored += time_diff
                            business_time_ignored += business_time
                        
                        # Atualiza para próxima iteração
                        last_dt = current_dt
                        last_classification = current_classification
                    
                    # Calcula o tempo entre a última interação e a data final
                    if last_dt < final_date:
                        # Tempo entre a última interação e a data final
                        time_diff = (final_date - last_dt).total_seconds()
                        business_time = calculator.calculate_business_time(last_dt, final_date)
                        
                        # Atribui tempo com base na classificação da última interação
                        if last_classification == 'C':
                            time_with_support += time_diff
                            business_time_with_support += business_time
                        elif last_classification == 'A':
                            time_with_client += time_diff
                            business_time_with_client += business_time
                        elif last_classification == 'B':
                            time_in_bug += time_diff
                            business_time_in_bug += business_time
                        elif last_classification == 'I':
                            time_ignored += time_diff
                            business_time_ignored += business_time
                
                # Atualiza o ticket com os valores calculados
                current_ticket['reclassified_time_with_client'] = time_with_client
                current_ticket['reclassified_time_with_support'] = time_with_support
                current_ticket['reclassified_time_in_bug'] = time_in_bug
                current_ticket['reclassified_time_ignored'] = time_ignored
                current_ticket['reclassified_business_time_with_client'] = business_time_with_client
                current_ticket['reclassified_business_time_with_support'] = business_time_with_support
                current_ticket['reclassified_business_time_in_bug'] = business_time_in_bug
                current_ticket['reclassified_business_time_ignored'] = business_time_ignored
                
                # Garantir que as alterações sejam refletidas no dicionário original
                self.tickets_data[self.current_ticket_index] = current_ticket
                
                # Marca que houve modificações
                self.modified = True
                
                # Atualiza a interface
                self.update_metrics_comparison()
            else:
                QMessageBox.warning(self, "Erro", "Calculadora de horário comercial não encontrada.")

    def export_to_csv(self):
        """Exporta dados reclassificados para CSV"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            try:
                # Obtém ticket atual
                ticket = self.tickets_data[self.current_ticket_index]
                
                # Cria dados para exportação
                data = []
                
                # Adiciona linha de cabeçalho para o ticket
                data.append([
                    "Análise de Ticket",
                    f"Protocolo: {ticket.get('protocol', '')}",
                    f"Assunto: {ticket.get('subject', '')}",
                    f"Cliente: {ticket.get('customer_name', '')}"
                ])
                
                # Adiciona linha em branco
                data.append([])
                
                # Adiciona métricas recalculadas
                data.append(["Métricas de Tempo", "Original", "Reclassificado", "Diferença"])
                
                # Função para formatar segundos
                def seconds_to_time_format_util(seconds):
                    """Converte segundos para formato HH:MM:SS"""
                    if seconds < 0:
                        prefix = "-"
                        seconds = abs(seconds)
                    else:
                        prefix = ""
                        
                    hours = int(seconds // 3600)
                    minutes = int((seconds % 3600) // 60)
                    secs = int(seconds % 60)
                    return f"{prefix}{hours:02d}:{minutes:02d}:{secs:02d}"

                # Adiciona cada métrica
                metrics = [
                    ("Tempo com Cliente", "time_with_client", "reclassified_time_with_client"),
                    ("Tempo com Suporte", "time_with_support", "reclassified_time_with_support"),
                    ("Tempo Comercial com Cliente", "business_time_with_client", "reclassified_business_time_with_client"),
                    ("Tempo Comercial com Suporte", "business_time_with_support", "reclassified_business_time_with_support"),
                    ("Tempo em Status de Bug", None, "reclassified_time_in_bug"),
                    ("Tempo Comercial em Status de Bug", None, "reclassified_business_time_in_bug"),
                    ("Tempo Ignorado", None, "reclassified_time_ignored"),
                    ("Tempo Comercial Ignorado", None, "reclassified_business_time_ignored")
                ]
                
                for label, orig_key, new_key in metrics:
                    orig_val = seconds_to_time_format_util(ticket.get(orig_key, 0)) if orig_key else ""
                    new_val = seconds_to_time_format_util(ticket.get(new_key, 0))
                    diff = ticket.get(new_key, 0) - ticket.get(orig_key, 0) if orig_key else ""
                    if diff != "":
                        diff = seconds_to_time_format_util(diff)
                    
                    data.append([label, orig_val, new_val, diff])
                
                # Adiciona linha em branco
                data.append([])
                
                # Adiciona pares de interações
                data.append(["Detalhes dos Intervalos"])
                data.append(["De (Data/Hora)", "Para (Data/Hora)", "Tempo Decorrido", "Tempo Comercial", "Atribuído a", "Classificação"])
                
                interactions = [i for i in ticket.get('interactions', []) if i.get('date')]
                interactions.sort(key=lambda x: x.get('date'))
                
                # Obtém o calculador de horas comerciais
                calculator = None
                parent = self.parent()
                
                if hasattr(parent, 'calculator'):
                    calculator = parent.calculator
                elif hasattr(parent, 'analyzer') and hasattr(parent.analyzer, 'calculator'):
                    calculator = parent.analyzer.calculator
                
                if calculator:
                    for i in range(len(interactions) - 1):
                        from_interaction = interactions[i]
                        to_interaction = interactions[i+1]
                        
                        # Calcular tempo entre as interações
                        time_diff = (to_interaction['date'] - from_interaction['date']).total_seconds()
                        business_time = calculator.calculate_business_time(from_interaction['date'], to_interaction['date'])
                        
                        # Determinar a quem este tempo é atribuído
                        current_classification = from_interaction.get('classification', from_interaction.get('sender_type', ''))
                        
                        if current_classification == 'C':
                            attributed_to = "Suporte"
                        elif current_classification == 'A':
                            attributed_to = "Cliente"
                        elif current_classification == 'B':
                            attributed_to = "Bug"
                        elif current_classification == 'I':
                            attributed_to = "Ignorado"
                        else:
                            attributed_to = "Desconhecido"
                        
                        # Formatar os tempos
                        time_diff_str = seconds_to_time_format_util(time_diff)
                        business_time_str = seconds_to_time_format_util(business_time)
                        
                        # Adicionar linha
                        data.append([
                            from_interaction['date'].strftime("%Y-%m-%d %H:%M:%S"),
                            to_interaction['date'].strftime("%Y-%m-%d %H:%M:%S"),
                            time_diff_str,
                            business_time_str,
                            attributed_to,
                            current_classification
                        ])
                
                # Adiciona linha em branco
                data.append([])
                
                # Adiciona todas as interações originais
                data.append(["Detalhes de Todas as Interações"])
                data.append(["Data/Hora", "Remetente", "Tipo Original", "Classificação Atual", "Status", "Prévia da Mensagem"])
                
                
                for interaction in sorted(ticket.get('interactions', []), key=lambda x: x.get('date') or datetime.datetime.min):
                    date_str = interaction.get('date').strftime("%Y-%m-%d %H:%M:%S") if interaction.get('date') else ""
                    sender = interaction.get('sender', '')
                    orig_type = interaction.get('sender_type', '')
                    curr_class = interaction.get('classification', '')
                    status = interaction.get('status', '')
                    
                    # Remover HTML para exibição na prévia
                    message = interaction.get('message', '')
                    preview = re.sub('<[^<]+?>', '', message)
                    preview = preview[:100] + "..." if len(preview) > 100 else preview
                    
                    data.append([date_str, sender, orig_type, curr_class, status, preview])
                
                # Solicita local para salvar o arquivo
                filename, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Salvar CSV", 
                    f"ticket_reclassificado_{ticket.get('protocol', '')}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                    "Arquivos CSV (*.csv)"
                )
                
                if filename:
                    # Cria arquivo CSV
                    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerows(data)
                        
                    QMessageBox.information(self, "Exportação Concluída", f"Dados exportados para {filename}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Erro na Exportação", str(e))

    def accept(self):
        """Sobrescreve o método accept para garantir que os dados estejam atualizados"""
        if not all(self.analyzed_tickets.values()):
            non_analyzed = [i for i, analyzed in self.analyzed_tickets.items() if not analyzed]
            
            tickets_text = ", ".join([f"{self.tickets_data[i].get('protocol', '')}" for i in non_analyzed[:3]])
            if len(non_analyzed) > 3:
                tickets_text += f" e mais {len(non_analyzed) - 3}"
                
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Tickets Não Analisados")
            msg.setText(f"Existem {len(non_analyzed)} tickets não analisados.")
            msg.setInformativeText(f"Por favor, marque todos os tickets como analisados antes de aplicar as alterações.\n\nTickets não analisados: {tickets_text}")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Ignore)
            msg.setDefaultButton(QMessageBox.Ok)
            
            result = msg.exec_()
            if result == QMessageBox.Ok:
                return  # Cancela o fechamento
        
        
        # Verifica se houve modificações
        if self.modified:
            # Verificação final dos dados
            for i, ticket in enumerate(self.tickets_data):
                print(f"Ticket {i}, tempo cliente: {ticket.get('reclassified_time_with_client', 0)/3600:.2f}h, "
                    f"tempo suporte: {ticket.get('reclassified_time_with_support', 0)/3600:.2f}h")
        
        # Chama o método da classe base para aceitar o diálogo
        super().accept()

    # Função de integração para o aplicativo principal
    def update_main_app_for_enhanced_classifier():
        """Atualiza o aplicativo principal para usar o classificador aprimorado"""
        
        # Substitui a função results_tab.analyze_selected para usar a nova versão do diálogo
        def new_analyze_selected(self):
            """Nova versão da função analyze_selected que usa o diálogo aprimorado"""
            selected_ids = self.get_selected_tickets()
            
            if not selected_ids:
                QMessageBox.warning(self, "Seleção Inválida", "Selecione pelo menos um ticket para analisar.")
                return
                
            # Create progress dialog
            progress = QMessageBox()
            progress.setWindowTitle("Processando")
            progress.setText("Analisando tickets, aguarde...")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.show()
            QApplication.processEvents()
            
            try:
                # Fetch details and analyze
                analysis_results = []
                
                for ticket_id in selected_ids:
                    # Get ticket details
                    print(f"Obtendo detalhes do ticket ID: {ticket_id}")
                    response = self.api_client.get_ticket_details(ticket_id)
                    
                    if not response.get('error', True):
                        # Analyze ticket data from response
                        ticket_data = response.get('data', {})
                        analysis = self.analyzer.analyze_ticket(ticket_data)
                        analysis_results.append(analysis)
                    else:
                        progress.close()
                        QMessageBox.warning(
                            self, 
                            "API Error", 
                            f"Erro ao obter detalhes do ticket {ticket_id}: {response.get('message', 'Erro desconhecido')}"
                        )
                        return
                        
                # Close progress
                progress.close()
                
                # If we have results to show
                if analysis_results:
                    # Ask what to do
                    dialog = QMessageBox()
                    dialog.setWindowTitle("Resultados da Análise")
                    dialog.setText("Análise concluída. O que você gostaria de fazer?")
                    dialog.addButton("Ver Resumo", QMessageBox.AcceptRole)
                    dialog.addButton("Classificar Interações", QMessageBox.ActionRole)
                    dialog.addButton("Cancelar", QMessageBox.RejectRole)
                    
                    action = dialog.exec_()
                    
                    if action == 0:  # View Summary
                        # Mostra o resumo com os dados originais
                        self.show_analysis_results(analysis_results)
                        
                    elif action == 1:  # Classify Interactions
                        # Abre o diálogo de classificação APRIMORADO em vez do original
                        classifier = InteractionClassifierDialogUpdated(analysis_results, self)
                        classifier_result = classifier.exec_()
                        
                        # Se o usuário clicou em Apply Changes
                        if classifier_result == QDialog.Accepted:
                            print("Dialog accepted, checking data before showing results:")
                            for i, ticket in enumerate(classifier.tickets_data):
                                print(f"Ticket {i}, client time: {ticket.get('reclassified_time_with_client', 0)/3600:.2f}h, "
                                    f"support time: {ticket.get('reclassified_time_with_support', 0)/3600:.2f}h")
                                
                                # Ajuste temporário para depuração - forçar valores diretamente nos dados originais
                                for key in ['time_with_client', 'time_with_support', 'business_time_with_client', 'business_time_with_support']:
                                    if f'reclassified_{key}' in ticket:
                                        ticket[key] = ticket[f'reclassified_{key}']
                            
                            # Usamos diretamente os dados da instância classifier
                            self.show_analysis_results(classifier.tickets_data)
                else:
                    QMessageBox.warning(self, "Sem Resultados", "Não foi possível analisar nenhum dos tickets selecionados.")
                    
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", str(e))
        
        # Retorna a função atualizada para ser usada no aplicativo principal
        return new_analyze_selected
    
    def show_help(self):
        """Exibe ajuda sobre as regras de cálculo"""
        help_dialog = QDialog(self)
        help_dialog.setWindowTitle("Ajuda - Cálculos de Tempo")
        help_dialog.setMinimumSize(700, 500)
        
        layout = QVBoxLayout()
        
        # Usar um scroll area para conteúdo extenso
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Título
        title = QLabel("Explicação dos Cálculos de Tempo com Cliente e Suporte")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        content_layout.addWidget(title)
        
        # Texto explicativo
        explanation = QLabel(
            "<h3>Visão Geral</h3>"
            "<p>Os cálculos de \"Tempo com Cliente\", \"Tempo com Suporte\", \"Tempo Comercial com Cliente\" e "
            "\"Tempo Comercial com Suporte\" são baseados na análise das interações (replies) no ticket. "
            "Essas métricas mostram quanto tempo o ticket passou \"com o cliente\" versus \"com a equipe de suporte\", "
            "considerando tanto o tempo total quanto apenas o tempo em horário comercial.</p>"
            
            "<h3>Método de Cálculo</h3>"
            "<p><b>Lógica Fundamental:</b></p>"
            "<ul>"
            "<li>A premissa básica é que o remetente atual determina com quem o ticket está agora</li>"
            "<li>O tempo entre duas interações é atribuído à parte que tinha o ticket no início desse período</li>"
            "</ul>"
            
            "<p><b>Passo a Passo:</b></p>"
            "<ol>"
            "<li><b>Ordenação das Interações:</b> Todas as interações (replies) são ordenadas cronologicamente por data</li>"
            "<li><b>Estado Inicial:</b>"
            "<ul>"
            "<li>Assumimos que o ticket começa \"com o cliente\" (após a criação do ticket)</li>"
            "<li>Definimos a data de criação do ticket como ponto de partida</li>"
            "<li>Definimos o último remetente como 'C' (cliente)</li>"
            "</ul></li>"
            "<li><b>Para cada interação sequencial:</b>"
            "<ul>"
            "<li>Obtemos a data da interação atual</li>"
            "<li>Identificamos o tipo de remetente ('C' para cliente, 'A' para atendente/suporte, 'B' para bug, 'I' para ignorado)</li>"
            "<li>Calculamos o tempo total entre a interação anterior e a atual</li>"
            "<li>Calculamos o tempo em horário comercial entre essas datas</li>"
            "</ul></li>"
            "<li><b>Atribuição do Tempo:</b>"
            "<ul>"
            "<li>Se o último remetente foi 'C' (cliente): O tempo foi gasto \"com o suporte\" (o suporte estava trabalhando no ticket)</li>"
            "<li>Se o último remetente foi 'A' (atendente): O tempo foi gasto \"com o cliente\" (o cliente estava analisando ou respondendo)</li>"
            "<li>Se o último remetente foi 'B' (bug): O tempo foi classificado como bug (problema no sistema)</li>"
            "<li>Se o último remetente foi 'I' (ignorado): O tempo não é contabilizado nas métricas principais</li>"
            "</ul></li>"
            "<li><b>Atualização para próxima iteração:</b>"
            "<ul>"
            "<li>Atualizamos a última data para a data atual</li>"
            "<li>Atualizamos o último remetente para o remetente atual</li>"
            "</ul></li>"
            "</ol>"
            
            "<h3>Exemplo Prático</h3>"
            "<p>Para um ticket com as seguintes interações:</p>"
            "<ul>"
            "<li>Criação do ticket pelo cliente (C) em 10/04/2023 às 09:00</li>"
            "<li>Primeira resposta do atendente (A) em 10/04/2023 às 11:00</li>"
            "<li>Resposta do cliente (C) em 11/04/2023 às 14:00</li>"
            "<li>Resposta final do atendente (A) em 11/04/2023 às 16:00</li>"
            "</ul>"
            
            "<p>O cálculo seria:</p>"
            "<ul>"
            "<li>Entre 09:00 e 11:00 (2h): Tempo com Suporte (último remetente era 'C')</li>"
            "<li>Entre 11:00 e 14:00 (3h): Tempo com Cliente (último remetente era 'A')</li>"
            "<li>Entre 14:00 e 16:00 (2h): Tempo com Suporte (último remetente era 'C')</li>"
            "</ul>"
            
            "<p>Resultando em:</p>"
            "<ul>"
            "<li>Tempo com Cliente: 3h (total)</li>"
            "<li>Tempo com Suporte: 4h (total)</li>"
            "</ul>"
            
            "<p>Para o cálculo de \"Tempo Comercial\", é aplicada a mesma lógica, mas considerando apenas as horas que caem dentro do horário comercial definido e excluindo feriados.</p>"
            
            "<h3>Diferença para os Cálculos de Status</h3>"
            "<p>É importante notar que este cálculo difere do \"Tempo em Status\", que mede o tempo gasto em cada status (como \"Em andamento\", \"Pausado\", etc.). O cálculo de tempo com cliente/suporte se concentra em quem está atuando no ticket, enquanto os status mostram em que etapa do processo o ticket se encontra.</p>"
        )
        
        explanation.setWordWrap(True)
        explanation.setTextFormat(Qt.RichText)
        content_layout.addWidget(explanation)
        
        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Botão de fechar
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(help_dialog.accept)
        layout.addWidget(close_btn)
        
        help_dialog.setLayout(layout)
        help_dialog.exec_()

def install_enhanced_classifier():
    """Instala o classificador aprimorado no aplicativo principal"""
    import sys
    
    # Obtém o módulo importador principal (ticket_analyzer)
    main_module = sys.modules['__main__']
    
    # Obtém a classe ResultsTab
    if hasattr(main_module, 'ResultsTab'):
        # Obtém a classe ResultsTab do módulo principal
        ResultsTab = main_module.ResultsTab
        
        # Guarda a função original para referência
        original_analyze_selected = ResultsTab.analyze_selected
        
        # Define a nova função
        def new_analyze_selected(self):
            """Nova versão da função analyze_selected que usa o diálogo aprimorado"""
            print("EXECUTANDO analyze_selected NOVA!")
            
            selected_ids = self.get_selected_tickets()
            
            if not selected_ids:
                QMessageBox.warning(self, "Seleção Inválida", "Selecione pelo menos um ticket para analisar.")
                return
                
            # Create progress dialog
            progress = QMessageBox()
            progress.setWindowTitle("Processando")
            progress.setText("Analisando tickets, aguarde...")
            progress.setStandardButtons(QMessageBox.NoButton)
            progress.show()
            QApplication.processEvents()
            
            try:
                # Fetch details and analyze
                analysis_results = []
                
                for ticket_id in selected_ids:
                    # Get ticket details
                    print(f"Obtendo detalhes do ticket ID: {ticket_id}")
                    response = self.api_client.get_ticket_details(ticket_id)
                    
                    if not response.get('error', True):
                        # Analyze ticket data from response
                        ticket_data = response.get('data', {})
                        analysis = self.analyzer.analyze_ticket(ticket_data)
                        analysis_results.append(analysis)
                    else:
                        progress.close()
                        QMessageBox.warning(
                            self, 
                            "API Error", 
                            f"Erro ao obter detalhes do ticket {ticket_id}: {response.get('message', 'Erro desconhecido')}"
                        )
                        return
                        
                # Close progress
                progress.close()
                
                # If we have results to show
                if analysis_results:
                    # Ask what to do
                    dialog = QMessageBox()
                    dialog.setWindowTitle("Resultados da Análise")
                    dialog.setText("Análise concluída. O que você gostaria de fazer?")
                    dialog.addButton("Ver Resumo", QMessageBox.AcceptRole)
                    dialog.addButton("Classificar Interações", QMessageBox.ActionRole)
                    dialog.addButton("Cancelar", QMessageBox.RejectRole)
                    
                    action = dialog.exec_()
                    
                    if action == 0:  # View Summary
                        # Mostra o resumo com os dados originais
                        self.show_analysis_results(analysis_results)
                        
                    elif action == 1:  # Classify Interactions
                        # Abre o diálogo de classificação APRIMORADO em vez do original
                        classifier = InteractionClassifierDialogUpdated(analysis_results, self)
                        classifier_result = classifier.exec_()
                        
                        # Se o usuário clicou em Apply Changes
                        if classifier_result == QDialog.Accepted:
                            print("Dialog accepted, checking data before showing results:")
                            for i, ticket in enumerate(classifier.tickets_data):
                                print(f"Ticket {i}, client time: {ticket.get('reclassified_time_with_client', 0)/3600:.2f}h, "
                                    f"support time: {ticket.get('reclassified_time_with_support', 0)/3600:.2f}h")
                                
                                # Ajuste temporário para depuração - forçar valores diretamente nos dados originais
                                for key in ['time_with_client', 'time_with_support', 'business_time_with_client', 'business_time_with_support']:
                                    if f'reclassified_{key}' in ticket:
                                        ticket[key] = ticket[f'reclassified_{key}']
                            
                            # Usamos diretamente os dados da instância classifier
                            self.show_analysis_results(classifier.tickets_data)
                else:
                    QMessageBox.warning(self, "Sem Resultados", "Não foi possível analisar nenhum dos tickets selecionados.")
                    
            except Exception as e:
                progress.close()
                QMessageBox.critical(self, "Error", str(e))
        
        # Substitui o método na classe (isso afeta todas as instâncias)
        ResultsTab.analyze_selected = new_analyze_selected
        
        print("Método ResultsTab.analyze_selected substituído com sucesso!")
    else:
        print("ERRO: Não foi possível encontrar a classe ResultsTab no módulo principal!")
        
        
class TimeCalculatorDialog(QDialog):
    """Diálogo para calcular diferença de tempo entre duas datas, considerando horário comercial,
    com capacidade de acumular múltiplos resultados"""
    
    def __init__(self, calculator, parent=None):
        super().__init__(parent)
        self.calculator = calculator
        self.setWindowTitle("Calculadora de Horário Comercial")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(500)
        
        # Valores acumulados em segundos
        self.total_accumulated = 0
        self.business_total_accumulated = 0
        
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Data/hora inicial
        self.start_datetime = QLineEdit()
        self.start_datetime.setPlaceholderText("AAAA-MM-DD HH:MM:SS")
        form_layout.addRow("Data/Hora Inicial:", self.start_datetime)
        
        # Data/hora final
        self.end_datetime = QLineEdit()
        self.end_datetime.setPlaceholderText("AAAA-MM-DD HH:MM:SS")
        form_layout.addRow("Data/Hora Final:", self.end_datetime)
        
        # Botão calcular
        calculate_btn = QPushButton("Calcular")
        calculate_btn.clicked.connect(self.calculate_time_diff)
        form_layout.addRow("", calculate_btn)
        
        # Resultados
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout()
        
        # Resultado de tempo normal
        result_layout = QHBoxLayout()
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-weight: bold; color: blue;")
        result_layout.addWidget(QLabel("Diferença de Tempo:"))
        result_layout.addWidget(self.result_label)
        result_layout.addStretch()
        
        # Botão para acumular tempo normal
        self.accumulate_btn = QPushButton("Acumular")
        self.accumulate_btn.setEnabled(False)  # Desativado até ter um resultado
        self.accumulate_btn.clicked.connect(lambda: self.accumulate_time("normal"))
        result_layout.addWidget(self.accumulate_btn)
        
        results_layout.addLayout(result_layout)
        
        # Resultado de horário comercial
        business_layout = QHBoxLayout()
        self.business_result_label = QLabel("")
        self.business_result_label.setStyleSheet("font-weight: bold; color: green;")
        business_layout.addWidget(QLabel("Tempo em Horário Comercial:"))
        business_layout.addWidget(self.business_result_label)
        business_layout.addStretch()
        
        # Botão para acumular tempo comercial
        self.business_accumulate_btn = QPushButton("Acumular")
        self.business_accumulate_btn.setEnabled(False)  # Desativado até ter um resultado
        self.business_accumulate_btn.clicked.connect(lambda: self.accumulate_time("comercial"))
        business_layout.addWidget(self.business_accumulate_btn)
        
        results_layout.addLayout(business_layout)
        
        results_group.setLayout(results_layout)
        
        # Grupo de resultados acumulados
        accumulated_group = QGroupBox("Tempo Acumulado")
        accumulated_layout = QVBoxLayout()
        
        # Tempo normal acumulado
        total_layout = QHBoxLayout()
        self.total_label = QLabel("00:00:00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: blue;")
        total_layout.addWidget(QLabel("Tempo Total:"))
        total_layout.addWidget(self.total_label)
        total_layout.addStretch()
        
        # Botão para resetar tempo normal
        reset_btn = QPushButton("Zerar")
        reset_btn.clicked.connect(lambda: self.reset_accumulated("normal"))
        total_layout.addWidget(reset_btn)
        
        accumulated_layout.addLayout(total_layout)
        
        # Tempo comercial acumulado
        business_total_layout = QHBoxLayout()
        self.business_total_label = QLabel("00:00:00")
        self.business_total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: green;")
        business_total_layout.addWidget(QLabel("Tempo Comercial Total:"))
        business_total_layout.addWidget(self.business_total_label)
        business_total_layout.addStretch()
        
        # Botão para resetar tempo comercial
        business_reset_btn = QPushButton("Zerar")
        business_reset_btn.clicked.connect(lambda: self.reset_accumulated("comercial"))
        business_total_layout.addWidget(business_reset_btn)
        
        accumulated_layout.addLayout(business_total_layout)
        
        # Botão para resetar tudo
        reset_all_layout = QHBoxLayout()
        reset_all_layout.addStretch()
        reset_all_btn = QPushButton("Zerar Tudo")
        reset_all_btn.clicked.connect(lambda: self.reset_accumulated("tudo"))
        reset_all_btn.setStyleSheet("background-color: #ffdddd;")
        reset_all_layout.addWidget(reset_all_btn)
        
        accumulated_layout.addLayout(reset_all_layout)
        
        accumulated_group.setLayout(accumulated_layout)
        
        # Adiciona tudo ao layout principal
        layout.addLayout(form_layout)
        layout.addWidget(results_group)
        layout.addWidget(accumulated_group)
        
        self.setLayout(layout)
        
    def calculate_time_diff(self):
        """Calcula a diferença de tempo entre as datas/horas inicial e final"""
        try:
            # Analisa as datas de entrada
            start_str = self.start_datetime.text().strip()
            end_str = self.end_datetime.text().strip()
            
            # Tenta analisar com diferentes formatos
            try:
                start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                start_dt = datetime.datetime.strptime(start_str, "%Y-%m-%d %H:%M")
                
            try:
                end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                end_dt = datetime.datetime.strptime(end_str, "%Y-%m-%d %H:%M")
            
            # Calcula diferença de tempo normal
            self.time_diff = (end_dt - start_dt).total_seconds()
            
            # Calcula diferença de horário comercial
            self.business_time = self.calculator.calculate_business_time(start_dt, end_dt)
            
            # Converte segundos para formato HH:MM:SS
            time_diff_str = self.seconds_to_time_format(self.time_diff)
            business_time_str = self.seconds_to_time_format(self.business_time)
            
            # Atualiza labels de resultado
            self.result_label.setText(time_diff_str)
            self.business_result_label.setText(business_time_str)
            
            # Ativa botões de acumular
            self.accumulate_btn.setEnabled(True)
            self.business_accumulate_btn.setEnabled(True)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao calcular diferença de tempo: {str(e)}")
            self.accumulate_btn.setEnabled(False)
            self.business_accumulate_btn.setEnabled(False)
    
    def accumulate_time(self, time_type):
        """Acumula o tempo calculado no total"""
        if time_type == "normal":
            self.total_accumulated += self.time_diff
            self.total_label.setText(self.seconds_to_time_format(self.total_accumulated))
        elif time_type == "comercial":
            self.business_total_accumulated += self.business_time
            self.business_total_label.setText(self.seconds_to_time_format(self.business_total_accumulated))
            
        # Fornece feedback visual que o tempo foi acumulado
        flash_button = self.accumulate_btn if time_type == "normal" else self.business_accumulate_btn
        original_style = flash_button.styleSheet()
        flash_button.setStyleSheet("background-color: #aaffaa;")
        
        # Restaura o estilo do botão após um curto atraso
        QTimer.singleShot(300, lambda: flash_button.setStyleSheet(original_style))
    
    def reset_accumulated(self, time_type):
        """Reseta o tempo acumulado"""
        if time_type in ["normal", "tudo"]:
            self.total_accumulated = 0
            self.total_label.setText("00:00:00")
            
        if time_type in ["comercial", "tudo"]:
            self.business_total_accumulated = 0
            self.business_total_label.setText("00:00:00")
    
    def seconds_to_time_format(self, seconds):
        """Converte segundos para formato HH:MM:SS"""
        if seconds < 0:
            prefix = "-"
            seconds = abs(seconds)
        else:
            prefix = ""
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{prefix}{hours:02d}:{minutes:02d}:{secs:02d}"