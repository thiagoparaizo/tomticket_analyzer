import csv
import re
import sys
import os
import json
import configparser
import datetime
import pandas as pd
import requests
from dateutil import parser
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QComboBox, QDateEdit, 
                            QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
                            QCheckBox, QMessageBox, QGroupBox, QFormLayout, QSpinBox,
                            QTimeEdit, QDialog, QScrollArea, QFileDialog, QGridLayout, QTextEdit, QSplitter, QFrame )
from PyQt5.QtCore import Qt, QDate, QTime, QDateTime, QSize
from PyQt5.QtCore import QTimer, QPropertyAnimation
from PyQt5.QtGui import QColor, QIcon, QCursor, QPixmap

from enhanced_classifier import (
    InteractionPairTableView,
    InteractionPairDetailsDialog, 
    InteractionClassifierDialogUpdated,
    install_enhanced_classifier
)

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


class InteractionClassifierDialog(QDialog):
    """Diálogo para classificação manual de interações de tickets"""
    
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
        
        ticket_selector_layout = QHBoxLayout()
        ticket_selector_layout.addWidget(QLabel("Selecionar Ticket:"))
        self.ticket_selector = QComboBox()
        # Preenche o combobox com os tickets disponíveis
        for i, ticket in enumerate(self.tickets_data):
            self.ticket_selector.addItem(f"{ticket.get('protocol', '')} - {ticket.get('subject', '')}", i)
        self.ticket_selector.currentIndexChanged.connect(self.on_ticket_changed)
        ticket_selector_layout.addWidget(self.ticket_selector)
        
        top_layout.addLayout(ticket_selector_layout)
        top_layout.addStretch()
        
        # Botões de recálculo e exportação
        recalculate_btn = QPushButton("Recalcular Tempos")
        recalculate_btn.clicked.connect(self.recalculate_times)
        top_layout.addWidget(recalculate_btn)
        
        reset_btn = QPushButton("Resetar Classificações")
        reset_btn.clicked.connect(self.reset_classifications)
        
        export_btn = QPushButton("Exportar para CSV")
        export_btn.clicked.connect(self.export_to_csv)
        top_layout.addWidget(export_btn)
        
        
        
        layout.addLayout(top_layout)
        
        # Seção do meio - Visão dividida com tabela de interações e visualização de mensagem
        middle_layout = QSplitter(Qt.Horizontal)
        
        # Tabela de interações
        interaction_group = QGroupBox("Interações")
        interaction_layout = QVBoxLayout()
        
        # Filtros
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
        
        interaction_layout.addLayout(filter_layout)
        
        # Tabela principal de interações
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
        
        interaction_layout.addWidget(self.interaction_table)
        
        # Botões de classificação
        classify_layout = QHBoxLayout()
        classify_layout.addWidget(reset_btn)
        
        classify_as_client_btn = QPushButton("Atribuir tempo p/ Suporte (C)")
        classify_as_client_btn.clicked.connect(lambda: self.classify_selected("C"))
        classify_layout.addWidget(classify_as_client_btn)
        
        classify_as_support_btn = QPushButton("Atribuir tempo p/ Cliente (A)")
        classify_as_support_btn.clicked.connect(lambda: self.classify_selected("A"))
        classify_layout.addWidget(classify_as_support_btn)
        
        classify_as_bug_btn = QPushButton("Classificar como Bug (B)")
        classify_as_bug_btn.clicked.connect(lambda: self.classify_selected("B"))
        classify_layout.addWidget(classify_as_bug_btn)
        
        classify_as_ignore_btn = QPushButton("Ignorar (I)")
        classify_as_ignore_btn.clicked.connect(lambda: self.classify_selected("I"))
        classify_layout.addWidget(classify_as_ignore_btn)
        
        reset_btn = QPushButton("Resetar para Original")
        reset_btn.clicked.connect(self.reset_classifications)
        classify_layout.addWidget(reset_btn)
        
        interaction_layout.addLayout(classify_layout)
        
        interaction_group.setLayout(interaction_layout)
        
        # Visualizador de mensagem
        message_group = QGroupBox("Conteúdo da Mensagem")
        message_layout = QVBoxLayout()
        
        self.message_display = QTextEdit()
        self.message_display.setReadOnly(True)
        message_layout.addWidget(self.message_display)
        
        message_group.setLayout(message_layout)
        
        # Adiciona os dois painéis ao splitter
        left_widget = QWidget()
        left_widget.setLayout(interaction_layout)
        middle_layout.addWidget(left_widget)
        middle_layout.addWidget(message_group)
        
        # Define proporções iniciais
        middle_layout.setSizes([600, 400])
        
        layout.addWidget(middle_layout)
        
        # Seção inferior - Comparação de métricas de tempo
        metrics_group = QGroupBox("Comparação de Métricas de Tempo")
        metrics_layout = QGridLayout()
        
        # Cabeçalhos
        metrics_layout.addWidget(QLabel("Métrica"), 0, 0)
        metrics_layout.addWidget(QLabel("Original"), 0, 1)
        metrics_layout.addWidget(QLabel("Reclassificado"), 0, 2)
        metrics_layout.addWidget(QLabel("Diferença"), 0, 3)
        
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
        
        for row, (label, orig_key, new_key) in enumerate(metrics, 1):
            metrics_layout.addWidget(QLabel(label), row, 0)
            
            # Valor original
            self.metric_labels[f"{orig_key}_orig"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{orig_key}_orig"], row, 1)
            
            # Novo valor
            self.metric_labels[f"{new_key}_new"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{new_key}_new"], row, 2)
            
            # Diferença
            self.metric_labels[f"{new_key}_diff"] = QLabel("00:00:00")
            metrics_layout.addWidget(self.metric_labels[f"{new_key}_diff"], row, 3)
        
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
        
    def on_ticket_changed(self, index):
        """Lida com mudança na seleção de ticket"""
        if index >= 0:
            self.current_ticket_index = self.ticket_selector.currentData()
            self.load_current_ticket()
            
    def load_current_ticket(self):
        """Carrega os dados do ticket atualmente selecionado"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            
            
            
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
            
            # Limpa a tabela
            self.interaction_table.setRowCount(0)
            
            # Adiciona interações à tabela
            interactions = ticket.get('interactions', [])
            
            if interactions:
                self.update_interaction_table()
                
            # Atualiza métricas
            self.update_metrics_comparison()
            
    def reset_classifications(self):
        """Reseta todas as classificações para seus valores originais"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            interactions = ticket.get('interactions', [])
            
            # Reset each interaction's classification to its original type
            modified = False
            # Reset each interaction's classification to its original type
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
                
                # Update the UI
                self.update_interaction_table()
                self.update_metrics_comparison()
                
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
        
        # Atualiza a tabela
        self.update_interaction_table()
        
    def apply_filters(self):
        """Aplica filtros à tabela de interações"""
        self.update_interaction_table()
        
    def clear_filters(self):
        """Limpa todos os filtros"""
        self.filter_type.setCurrentIndex(0)
        self.filter_status.clear()
        self.category.setCurrentIndex(0)  # "Todas"
        
    def update_metrics_comparison(self):
        """Atualiza a seção de comparação de métricas"""
        if 0 <= self.current_ticket_index < len(self.tickets_data):
            ticket = self.tickets_data[self.current_ticket_index]
            
            # Função auxiliar para formatar segundos como HH:MM:SS
            def format_time(seconds):
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
                
            # Função para calcular diferença
            def calc_diff(new_val, old_val):
                try:
                    new_val = float(new_val or 0)
                    old_val = float(old_val or 0)
                    return new_val - old_val
                except (ValueError, TypeError):
                    return 0
            
            # Atualiza as métricas
            metrics = [
                ("time_with_client", "reclassified_time_with_client"),
                ("time_with_support", "reclassified_time_with_support"),
                ("business_time_with_client", "reclassified_business_time_with_client"),
                ("business_time_with_support", "reclassified_business_time_with_support"),
                (None, "reclassified_time_in_bug"),
                (None, "reclassified_business_time_in_bug"),
                (None, "reclassified_time_ignored"),
                (None, "reclassified_business_time_ignored") 
            ]
            
            for orig_key, new_key in metrics:
                # Original
                if orig_key:
                    orig_val = ticket.get(orig_key, 0)
                    formatted_orig = format_time(orig_val)
                    self.metric_labels[f"{orig_key}_orig"].setText(formatted_orig)
                
                # Reclassificado
                new_val = ticket.get(new_key, 0)
                formatted_new = format_time(new_val)
                self.metric_labels[f"{new_key}_new"].setText(formatted_new)
                
                # Diferença
                if orig_key:
                    diff = calc_diff(new_val, ticket.get(orig_key, 0))
                    
                    # Formata a diferença
                    if diff == 0:
                        diff_text = "00:00:00"
                    else:
                        diff_abs = format_time(abs(diff))
                        diff_text = f"{'+' if diff > 0 else '-'}{diff_abs}"
                    
                    self.metric_labels[f"{new_key}_diff"].setText(diff_text)
                    
                    # Destaca diferenças
                    if diff < 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: red;")
                    elif diff > 0:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("color: green;")
                    else:
                        self.metric_labels[f"{new_key}_diff"].setStyleSheet("")
                
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
                def format_time_hours(seconds):
                    if seconds is None:
                        return 0
                    return round(seconds / 3600, 2)  # Converte para horas com 2 casas decimais

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
                    ("Tempo com Cliente (h)", "time_with_client", "reclassified_time_with_client"),
                    ("Tempo com Suporte (h)", "time_with_support", "reclassified_time_with_support"),
                    ("Tempo Comercial com Cliente (h)", "business_time_with_client", "reclassified_business_time_with_client"),
                    ("Tempo Comercial com Suporte (h)", "business_time_with_support", "reclassified_business_time_with_support"),
                    ("Tempo em Status de Bug (h)", None, "reclassified_time_in_bug"),
                    ("Tempo Comercial em Status de Bug (h)", None, "reclassified_business_time_in_bug")
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
                
                # Adiciona todas as interações
                data.append(["Detalhes das Interações"])
                data.append(["Data/Hora", "Remetente", "Tipo Original", "Classificação Atual", "Status", "Prévia da Mensagem"])
                
                for interaction in ticket.get('interactions', []):
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
                    
                print(f"Status do ticket: {'Finalizado' if is_finished else 'Em Andamento'}")
                print(f"Data final para cálculos: {final_date}")
                
                if len(sorted_interactions) > 0:
                    # Inicializa com a primeira interação (ou criação do ticket)
                    last_dt = creation_dt
                    last_classification = 'C'  # Assumir que o ticket começa com o cliente
                    
                    print(f"Iniciando com: Data={last_dt}, Classificação={last_classification}")
                    
                    # Processa todas as interações
                    for interaction in sorted_interactions:
                        current_dt = interaction.get('date')
                        current_classification = interaction.get('classification')
                        
                        if interaction.get('id','') == 'creation' and len(sorted_interactions) > 1:
                            prox_iteraction = sorted_interactions[1]
                            current_dt = prox_iteraction.get('date')
                        
                        # Calcula tempos
                        time_diff = (current_dt - last_dt).total_seconds()
                        business_time = calculator.calculate_business_time(last_dt, current_dt)
                        
                        print(f"\nInteração em {current_dt}")
                        print(f"Classificação: {current_classification}")
                        print(f"Última classificação: {last_classification}")
                        print(f"Diferença de tempo: {time_diff:.2f} segundos ({time_diff/3600:.2f} horas)")
                        print(f"Tempo comercial: {business_time:.2f} segundos ({business_time/3600:.2f} horas)")
                        
                        # Atribui tempo com base na classificação anterior
                        if current_classification == 'I':
                            # Se a interação atual é ignorada, atribui o tempo à categoria ignorada
                            time_ignored += time_diff
                            business_time_ignored += business_time
                            print(f"Tempo atribuído a IGNORADO")
                            
                            # Não atualiza last_classification para manter a classificação anterior
                            # mas atualiza last_dt para não perder o intervalo de tempo
                            last_dt = current_dt
                            
                            # Continua para a próxima interação sem mudar last_classification
                            continue
                        if last_classification == 'C':
                            time_with_support += time_diff
                            business_time_with_support += business_time
                            print(f"Tempo atribuído a SUPORTE")
                        elif last_classification == 'A':
                            time_with_client += time_diff
                            business_time_with_client += business_time
                            print(f"Tempo atribuído a CLIENTE")
                        elif last_classification == 'B':
                            time_in_bug += time_diff
                            business_time_in_bug += business_time
                            print(f"Tempo atribuído a BUG")
                        
                        # Atualiza para próxima iteração
                        last_dt = current_dt
                        last_classification = current_classification
                    
                    # Calcula o tempo entre a última interação e a data final
                    if last_dt < final_date:
                        # Tempo entre a última interação e a data final
                        time_diff = (final_date - last_dt).total_seconds()
                        business_time = calculator.calculate_business_time(last_dt, final_date)
                        
                        print(f"\nTempo entre última interação e data final:")
                        print(f"Última interação: {last_dt}")
                        print(f"Data final: {final_date}")
                        print(f"Última classificação: {last_classification}")
                        print(f"Diferença de tempo: {time_diff:.2f} segundos ({time_diff/3600:.2f} horas)")
                        print(f"Tempo comercial: {business_time:.2f} segundos ({business_time/3600:.2f} horas)")
                        
                        # Atribui tempo com base na classificação da última interação
                        if last_classification == 'C':
                            time_with_support += time_diff
                            business_time_with_support += business_time
                            print(f"Tempo atribuído a SUPORTE")
                        elif last_classification == 'A':
                            time_with_client += time_diff
                            business_time_with_client += business_time
                            print(f"Tempo atribuído a CLIENTE")
                        elif last_classification == 'B':
                            time_in_bug += time_diff
                            business_time_in_bug += business_time
                            print(f"Tempo atribuído a BUG")
                
                # Imprime totais
                print("\nTotais finais:")
                print(f"Tempo com cliente: {time_with_client/3600:.2f} horas")
                print(f"Tempo com suporte: {time_with_support/3600:.2f} horas")
                print(f"Tempo em bug: {time_in_bug/3600:.2f} horas")
                print(f"Tempo ignorado: {time_ignored  /3600:.2f} horas")
                print(f"Tempo comercial com cliente: {business_time_with_client/3600:.2f} horas")
                print(f"Tempo comercial com suporte: {business_time_with_support/3600:.2f} horas")
                print(f"Tempo comercial em bug: {business_time_in_bug/3600:.2f} horas")
                print(f"Tempo comercial ignorado: {business_time_ignored  /3600:.2f} horas")
                
                
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
                
                print("Após recálculo, valores em tickets_data:")
                print(f"Tempo com cliente: {self.tickets_data[self.current_ticket_index]['reclassified_time_with_client']/3600:.2f} horas")
                print(f"Tempo com suporte: {self.tickets_data[self.current_ticket_index]['reclassified_time_with_support']/3600:.2f} horas")
                
                # Atualiza a interface
                self.update_metrics_comparison()
                
                QMessageBox.information(self, "Recálculo", "As métricas de tempo foram recalculadas com base nas classificações atuais.")
            else:
                QMessageBox.warning(self, "Erro", "Calculadora de horário comercial não encontrada.")
    
    def accept(self):
        """Sobrescreve o método accept para garantir que os dados estejam atualizados"""
        # Verifica se houve modificações
        if self.modified:
            print("Dialog accept - modified data detected")
            # Verificação final dos dados
            for i, ticket in enumerate(self.tickets_data):
                print(f"Ticket {i}, tempo cliente: {ticket.get('reclassified_time_with_client', 0)/3600:.2f}h, "
                    f"tempo suporte: {ticket.get('reclassified_time_with_support', 0)/3600:.2f}h")
        
        # Chama o método da classe base para aceitar o diálogo
        super().accept()    

class ConfigManager:
    """Gerencia a persistência da configuração da aplicação"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.expanduser("~"), ".ticket_analyzer_config.ini")
        self.config = configparser.ConfigParser()
        self.load_config()
    
    def load_config(self):
        """Carrega configuração do arquivo se ele existir"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            # Inicializa com seções padrão
            self.config['API'] = {'token': ''}
            self.config['BusinessHours'] = {
                'monday': '08:00-12:00,14:00-18:00',
                'tuesday': '08:00-12:00,14:00-18:00',
                'wednesday': '08:00-12:00,14:00-18:00',
                'thursday': '08:00-12:00,14:00-18:00',
                'friday': '08:00-12:00,14:00-18:00',
                'saturday': '',
                'sunday': ''
            }
            self.save_config()
    
    def save_config(self):
        """Salva configuração no arquivo"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
    
    def get_api_token(self):
        """Obtém o token da API"""
        return self.config['API'].get('token', '')
    
    def set_api_token(self, token):
        """Define o token da API"""
        self.config['API']['token'] = token
        self.save_config()
    
    def get_business_hours(self):
        """Obtém configuração de horário comercial"""
        return dict(self.config['BusinessHours'])
    
    def set_business_hours(self, day, hours):
        """Define horário comercial para um dia específico"""
        self.config['BusinessHours'][day] = hours
        self.save_config()
        
    def get_holidays(self):
        """Obtém lista de feriados"""
        if 'Holidays' not in self.config:
            self.config['Holidays'] = {}
        
        holidays = []
        for date_str, description in self.config['Holidays'].items():
            try:
                date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                holidays.append((date, description))
            except ValueError:
                pass  # Ignora datas inválidas
        
        return sorted(holidays, key=lambda x: x[0])  # Ordena por data

    def add_holiday(self, date, description):
        """Adiciona um feriado"""
        if 'Holidays' not in self.config:
            self.config['Holidays'] = {}
            
        date_str = date.strftime("%Y-%m-%d")
        self.config['Holidays'][date_str] = description
        self.save_config()
        
    def remove_holiday(self, date):
        """Remove um feriado"""
        if 'Holidays' not in self.config:
            return
            
        date_str = date.strftime("%Y-%m-%d")
        if date_str in self.config['Holidays']:
            del self.config['Holidays'][date_str]
            self.save_config()


class ApiClient:
    """Gerencia comunicação com a API do TomTicket"""
    
    BASE_URL = "https://api.tomticket.com/v2.0"
    
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Bearer {token}'
        }
    
    def list_tickets(self, params):
        """Obtém lista de tickets com base nos parâmetros de filtro"""
        endpoint = f"{self.BASE_URL}/ticket/list"
        print("Enviando parâmetros:", params)
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Erro na API: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Falha na chamada da API list_tickets: {str(e)}")
    
    def get_ticket_details(self, ticket_id):
        """Obtém informações detalhadas sobre um ticket específico"""
        endpoint = f"{self.BASE_URL}/ticket/detail"
        
        # Parâmetros para a requisição GET
        params = {'ticket_id': ticket_id}
        
        try:
            # Imprimir informações para debug
            print(f"Chamando API: {endpoint}")
            print(f"Headers: {self.headers}")
            print(f"Parâmetros: {params}")
            
            # Usar GET em vez de POST
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            print(f"Resposta: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                # Check for valid data structure
                if not result.get('error', True) and result.get('data'):
                    return result
                else:
                    raise Exception(f"Erro na resposta da API: {result.get('message', 'Erro desconhecido')}")
            else:
                raise Exception(f"Erro na API: {response.status_code} - {response.text}")
        except Exception as e:
            raise Exception(f"Falha na chamada da API: {e}, endpoint = {endpoint}, params = {params}")


class BusinessHoursCalculator:
    """Calcula tempo de trabalho com base no horário comercial, excluindo feriados"""
    
    def __init__(self, business_hours_config, holidays=None):
        self.business_hours = self._parse_business_hours(business_hours_config)
        self.holidays = set(date for date, _ in (holidays or []))  # Conjunto de datas de feriados
        
    def _parse_business_hours(self, config):
        """Analisa horário comercial de formato string para dados estruturados"""
        business_hours = {}
        days_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day, hours_str in config.items():
            day_index = days_map.get(day.lower())
            if day_index is None:
                continue
                
            ranges = []
            if hours_str:
                for time_range in hours_str.split(','):
                    if '-' in time_range:
                        start, end = time_range.split('-')
                        start_h, start_m = map(int, start.split(':'))
                        end_h, end_m = map(int, end.split(':'))
                        ranges.append((
                            datetime.time(start_h, start_m),
                            datetime.time(end_h, end_m)
                        ))
            
            business_hours[day_index] = ranges
            
        return business_hours
    
    def is_business_hours(self, dt):
        """Verifica se um datetime está dentro do horário comercial e não é feriado"""
        # Verifica se a data é feriado
        if dt.date() in self.holidays:
            return False
            
        # Verifica horário comercial
        day_of_week = dt.weekday()
        time_ranges = self.business_hours.get(day_of_week, [])
        
        if not time_ranges:
            return False
            
        current_time = dt.time()
        return any(start <= current_time <= end for start, end in time_ranges)
    
    def calculate_business_time(self, start_dt, end_dt):
        """Calcula tempo comercial entre dois datetimes em segundos, excluindo feriados"""
        if start_dt >= end_dt:
            return 0
            
        # Inicializa variáveis
        current_dt = start_dt
        total_seconds = 0
        
        # Itera através de cada dia
        while current_dt.date() <= end_dt.date():
            # Pula se for feriado
            if current_dt.date() in self.holidays:
                current_dt = datetime.datetime.combine(
                    current_dt.date() + datetime.timedelta(days=1),
                    datetime.time(0, 0)
                )
                continue
                
            day_ranges = self.business_hours.get(current_dt.weekday(), [])
            
            if not day_ranges:
                # Sem horário comercial para este dia
                current_dt = datetime.datetime.combine(
                    current_dt.date() + datetime.timedelta(days=1),
                    datetime.time(0, 0)
                )
                continue
                
            for start_time, end_time in day_ranges:
                range_start = datetime.datetime.combine(current_dt.date(), start_time)
                range_end = datetime.datetime.combine(current_dt.date(), end_time)
                
                # Pula se o intervalo estiver completamente antes de start_dt ou depois de end_dt
                if range_end <= start_dt or range_start >= end_dt:
                    continue
                    
                # Ajusta intervalo se sobrepor com start_dt ou end_dt
                calc_start = max(range_start, start_dt)
                calc_end = min(range_end, end_dt)
                
                # Adiciona segundos neste intervalo
                total_seconds += (calc_end - calc_start).total_seconds()
            
            # Move para o próximo dia
            current_dt = datetime.datetime.combine(
                current_dt.date() + datetime.timedelta(days=1),
                datetime.time(0, 0))
            
        return total_seconds

def recalculate_times(self):
    """Recalcula métricas de tempo com base nas classificações atuais"""
    current_ticket = self.tickets_data[self.current_ticket_index]
    interactions = current_ticket['interactions']
    
    # Inicializa métricas
    time_with_client = 0
    time_with_support = 0
    time_in_bug = 0  # Nova métrica
    business_time_with_client = 0
    business_time_with_support = 0
    business_time_in_bug = 0  # Nova métrica
    
    # Filtra interações ignoradas antes de ordenar
    valid_interactions = [i for i in interactions if i.get('classification') != 'I' and i.get('date')]
    # Ordena interações por data
    sorted_interactions = sorted(valid_interactions, key=lambda x: x.get('date'))
    
    # Inicializa com a primeira interação
    if sorted_interactions:
        creation_dt = self.parse_datetime(current_ticket['creation_date'])
        last_dt = creation_dt
        # Assume que o ticket começa com o cliente
        last_classification = 'C'
        
        for interaction in sorted_interactions:
            # if interaction.get('classification') == 'I':  # Ignorar
            #     continue
                
            current_dt = interaction['date']
            current_classification = interaction['classification']
            
            # if not current_dt:
            #     continue
                
            # Calcula tempos
            time_diff = (current_dt - last_dt).total_seconds()
            business_time = self.calculator.calculate_business_time(last_dt, current_dt)
            
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
                
            # Atualiza para próxima iteração
            last_dt = current_dt
            last_classification = current_classification
    
    # Atualiza resultados
    current_ticket['reclassified_time_with_client'] = time_with_client
    current_ticket['reclassified_time_with_support'] = time_with_support
    current_ticket['reclassified_time_in_bug'] = time_in_bug
    current_ticket['reclassified_business_time_with_client'] = business_time_with_client
    current_ticket['reclassified_business_time_with_support'] = business_time_with_support
    current_ticket['reclassified_business_time_in_bug'] = business_time_in_bug
    
    # Atualiza a interface
    self.update_metrics_comparison()
    
def classify_interaction(self, interaction_index, new_classification):
    """Atualiza a classificação de uma interação"""
    current_ticket = self.tickets_data[self.current_ticket_index]
    if 0 <= interaction_index < len(current_ticket['interactions']):
        # Atualizar classificação
        current_ticket['interactions'][interaction_index]['classification'] = new_classification
        self.modified = True
        
        # Atualizar a visualização
        self.update_interaction_table()
        
        # Recalcular tempos (opcional - pode ser feito apenas quando solicitado)
        self.recalculate_times()


class TicketAnalyzer:
    """Analisa dados de tickets e calcula métricas de tempo"""
    
    def __init__(self, business_hours_calculator):
        self.calculator = business_hours_calculator
    
    def parse_datetime(self, datetime_str):
        """Analisa string de datetime da API e retorna no formato %Y-%m-%d %H:%M:%S (sem fuso e sem milissegundos)."""
        if not datetime_str:
            return None
        try:
            dt = parser.parse(datetime_str)
            # Remove fuso horário e milissegundos, e retransforma em datetime sem tzinfo
            dt_clean = dt.replace(tzinfo=None, microsecond=0)
            return dt_clean  # Retorna datetime no formato padrão
        except (ValueError, TypeError):
            return None
    
    def seconds_to_time_format(self, seconds):
        """Converte segundos para formato HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    
    def get_status_at_time(self, statuses, timestamp):
        """
        Determina o status do ticket em um momento específico
        
        Args:
            statuses (list): Lista de status do ticket, cada um com start e end
            timestamp (datetime): Data/hora para verificar
            
        Returns:
            str: Descrição do status ativo naquele momento ou None se nenhum status ativo
        """
        if not timestamp or not statuses:
            return None
            
        # Ordena os status por data de início
        sorted_statuses = sorted(
            statuses, 
            key=lambda x: self.parse_datetime(x.get('start', {}).get('operator', {}).get('date')) or datetime.datetime.min
        )
        
        # Encontra o status ativo no momento do timestamp
        for status in sorted_statuses:
            start_dt = self.parse_datetime(status.get('start', {}).get('operator', {}).get('date'))
            end_dt = self.parse_datetime(status.get('end', {}).get('operator', {}).get('date'))
            
            # Verifica se o timestamp está dentro do intervalo deste status
            if start_dt and start_dt <= timestamp and (not end_dt or timestamp <= end_dt):
                return status.get('description')
                
        # Se chegou aqui, não encontrou um status ativo
        return None
        
    def analyze_ticket(self, ticket_details):
        """Analisa interações de ticket e calcula métricas de tempo"""
        result = {
            'id': ticket_details.get('id'),
            'protocol': ticket_details.get('protocol'),
            'subject': ticket_details.get('subject'),
            'customer_name': ticket_details.get('customer', {}).get('name'),
            'customer_email': ticket_details.get('customer', {}).get('email'),
            'creation_date': ticket_details.get('creation_date'),
            'creation_dt': self.parse_datetime(ticket_details.get('creation_date')),
            'first_reply_date': ticket_details.get('first_reply_date'),
            'end_date': ticket_details.get('end_date'),
            'current_situation': ticket_details.get('situation', {}).get('description'),
            'situation_id': ticket_details.get('situation', {}).get('id'),
            'situation_apply_date': ticket_details.get('situation', {}).get('apply_date'),
            'time_with_client': 0,  # em segundos
            'time_with_support': 0,  # em segundos
            'status_time': {},       # tempo total em cada status
            'status_business_time': {},  # tempo em horário comercial para cada status
            'business_time_with_client': 0,  # em segundos durante horário comercial
            'business_time_with_support': 0,  # em segundos durante horário comercial
            'time_to_first_status': 0,  # tempo da criação até o primeiro status
            'business_time_to_first_status': 0,  # tempo comercial da criação até o primeiro status
            'interactions': [],  # Lista para armazenar todas as interações
        }
        
        # Obtém respostas e status
        replies = ticket_details.get('replies', [])
        statuses = ticket_details.get('status', []) if isinstance(ticket_details.get('status'), list) else []
        
        # Ordena por data
        replies.sort(key=lambda x: self.parse_datetime(x.get('date')) or datetime.datetime.min)
        statuses.sort(key=lambda x: self.parse_datetime(x.get('start', {}).get('operator', {}).get('date')) or datetime.datetime.min)
        
        # Calcula tempo com cliente vs suporte baseado nas respostas
        creation_dt = self.parse_datetime(ticket_details.get('creation_date'))
        if creation_dt:
            creation_interaction = {
                'id': 'creation',
                'date': creation_dt,
                'sender_type': 'C',  # Assume que o ticket é criado pelo cliente
                'classification': 'C',  # Classificação inicial igual ao tipo
                'sender': ticket_details.get('customer', {}).get('name', 'Cliente'),
                'message': 'Ticket criado',
                'status': None,
                'has_attachments': False,
                'is_virtual': True  # Marca como interação virtual
            }
            result['interactions'].append(creation_interaction)
            
        
        # Determina se o ticket está finalizado
        is_finished = False
        end_dt = None
        
        # Verifica end_date
        if ticket_details.get('end_date'):
            end_dt = self.parse_datetime(ticket_details.get('end_date'))
            is_finished = True
        
        # Verifica situation
        situation_id = ticket_details.get('situation', {}).get('id')
        situation_dt = self.parse_datetime(ticket_details.get('situation', {}).get('apply_date'))
        
        if situation_id in [4, 5]:  # Cancelada ou Finalizada
            is_finished = True
            if not end_dt and situation_dt:
                end_dt = situation_dt
        
        # Define data final para cálculos
        final_date = datetime.datetime.now()
        if is_finished and end_dt:
            final_date = end_dt
        
        # Inicializa com a criação do ticket
        last_dt = creation_dt
        last_sender = 'C'  # Assumindo que o ticket começa com o cliente
        
        # Processar interações (replies) - APENAS UM LOOP
        for reply in replies:
            interaction = {
                'id': reply.get('id'),
                'date': self.parse_datetime(reply.get('date')),
                'sender_type': reply.get('sender_type'),  # Original
                'classification': reply.get('sender_type'),  # Classificação atual (inicialmente igual ao original)
                'sender': reply.get('sender'),
                'message': reply.get('message'),
                'status': self.get_status_at_time(statuses, self.parse_datetime(reply.get('date'))),
                'has_attachments': len(reply.get('attachments', [])) > 0
            }
            result['interactions'].append(interaction)
            
            current_dt = interaction['date']
            sender_type = interaction['sender_type']
            
            if not current_dt or not sender_type:
                continue
                
            time_diff = (current_dt - last_dt).total_seconds()
            business_time = self.calculator.calculate_business_time(last_dt, current_dt)
            
            # Se o último remetente foi cliente, o tempo foi com suporte
            if last_sender == 'C':
                result['time_with_support'] += time_diff
                result['business_time_with_support'] += business_time
            # Se o último remetente foi suporte, o tempo foi com cliente
            elif last_sender == 'A':
                result['time_with_client'] += time_diff
                result['business_time_with_client'] += business_time
                
            last_dt = current_dt
            last_sender = sender_type
        
        # Calcula tempo da última resposta até agora/fim
        if last_dt and last_dt < final_date:
            time_diff = (final_date - last_dt).total_seconds()
            business_time = self.calculator.calculate_business_time(last_dt, final_date)
            
            # Se o último remetente foi cliente, o tempo é com suporte
            if last_sender == 'C':
                result['time_with_support'] += time_diff
                result['business_time_with_support'] += business_time
            # Se o último remetente foi suporte, o tempo é com cliente
            elif last_sender == 'A':
                result['time_with_client'] += time_diff
                result['business_time_with_client'] += business_time
        
        # Calcula tempo da criação até o primeiro status
        if statuses and creation_dt:
            first_status_start = self.parse_datetime(statuses[0].get('start', {}).get('operator', {}).get('date'))
            if first_status_start:
                result['time_to_first_status'] = (first_status_start - creation_dt).total_seconds()
                # Calcula tempo em horário comercial
                result['business_time_to_first_status'] = self.calculator.calculate_business_time(
                    creation_dt, first_status_start
                )
        
        # LOOP SEPARADO PARA CALCULAR TEMPO EM CADA STATUS
        # Calcula tempo em cada status
        for status in statuses:
            start_dt = self.parse_datetime(status.get('start', {}).get('operator', {}).get('date'))
            end_dt = self.parse_datetime(status.get('end', {}).get('operator', {}).get('date'))
            status_desc = status.get('description')
            
            if not start_dt or not status_desc:
                continue
                
            # Usa data final se fornecida, caso contrário usa agora ou data final do ticket
            if not end_dt:
                if is_finished and end_dt:
                    end_dt = end_dt
                else:
                    end_dt = final_date
                    
            # Calcula tempo neste status (total e horário comercial)
            time_diff = (end_dt - start_dt).total_seconds()
            business_time = self.calculator.calculate_business_time(start_dt, end_dt)
            
            # Adiciona ao dicionário de tempo total por status
            if status_desc in result['status_time']:
                result['status_time'][status_desc] += time_diff
            else:
                result['status_time'][status_desc] = time_diff
                
            # Adiciona ao dicionário de tempo em horário comercial por status
            if status_desc in result['status_business_time']:
                result['status_business_time'][status_desc] += business_time
            else:
                result['status_business_time'][status_desc] = business_time
        
        # Ordenar interações por data (mantive caso ainda haja necessidade)
        result['interactions'].sort(key=lambda x: x['date'] or datetime.datetime.min)
            
        return result




class BusinessHoursDialog(QDialog):
    """Dialog for configuring business hours"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.business_hours = config_manager.get_business_hours()
        
        self.setWindowTitle("Configurar Horário Comercial")
        self.setMinimumSize(800, 500)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        
        # Título com instrução
        title_label = QLabel("Configure os horários comerciais para cada dia da semana")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Layout de grade para os dias
        days_layout = QGridLayout()
        days_layout.setSpacing(10)
        
        # Tradução dos dias para português
        day_names = {
            'monday': 'Segunda-feira',
            'tuesday': 'Terça-feira',
            'wednesday': 'Quarta-feira',
            'thursday': 'Quinta-feira',
            'friday': 'Sexta-feira',
            'saturday': 'Sábado',
            'sunday': 'Domingo'
        }
        
        # Cores para dias úteis e fins de semana
        weekday_color = "#E5F5E5"  # Verde claro
        weekend_color = "#F5E5E5"  # Vermelho claro
        
        # Create widgets for each day
        self.day_widgets = {}
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Posiciona os dias em uma grade de 3 colunas
        for i, day in enumerate(days):
            row = i // 3
            col = i % 3
            
            # Escolhe a cor de fundo com base no dia
            bg_color = weekend_color if day in ['saturday', 'sunday'] else weekday_color
            
            group = QGroupBox(day_names.get(day, day.capitalize()))
            group.setStyleSheet(f"QGroupBox {{ background-color: {bg_color}; border-radius: 5px; padding: 5px; }}")
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(10, 10, 10, 10)
            
            # Get current time ranges
            ranges_str = self.business_hours.get(day, '')
            ranges = []
            
            if ranges_str:
                for time_range in ranges_str.split(','):
                    if '-' in time_range:
                        start, end = time_range.split('-')
                        ranges.append((start, end))
            
            # Container para os intervalos
            ranges_widget = QWidget()
            ranges_layout = QVBoxLayout(ranges_widget)
            ranges_layout.setContentsMargins(0, 0, 0, 0)
            ranges_layout.setSpacing(5)
            
            # Adicionar intervalos existentes
            ranges_widgets = []
            
            for start, end in ranges:
                range_widget = self.create_time_range_widget(start, end, ranges_widgets)
                ranges_layout.addWidget(range_widget)
            
            # Adicionar um scroll se necessário
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(ranges_widget)
            scroll.setMaximumHeight(150)
            scroll.setStyleSheet("QScrollArea { border: none; }")
            
            group_layout.addWidget(scroll)
            
            # Botão para adicionar novo intervalo
            add_btn = QPushButton("Adicionar Intervalo")
            add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            add_btn.clicked.connect(lambda checked=False, l=ranges_layout, w=ranges_widgets: 
                               self.add_range(l, w))
            
            group_layout.addWidget(add_btn)
            group.setLayout(group_layout)
            
            days_layout.addWidget(group, row, col)
            
            # Store widgets
            self.day_widgets[day] = {
                'ranges': ranges_widgets,
                'layout': ranges_layout
            }
        
        # Adiciona o layout dos dias ao layout principal
        main_layout.addLayout(days_layout)
        
        # Botões inferiores
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("padding: 6px 12px;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Salvar")
        save_btn.setStyleSheet("background-color: #3366CC; color: white; font-weight: bold; padding: 6px 16px;")
        save_btn.clicked.connect(self.save_hours)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
    
    def create_time_range_widget(self, start_time="08:00", end_time="12:00", ranges_widgets=None):
        """Cria um widget para um intervalo de tempo"""
        range_widget = QWidget()
        range_layout = QHBoxLayout(range_widget)
        range_layout.setContentsMargins(0, 0, 0, 0)
        
        start_edit = QTimeEdit()
        start_edit.setDisplayFormat("HH:mm")
        start_h, start_m = map(int, start_time.split(':'))
        start_edit.setTime(QTime(start_h, start_m))
        
        end_edit = QTimeEdit()
        end_edit.setDisplayFormat("HH:mm")
        end_h, end_m = map(int, end_time.split(':'))
        end_edit.setTime(QTime(end_h, end_m))
        
        range_layout.addWidget(QLabel("De:"))
        range_layout.addWidget(start_edit)
        range_layout.addWidget(QLabel("Até:"))
        range_layout.addWidget(end_edit)
        
        remove_btn = QPushButton("×")
        remove_btn.setToolTip("Remover este intervalo")
        remove_btn.setStyleSheet("background-color: #FF5555; color: white; font-weight: bold; max-width: 25px;")
        range_layout.addWidget(remove_btn)
        
        new_range = {
            'widget': range_widget,
            'start': start_edit,
            'end': end_edit,
            'remove': remove_btn
        }
        
        if ranges_widgets is not None:
            ranges_widgets.append(new_range)
            remove_btn.clicked.connect(lambda _, r=new_range, w=ranges_widgets: 
                                   self.remove_range(r, w))
        
        return range_widget
        
    def add_range(self, layout, ranges_widgets):
        """Add a new time range"""
        range_widget = self.create_time_range_widget("08:00", "12:00", ranges_widgets)
        layout.addWidget(range_widget)
        
    def remove_range(self, range_data, ranges_widgets):
        """Remove a time range"""
        if len(ranges_widgets) <= 1:
            QMessageBox.warning(self, "Aviso", "É necessário manter pelo menos um intervalo de horário.")
            return
            
        # Find and remove from list
        ranges_widgets.remove(range_data)
                
        # Remove from layout
        range_data['widget'].setParent(None)
        range_data['widget'].deleteLater()
        
    def save_hours(self):
        """Save business hours configuration"""
        for day, widgets in self.day_widgets.items():
            ranges = []
            
            for range_data in widgets['ranges']:
                start_time = range_data['start'].time().toString("HH:mm")
                end_time = range_data['end'].time().toString("HH:mm")
                ranges.append(f"{start_time}-{end_time}")
                
            # Save to config
            self.config_manager.set_business_hours(day, ','.join(ranges))
        
        QMessageBox.information(self, "Sucesso", "Horários comerciais salvos com sucesso!")    
        self.accept()


class HolidaysDialog(QDialog):
    """Dialog for managing holidays"""
    
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        
        self.setWindowTitle("Gerenciar Feriados")
        self.setMinimumSize(650, 500)
        
        self.init_ui()
        self.load_holidays()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título e descrição
        header = QWidget()
        header.setStyleSheet("background-color: #F0F8FF; border-radius: 5px;")
        header_layout = QVBoxLayout(header)
        
        title = QLabel("Gerenciamento de Feriados")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1E3A8A;")
        
        description = QLabel("Configure os feriados para que sejam excluídos dos cálculos de tempo em horário comercial.")
        description.setStyleSheet("color: #4A5568;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        
        layout.addWidget(header)
        
        # Adicionar novo feriado - seção superior
        add_group = QGroupBox("Adicionar Novo Feriado")
        add_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        form_layout = QHBoxLayout()
        
        date_label = QLabel("Data:")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setStyleSheet("padding: 5px; border: 1px solid #CCCCCC; border-radius: 3px;")
        
        description_label = QLabel("Descrição:")
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Informe o nome do feriado")
        self.description_edit.setStyleSheet("padding: 5px; border: 1px solid #CCCCCC; border-radius: 3px;")
        
        add_btn = QPushButton("Adicionar Feriado")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self.add_holiday)
        
        form_layout.addWidget(date_label)
        form_layout.addWidget(self.date_edit)
        form_layout.addWidget(description_label)
        form_layout.addWidget(self.description_edit)
        form_layout.addWidget(add_btn)
        
        add_group.setLayout(form_layout)
        layout.addWidget(add_group)
        
        # Lista de feriados
        list_group = QGroupBox("Feriados Cadastrados")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #CCCCCC;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        list_layout = QVBoxLayout()
        
        # Filtro por ano
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrar por ano:"))
        
        self.year_filter = QComboBox()
        self.year_filter.setStyleSheet("padding: 5px; border: 1px solid #CCCCCC; border-radius: 3px;")
        current_year = QDate.currentDate().year()
        self.year_filter.addItem("Todos os anos", 0)
        for year in range(current_year - 2, current_year + 5):
            self.year_filter.addItem(str(year), year)
        self.year_filter.setCurrentText(str(current_year))
        self.year_filter.currentIndexChanged.connect(self.apply_filter)
        
        clear_filter_btn = QPushButton("Limpar Filtro")
        clear_filter_btn.setStyleSheet("padding: 5px;")
        clear_filter_btn.clicked.connect(self.clear_filter)
        
        filter_layout.addWidget(self.year_filter)
        filter_layout.addWidget(clear_filter_btn)
        filter_layout.addStretch()
        
        list_layout.addLayout(filter_layout)
        
        # Table for holidays
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Data", "Descrição", "Ações"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                alternate-background-color: #F5F5F5;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 5px;
                font-weight: bold;
                border: none;
            }
        """)
        self.table.setAlternatingRowColors(True)
        
        list_layout.addWidget(self.table)
        list_group.setLayout(list_layout)
        
        layout.addWidget(list_group, 1)  # Com stretch factor para ocupar espaço disponível
        
        # Botões inferiores
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        import_btn = QPushButton("Importar Feriados Nacionais")
        import_btn.setStyleSheet("padding: 6px 12px;")
        import_btn.setToolTip("Importar feriados nacionais para o ano selecionado")
        import_btn.clicked.connect(self.import_holidays)
        
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("padding: 6px 12px;")
        close_btn.clicked.connect(self.accept)
        
        buttons_layout.addWidget(import_btn)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
    def load_holidays(self):
        """Load holidays from config"""
        holidays = self.config_manager.get_holidays()
        self.all_holidays = holidays  # Armazena para filtro
        
        self.apply_filter()
        
    def apply_filter(self):
        """Aplica filtro por ano"""
        year_filter = self.year_filter.currentData()
        
        filtered_holidays = self.all_holidays
        if year_filter:
            filtered_holidays = [(date, desc) for date, desc in self.all_holidays 
                              if date.year == year_filter]
        
        # Ordena por data
        filtered_holidays.sort(key=lambda x: x[0])
        
        self.table.setRowCount(len(filtered_holidays))
        
        for row, (date, description) in enumerate(filtered_holidays):
            # Date
            date_item = QTableWidgetItem(date.strftime("%d/%m/%Y"))
            date_item.setData(Qt.UserRole, date)  # Store actual date object
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, date_item)
            
            # Description
            self.table.setItem(row, 1, QTableWidgetItem(description))
            
            # Actions (Delete button)
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            
            delete_btn = QPushButton("Excluir")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            delete_btn.clicked.connect(lambda _, r=row: self.delete_holiday(r))
            
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.table.setCellWidget(row, 2, actions_widget)
            
    def clear_filter(self):
        """Limpa o filtro por ano"""
        self.year_filter.setCurrentIndex(0)  # "Todos os anos"
        
    def add_holiday(self):
        """Add a new holiday"""
        date = self.date_edit.date().toPyDate()
        description = self.description_edit.text().strip()
        
        if not description:
            QMessageBox.warning(self, "Erro", "Por favor, informe a descrição do feriado.")
            return
            
        # Check if date already exists
        for _, (holiday_date, _) in enumerate(self.all_holidays):
            if holiday_date == date:
                QMessageBox.warning(self, "Erro", "Já existe um feriado cadastrado para esta data.")
                return
        
        # Add to config
        self.config_manager.add_holiday(date, description)
        
        # Reload table
        self.all_holidays = self.config_manager.get_holidays()
        self.apply_filter()
        
        # Clear inputs and set success message
        self.description_edit.clear()
        QMessageBox.information(self, "Sucesso", f"Feriado '{description}' adicionado com sucesso!")
        
    def delete_holiday(self, row):
        """Delete a holiday"""
        date_item = self.table.item(row, 0)
        
        if date_item:
            date = date_item.data(Qt.UserRole)
            description = self.table.item(row, 1).text()
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, 
                "Confirmar Exclusão",
                f"Deseja realmente excluir o feriado '{description}' ({date.strftime('%d/%m/%Y')})?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Remove from config
                self.config_manager.remove_holiday(date)
                
                # Reload table
                self.all_holidays = self.config_manager.get_holidays()
                self.apply_filter()
                
                QMessageBox.information(self, "Sucesso", f"Feriado '{description}' excluído com sucesso!")
    
    def import_holidays(self):
        """Importa feriados nacionais fixos para o ano selecionado"""
        year = self.year_filter.currentData()
        
        if not year:
            year = QDate.currentDate().year()
            
        # Feriados nacionais fixos
        national_holidays = [
            (1, 1, "Confraternização Universal"),
            (4, 21, "Tiradentes"),
            (5, 1, "Dia do Trabalho"),
            (9, 7, "Independência do Brasil"),
            (10, 12, "Nossa Senhora Aparecida"),
            (11, 2, "Finados"),
            (11, 15, "Proclamação da República"),
            (12, 25, "Natal")
        ]
        
        count = 0
        for month, day, description in national_holidays:
            try:
                holiday_date = datetime.date(year, month, day)
                
                # Verifica se já existe
                exists = False
                for existing_date, _ in self.all_holidays:
                    if existing_date == holiday_date:
                        exists = True
                        break
                        
                if not exists:
                    self.config_manager.add_holiday(holiday_date, description)
                    count += 1
            except ValueError:
                # Data inválida
                pass
        
        # Recarrega a tabela
        self.all_holidays = self.config_manager.get_holidays()
        self.apply_filter()
        
        # Mensagem de sucesso
        if count > 0:
            QMessageBox.information(self, "Importação Concluída", 
                                  f"Foram importados {count} feriados nacionais para o ano de {year}.")
        else:
            QMessageBox.information(self, "Importação Concluída", 
                                  f"Nenhum feriado novo foi importado. Todos os feriados nacionais fixos para {year} já estão cadastrados.")

class FilterTab(QWidget):
    """Tab for filtering tickets"""
    
    def __init__(self, api_client, results_tab):
        super().__init__()
        self.api_client = api_client
        self.results_tab = results_tab
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Título e descrição da página
        header = QWidget()
        header.setStyleSheet("background-color: #F5F8FA; border-radius: 6px; padding: 10px;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("Filtros de Pesquisa")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        
        description = QLabel("Preencha os filtros desejados e clique em Pesquisar para localizar tickets. Quanto mais filtros preenchidos, mais específica será a busca.")
        description.setStyleSheet("color: #7F8C8D; font-size: 13px;")
        description.setWordWrap(True)
        
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        
        main_layout.addWidget(header)
        
        # Criar card para os filtros
        filter_card = QGroupBox("Filtros Disponíveis")
        filter_card.setStyleSheet("""
            QGroupBox {
                background-color: white;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                margin-top: 15px;
                padding-top: 20px;
                font-weight: bold;
            }
            QGroupBox::title {
                background-color: white;
                padding: 0 10px;
                subcontrol-origin: margin;
                left: 20px;
            }
        """)
        
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setSpacing(15)
        
        # Grid de filtros para melhor organização
        filters_grid = QGridLayout()
        filters_grid.setColumnStretch(0, 0)  # Rótulo
        filters_grid.setColumnStretch(1, 1)  # Campo
        filters_grid.setColumnStretch(2, 0)  # Rótulo 2
        filters_grid.setColumnStretch(3, 1)  # Campo 2
        filters_grid.setVerticalSpacing(15)
        filters_grid.setHorizontalSpacing(20)
        
        # Row 1: Período de Data
        date_label = QLabel("Período (Data Criação):")
        date_label.setStyleSheet("font-weight: bold;")
        
        date_widget = QWidget()
        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.setSpacing(8)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setStyleSheet("""
            QDateEdit {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        
        date_layout.addWidget(self.date_from)
        date_layout.addWidget(QLabel("até"))
        date_layout.addWidget(self.date_to)
        
        filters_grid.addWidget(date_label, 0, 0, Qt.AlignRight)
        filters_grid.addWidget(date_widget, 0, 1)
        
        # Row 1, Col 2: Situação do ticket
        situation_label = QLabel("Situação:")
        situation_label.setStyleSheet("font-weight: bold;")
        
        self.situation = QComboBox()
        self.situation.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #CCCCCC;
            }
        """)
        self.situation.addItem("Todos", "")
        self.situation.addItem("Abertos", "1")
        self.situation.addItem("Aguardando resposta do cliente", "2")
        self.situation.addItem("Aguardando resposta do operador", "3")
        self.situation.addItem("Em progresso", "4")
        self.situation.addItem("Fechado", "5")
        self.situation.addItem("Cancelado", "6")
        
        filters_grid.addWidget(situation_label, 0, 2, Qt.AlignRight)
        filters_grid.addWidget(self.situation, 0, 3)
        
        # Row 2: Prioridade
        priority_label = QLabel("Prioridade:")
        priority_label.setStyleSheet("font-weight: bold;")
        
        self.priority = QComboBox()
        self.priority.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        self.priority.addItem("Todos", "")
        self.priority.addItem("Baixa", "1")
        self.priority.addItem("Média", "2")
        self.priority.addItem("Alta", "3")
        self.priority.addItem("Crítica", "4")
        
        filters_grid.addWidget(priority_label, 1, 0, Qt.AlignRight)
        filters_grid.addWidget(self.priority, 1, 1)
        
        # Row 2, Col 2: Categoria
        category_label = QLabel("Categoria:")
        category_label.setStyleSheet("font-weight: bold;")

        self.category = QComboBox()
        self.category.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
            }
        """)
        self.category.addItem("Todas", "")
        self.category.addItem("Baixa - Problemas genéricos", "1e78916e1a57f8765005d860c4189028")
        self.category.addItem("Consulta - Dúvidas e investigação", "1456c683ab9e1de58eac3ca46f52b50e")
        self.category.addItem("Crítica - Paralisação total", "612a8b3bda595dc4e1c18b62dde04243")

        filters_grid.addWidget(category_label, 1, 2, Qt.AlignRight)
        filters_grid.addWidget(self.category, 1, 3)
        
        filter_layout.addLayout(filters_grid)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #E0E0E0;")
        filter_layout.addWidget(separator)
        
        # Botões de Ação
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        clear_btn = QPushButton("Limpar Filtros")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ECF0F1;
                border: 1px solid #BDC3C7;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                color: #7F8C8D;
            }
            QPushButton:hover {
                background-color: #D0D3D4;
            }
        """)
        clear_btn.clicked.connect(self.clear_filters)
        
        search_btn = QPushButton("Pesquisar Tickets")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        search_btn.clicked.connect(self.search_tickets)
        
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(search_btn)
        
        filter_layout.addLayout(button_layout)
        
        main_layout.addWidget(filter_card)
        
        # Área de ajuda/dicas
        tips_widget = QWidget()
        tips_widget.setStyleSheet("background-color: #FFF8E1; border-radius: 6px; padding: 8px;")
        tips_layout = QHBoxLayout(tips_widget)
        
        info_icon = QLabel("ℹ️")
        info_icon.setStyleSheet("font-size: 16px;")
        
        tips_text = QLabel("Dica: Para resultados mais precisos, utilize o período mais curto possível. A pesquisa retorna no máximo 50 tickets.")
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet("color: #9A7D0A; font-size: 12px;")
        
        tips_layout.addWidget(info_icon)
        tips_layout.addWidget(tips_text, 1)
        
        main_layout.addWidget(tips_widget)
        
        # Espaço flexível
        main_layout.addStretch()
        
        self.setLayout(main_layout)
    
    def clear_filters(self):
        """Limpa todos os filtros para uma nova pesquisa"""
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.situation.setCurrentIndex(0)  # "Todos"
        self.priority.setCurrentIndex(0)   # "Todos" 
        self.category.clear()
        
    def search_tickets(self):
        """Realiza a busca de tickets na API com base nos filtros"""
        # Verifica se a data final é posterior à data inicial
        if self.date_from.date() > self.date_to.date():
            QMessageBox.warning(self, "Erro de Validação", 
                              "A data inicial não pode ser posterior à data final.")
            return
            
        # Mostra indicador de carregamento
        cursor = QCursor(Qt.WaitCursor)
        QApplication.setOverrideCursor(cursor)
        
        try:
            # Monta os parâmetros
            params = {}

            # Obtém data/hora atual com timezone -0300
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S-0300")

            # Data inicial (00:00:00 do dia selecionado)
            date_from = self.date_from.date().toString("yyyy-MM-dd") + " 00:00:00-0300"
            if date_from > now:
                date_from = now  # Garante que não está no futuro

            # Data final (23:59:59 do dia selecionado)
            date_to = self.date_to.date().toString("yyyy-MM-dd") + " 23:59:59-0300"
            if date_to > now:
                date_to = now  # Garante que não está no futuro

            # Define os parâmetros de data para a API
            params['creation_date_ge'] = date_from
            params['creation_date_le'] = date_to

            # Situação (use 'situation' ao invés de 'situation_id')
            if self.situation.currentData():
                params['situation'] = str(self.situation.currentData())

            # Prioridade (API aceita vários separados por vírgula)
            if self.priority.currentData():
                params['priority'] = str(self.priority.currentData())

            # Categoria
            if self.category.currentData():
                params['category_id'] = str(self.category.currentData())

            # Chamada da API
            print("Parâmetros finais:", params)
            result = self.api_client.list_tickets(params)

            if result.get('success'):
                data = result.get('data', [])
                self.results_tab.load_results(data)
                if data:
                    # Procurar o QTabWidget e mudar para a aba de resultados
                    widget = self
                    while widget:
                        parent = widget.parent()
                        if not parent:
                            break
                            
                        if isinstance(parent, QTabWidget):
                            # Encontrou o QTabWidget
                            parent.setCurrentWidget(self.results_tab)
                            break
                        
                        # Tentar também com os widgets irmãos
                        for sibling in parent.children():
                            if isinstance(sibling, QTabWidget):
                                # Verificar se nosso results_tab está entre as abas
                                for i in range(sibling.count()):
                                    if sibling.widget(i) == self.results_tab:
                                        sibling.setCurrentWidget(self.results_tab)
                                        break
                        
                        widget = parent
                else:
                    # Exibe popup se não houver resultados
                    QMessageBox.information(self, "Sem Resultados", 
                                          "A pesquisa não retornou nenhum resultado. Tente ajustar os filtros.")
            else:
                QMessageBox.warning(self, "Erro da API", 
                                  f"Erro: {result.get('message', 'Erro desconhecido')}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
        finally:
            # Remove o indicador de carregamento
            QApplication.restoreOverrideCursor()


class ResultsTab(QWidget):
    """Tab for displaying ticket search results"""
    
    def __init__(self, api_client, analyzer):
        super().__init__()
        self.api_client = api_client
        self.analyzer = analyzer
        self.tickets = []
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Cabeçalho com título e estatísticas
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #F5F8FA; border-radius: 6px; padding: 10px;")
        header_layout = QHBoxLayout(header_widget)
        
        # Título e contador
        title_section = QWidget()
        title_layout = QVBoxLayout(title_section)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("Resultados da Pesquisa")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        
        self.result_count = QLabel("0 tickets encontrados")
        self.result_count.setStyleSheet("color: #7F8C8D;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(self.result_count)
        
        # Estatísticas (direita)
        stats_section = QWidget()
        stats_layout = QVBoxLayout(stats_section)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        
        self.avg_response_time = QLabel("Tempo médio de resposta: -")
        self.avg_response_time.setStyleSheet("color: #7F8C8D; text-align: right;")
        self.avg_response_time.setAlignment(Qt.AlignRight)
        
        self.sla_percentage = QLabel("SLA cumprido: -")
        self.sla_percentage.setStyleSheet("color: #7F8C8D; text-align: right;")
        self.sla_percentage.setAlignment(Qt.AlignRight)
        
        stats_layout.addWidget(self.avg_response_time)
        stats_layout.addWidget(self.sla_percentage)
        
        header_layout.addWidget(title_section)
        header_layout.addStretch()
        header_layout.addWidget(stats_section)
        
        layout.addWidget(header_widget)
        
        # Barra de ferramentas para a tabela
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # Filtro rápido
        search_label = QLabel("Filtrar:")
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite para filtrar resultados")
        self.search_input.setStyleSheet("padding: 5px; border: 1px solid #CCCCCC; border-radius: 4px; max-width: 250px;")
        self.search_input.textChanged.connect(self.filter_results)
        
        # Botões de seleção
        select_all_btn = QPushButton("Selecionar Todos")
        select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #E8F0FE;
                border: 1px solid #BBDEFB;
                padding: 5px 10px;
                border-radius: 4px;
                color: #1565C0;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        select_all_btn.clicked.connect(self.select_all)
        
        deselect_all_btn = QPushButton("Desmarcar Todos")
        deselect_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                padding: 5px 10px;
                border-radius: 4px;
                color: #616161;
            }
            QPushButton:hover {
                background-color: #EEEEEE;
            }
        """)
        deselect_all_btn.clicked.connect(self.deselect_all)
        
        toolbar_layout.addWidget(search_label)
        toolbar_layout.addWidget(self.search_input)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(select_all_btn)
        toolbar_layout.addWidget(deselect_all_btn)
        
        layout.addWidget(toolbar_widget)
        
        # Tabela de resultados
        table_widget = QWidget()
        table_widget.setStyleSheet("background-color: white; border: 1px solid #E0E0E0; border-bottom-left-radius: 6px; border-bottom-right-radius: 6px;")
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create table for results
        self.table = QTableWidget()
        self.table.setColumnCount(10) # Reduzi para as colunas mais importantes
        self.table.setHorizontalHeaderLabels([
            "", "Protocolo", "Assunto", "Cliente", 
            "Prioridade", "Criado", "Prazo", "SLA",
            "Situação", "Departamento"
        ])
        
        # Set table properties
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch) # Assunto estica
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                gridline-color: #E0E0E0;
                alternate-background-color: #F9F9F9;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 6px;
                font-weight: bold;
                border: none;
                border-bottom: 1px solid #E0E0E0;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #F0F0F0;
            }
            QTableWidget::item:selected {
                background-color: #EBF5FB;  /* Azul muito claro para seleção */
                color: black;  /* Mantém o texto em preto quando selecionado */
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_widget, 1) # 1 = stretch
        
        # Barra de ações inferior
        actions_widget = QWidget()
        actions_widget.setStyleSheet("background-color: #F5F5F5; border-radius: 6px; padding: 10px;")
        actions_layout = QHBoxLayout(actions_widget)
        
        self.selected_count = QLabel("0 tickets selecionados")
        
        analyze_btn = QPushButton("Analisar Selecionados")
        analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #2ECC71;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #27AE60;
            }
            QPushButton:disabled {
                background-color: #A5D6A7;
                color: #E8F5E9;
            }
        """)
        analyze_btn.setEnabled(False)
        analyze_btn.clicked.connect(self.analyze_selected)
        
        # Atualizar o estado do botão quando a seleção muda
        self.table.itemSelectionChanged.connect(lambda: self.update_selection_count(analyze_btn))
        
        actions_layout.addWidget(self.selected_count)
        actions_layout.addStretch()
        actions_layout.addWidget(analyze_btn)
        
        layout.addWidget(actions_widget)
        
        self.setLayout(layout)
        
    def load_results(self, tickets):
        """Load tickets into the table"""
        self.tickets = tickets
        self.table.setRowCount(len(tickets))
        
        # Atualizar contador de resultados
        self.result_count.setText(f"{len(tickets)} tickets encontrados")
        
        # Estatísticas
        response_times = []
        sla_compliant = 0
        
        for row, ticket in enumerate(tickets):
            # Widget para checkbox com estilo
            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(4, 0, 0, 0)
            checkbox_layout.setAlignment(Qt.AlignCenter)
            
            checkbox = QCheckBox()
            checkbox.setStyleSheet("QCheckBox { margin: 0 auto; }")
            checkbox_layout.addWidget(checkbox)
            
            self.table.setCellWidget(row, 0, checkbox_widget)
            
            # Protocolo
            protocol_item = QTableWidgetItem(str(ticket.get('protocol', '')))
            protocol_item.setData(Qt.UserRole, str(ticket.get('id', '')))  # Armazena ID como dado oculto
            self.table.setItem(row, 1, protocol_item)
            
            # Assunto
            subject_item = QTableWidgetItem(str(ticket.get('subject', '')))
            subject_item.setToolTip(str(ticket.get('subject', '')))
            self.table.setItem(row, 2, subject_item)
            
            # Cliente
            self.table.setItem(row, 3, QTableWidgetItem(str(ticket.get('customer', {}).get('name', ''))))
            
            # Prioridade (com cores)
            priority = str(ticket.get('priority', ''))
            priority_item = QTableWidgetItem(priority)
            priority_item.setTextAlignment(Qt.AlignCenter)
            
            # Cores baseadas na prioridade
            if priority == "4":  # Crítica
                priority_item.setBackground(QColor("#FFEBEE"))
                priority_item.setForeground(QColor("#D32F2F"))
                priority_item.setText("Crítica")
            elif priority == "3":  # Alta
                priority_item.setBackground(QColor("#FFF3E0"))
                priority_item.setForeground(QColor("#E64A19"))
                priority_item.setText("Alta")
            elif priority == "2":  # Média
                priority_item.setBackground(QColor("#E8F5E9"))
                priority_item.setForeground(QColor("#388E3C"))
                priority_item.setText("Média")
            elif priority == "1":  # Baixa
                priority_item.setBackground(QColor("#E3F2FD"))
                priority_item.setForeground(QColor("#1976D2"))
                priority_item.setText("Baixa")
                
            self.table.setItem(row, 4, priority_item)
            
            # Data de criação (formatada)
            creation_date = ticket.get('creation_date', '')
            if creation_date:
                try:
                    # Tenta formatar a data para exibição mais legível
                    date_parts = creation_date.split(' ')[0].split('-')
                    time_parts = creation_date.split(' ')[1].split(':')
                    formatted_date = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]} {time_parts[0]}:{time_parts[1]}"
                    self.table.setItem(row, 5, QTableWidgetItem(formatted_date))
                except:
                    self.table.setItem(row, 5, QTableWidgetItem(creation_date))
            else:
                self.table.setItem(row, 5, QTableWidgetItem(""))
            
            # Prazo SLA
            deadline = ticket.get('sla', {}).get('deadline', {}).get('date', '')
            if deadline:
                try:
                    # Tenta formatar a data para exibição mais legível
                    date_parts = deadline.split(' ')[0].split('-')
                    time_parts = deadline.split(' ')[1].split(':')
                    formatted_deadline = f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]} {time_parts[0]}:{time_parts[1]}"
                    self.table.setItem(row, 6, QTableWidgetItem(formatted_deadline))
                except:
                    self.table.setItem(row, 6, QTableWidgetItem(deadline))
            else:
                self.table.setItem(row, 6, QTableWidgetItem(""))
            
            # Status SLA (com cores)
            sla_accomplished = ticket.get('sla', {}).get('deadline', {}).get('accomplished', None)
            sla_item = QTableWidgetItem()
            sla_item.setTextAlignment(Qt.AlignCenter)
            
            if sla_accomplished is not None:
                if sla_accomplished:
                    sla_item.setText("✓")
                    sla_item.setToolTip("SLA cumprido")
                    sla_item.setBackground(QColor("#E8F5E9"))
                    sla_item.setForeground(QColor("#388E3C"))
                    sla_compliant += 1
                else:
                    sla_item.setText("✗")
                    sla_item.setToolTip("SLA não cumprido")
                    sla_item.setBackground(QColor("#FFEBEE"))
                    sla_item.setForeground(QColor("#D32F2F"))
            
            self.table.setItem(row, 7, sla_item)
            
            # Situação
            situation_item = QTableWidgetItem(str(ticket.get('situation', {}).get('description', '')))
            situation_id = str(ticket.get('situation', {}).get('id', ''))
            
            # Cores baseadas na situação
            if situation_id == "1":  # Aberto
                situation_item.setBackground(QColor("#E3F2FD"))
            elif situation_id == "5":  # Fechado
                situation_item.setBackground(QColor("#E8F5E9"))
            elif situation_id == "6":  # Cancelado
                situation_item.setBackground(QColor("#FFEBEE"))
                
            self.table.setItem(row, 8, situation_item)
            
            # Departamento
            self.table.setItem(row, 9, QTableWidgetItem(str(ticket.get('department', {}).get('name', ''))))
            
            # Coletar dados para estatísticas
            first_reply = ticket.get('first_reply_date')
            creation = ticket.get('creation_date')
            if first_reply and creation:
                try:
                    from datetime import datetime
                    first_reply_dt = datetime.strptime(first_reply.split('-03')[0], "%Y-%m-%d %H:%M:%S")
                    creation_dt = datetime.strptime(creation.split('-03')[0], "%Y-%m-%d %H:%M:%S")
                    response_time = (first_reply_dt - creation_dt).total_seconds()  # segundos
                    response_times.append(response_time)
                except:
                    pass
        
        # Atualizar estatísticas
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            hours = int(avg_time // 3600)
            minutes = int((avg_time % 3600) // 60)
            secs = int(avg_time % 60)
            self.avg_response_time.setText(f"Tempo médio de resposta: {hours:02d}:{minutes:02d}:{secs:02d}")
        
        if tickets:
            sla_pct = (sla_compliant / len(tickets)) * 100
            self.sla_percentage.setText(f"SLA cumprido: {sla_pct:.1f}%")
            
            # Definir cor baseada na porcentagem de SLA
            if sla_pct >= 90:
                self.sla_percentage.setStyleSheet("color: #388E3C; font-weight: bold; text-align: right;")
            elif sla_pct >= 75:
                self.sla_percentage.setStyleSheet("color: #FFA000; font-weight: bold; text-align: right;")
            else:
                self.sla_percentage.setStyleSheet("color: #D32F2F; font-weight: bold; text-align: right;")
            
        # Inicializar contador de seleção
        self.update_selection_count()
    
    def update_selection_count(self, analyze_btn=None):
        """Atualiza o contador de tickets selecionados e o estado do botão"""
        selected_count = len(self.get_selected_tickets())
        self.selected_count.setText(f"{selected_count} tickets selecionados")
        
        if analyze_btn:
            analyze_btn.setEnabled(selected_count > 0)
    
    def filter_results(self, text):
        """Filtra os resultados na tabela conforme o texto digitado"""
        text = text.lower()
        
        for row in range(self.table.rowCount()):
            visible = False
            
            # Verifica cada coluna exceto a primeira (checkbox)
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    visible = True
                    break
            
            # Esconde ou mostra a linha conforme o filtro
            self.table.setRowHidden(row, not visible)
    
    def select_all(self):
        """Select all tickets"""
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Seleciona apenas linhas visíveis
                checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(True)
        
        self.update_selection_count()
                
    def deselect_all(self):
        """Deselect all tickets"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(False)
                
        self.update_selection_count()
                
    def get_selected_tickets(self):
        """Get IDs of selected tickets"""
        selected = []
        
        for row in range(self.table.rowCount()):
            if not self.table.isRowHidden(row):  # Considera apenas linhas visíveis
                checkbox = self.table.cellWidget(row, 0).findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    ticket_id = self.table.item(row, 1).data(Qt.UserRole)  # Obtém ID armazenado
                    selected.append(ticket_id)
                
        return selected
    
    def analyze_selected(self):
        """Analyze selected tickets"""
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
                        "Erro na API", 
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
                    # Abre o diálogo de classificação
                    classifier = InteractionClassifierDialog(analysis_results, self)
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
            QMessageBox.critical(self, "Erro", str(e))
            
    def show_analysis_results(self, results):
        """Show analysis results in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Resultados da Análise")
        dialog.setMinimumSize(800, 600)
        dialog.setWindowState(Qt.WindowMaximized)
        
        layout = QVBoxLayout()
        
        # Create table for results
        table = QTableWidget()
        table.setColumnCount(10)  # Aumentado para incluir Bug e Ignorado
        table.setHorizontalHeaderLabels([
            "Protocolo", "Assunto", "Cliente", 
            "Tempo com Cliente", "Tempo com Suporte", "Tempo em Bug", "Tempo Ignorado",
            "Tempo Comercial com Cliente", "Tempo Comercial com Suporte", 
            "Status Atual"
        ])
        
        # Cores para os cabeçalhos da tabela
        table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #E0E0E0; font-weight: bold; }")
        
        # Set table properties
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("alternate-background-color: #F5F5F5; background-color: white;")
        
        # Add rows
        table.setRowCount(len(results))
        
        for row, analysis in enumerate(results):
            table.setItem(row, 0, QTableWidgetItem(str(analysis.get('protocol', ''))))
            table.setItem(row, 1, QTableWidgetItem(str(analysis.get('subject', ''))))
            table.setItem(row, 2, QTableWidgetItem(str(analysis.get('customer_name', ''))))
            
            # Função para formatar células de tempo com cores
            def set_time_cell(col, value, color_bg=None):
                cell = QTableWidgetItem(value)
                cell.setTextAlignment(Qt.AlignCenter)
                if color_bg:
                    cell.setBackground(QColor(color_bg))
                table.setItem(row, col, cell)
            
            # Convert seconds to HH:MM:SS format and add to table with colors
            client_time = self.analyzer.seconds_to_time_format(analysis.get('time_with_client', 0))
            support_time = self.analyzer.seconds_to_time_format(analysis.get('time_with_support', 0))
            bug_time = self.analyzer.seconds_to_time_format(analysis.get('reclassified_time_in_bug', 0))
            ignored_time = self.analyzer.seconds_to_time_format(analysis.get('reclassified_time_ignored', 0))
            
            business_client_time = self.analyzer.seconds_to_time_format(analysis.get('business_time_with_client', 0))
            business_support_time = self.analyzer.seconds_to_time_format(analysis.get('business_time_with_support', 0))
            
            # Definir células com cores correspondentes
            set_time_cell(3, client_time, "#E0E0FF")  # Azul claro para Cliente
            set_time_cell(4, support_time, "#E0FFE0")  # Verde claro para Suporte
            set_time_cell(5, bug_time, "#FFE0E0")  # Vermelho claro para Bug
            set_time_cell(6, ignored_time, "#F0F0F0")  # Cinza claro para Ignorado
            
            set_time_cell(7, business_client_time, "#C0C0FF")  # Azul mais forte para tempo comercial Cliente
            set_time_cell(8, business_support_time, "#C0FFC0")  # Verde mais forte para tempo comercial Suporte
            
            # Status atual
            status_item = QTableWidgetItem(str(analysis.get('current_situation', '')))
            status_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 9, status_item)
        
        layout.addWidget(table)
        
        # Título para a seção de tempo em status
        title_frame = QFrame()
        title_frame.setFrameShape(QFrame.StyledPanel)
        title_frame.setStyleSheet("background-color: #F0F0F0; border-radius: 3px;")
        
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(10, 5, 10, 5)
        
        title_label = QLabel("Tempo em Status (Horário Comercial)")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        help_btn = QPushButton("?")
        help_btn.setToolTip("Mostrar explicação dos cálculos de tempo")
        help_btn.setMaximumWidth(30)
        help_btn.setStyleSheet("font-weight: bold;")
        help_btn.clicked.connect(self.show_status_time_help)
        title_layout.addWidget(help_btn)
        
        layout.addWidget(title_frame)
        
        # Combine all status types
        all_statuses = set()
        for analysis in results:
            all_statuses.update(analysis.get('status_time', {}).keys())
            all_statuses.update(analysis.get('status_business_time', {}).keys())
        
        # Se ainda não encontramos status, procura nos dados brutos de 'status'
        if not all_statuses:
            for analysis in results:
                statuses = analysis.get('status', [])
                if isinstance(statuses, list):
                    for status in statuses:
                        desc = status.get('description')
                        if desc:
                            all_statuses.add(desc)
        
        # Sorted for consistent display
        all_statuses = sorted(all_statuses)
        
        # Create table for status times
        status_table = QTableWidget()
        status_table.setColumnCount(len(all_statuses) + 2)  # +2 para Protocol e Time to First Status
        
        # Headers
        headers = ["Protocolo", "Tempo até o primeiro status"] + list(all_statuses)
        status_table.setHorizontalHeaderLabels(headers)
        status_table.horizontalHeader().setStyleSheet("QHeaderView::section { background-color: #E0E0E0; font-weight: bold; }")
        
        # Set table properties
        status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        status_table.setAlternatingRowColors(True)
        status_table.setStyleSheet("alternate-background-color: #F5F5F5; background-color: white;")
        
        # Add rows
        status_table.setRowCount(len(results))
        
        for row, analysis in enumerate(results):
            # Protocol
            status_table.setItem(row, 0, QTableWidgetItem(str(analysis.get('protocol', ''))))
            
            # Add time to first status
            time_to_first = self.analyzer.seconds_to_time_format(analysis.get('business_time_to_first_status', 0))
            first_status_item = QTableWidgetItem(time_to_first)
            first_status_item.setTextAlignment(Qt.AlignCenter)
            first_status_item.setBackground(QColor("#FFFFD0"))  # Amarelo claro
            status_table.setItem(row, 1, first_status_item)
            
            # Add time in each status
            for col, status in enumerate(all_statuses, 2):  # Começar na coluna 2
                time_sec = analysis.get('status_business_time', {}).get(status, 0)
                time_formatted = self.analyzer.seconds_to_time_format(time_sec)
                
                status_item = QTableWidgetItem(time_formatted)
                status_item.setTextAlignment(Qt.AlignCenter)
                
                # Determina a cor baseada no nome do status
                status_lower = status.lower()
                if 'andamento' in status_lower or 'progress' in status_lower:
                    status_item.setBackground(QColor("#E6FFE6"))  # Verde muito claro
                elif 'aguardando' in status_lower or 'waiting' in status_lower:
                    status_item.setBackground(QColor("#FFE6E6"))  # Vermelho muito claro
                elif 'pausado' in status_lower or 'paused' in status_lower:
                    status_item.setBackground(QColor("#E6E6FF"))  # Azul muito claro
                
                status_table.setItem(row, col, status_item)
        
        # Add to layout with proper margins
        status_scroll = QScrollArea()
        status_scroll.setWidgetResizable(True)
        status_scroll.setWidget(status_table)
        layout.addWidget(status_scroll)
        
        # Footer with buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        export_btn = QPushButton("Exportar para CSV")
        export_btn.setIcon(QIcon.fromTheme("document-save"))
        export_btn.setStyleSheet("padding: 5px 15px;")
        export_btn.clicked.connect(lambda: self.export_results(results, all_statuses))
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
        
    def export_results(self, results, status_types):
        """Export analysis results to CSV"""
        
        def seconds_to_time_format_util_csv(seconds):
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
        
        try:
            # Create DataFrame
            data = []
            
            for analysis in results:
                row = {
                    'protocol': analysis.get('protocol', ''),
                    'subject': analysis.get('subject', ''),
                    'client': analysis.get('customer_name', ''),
                    'time_to_first_status': seconds_to_time_format_util_csv(analysis.get('business_time_to_first_status', 0)),
                    'time_with_client': seconds_to_time_format_util_csv(analysis.get('time_with_client', 0)),
                    'time_with_support': seconds_to_time_format_util_csv(analysis.get('time_with_support', 0)),
                    'time_in_bug': seconds_to_time_format_util_csv(analysis.get('reclassified_time_in_bug', 0)),
                    'time_ignored': seconds_to_time_format_util_csv(analysis.get('reclassified_time_ignored', 0)),
                    'time_with_client (business)': seconds_to_time_format_util_csv(analysis.get('business_time_with_client', 0)),
                    'time_with_support (business)': seconds_to_time_format_util_csv(analysis.get('business_time_with_support', 0)),
                    'time_in_bug (business)': seconds_to_time_format_util_csv(analysis.get('reclassified_business_time_in_bug', 0)),
                    'time_ignored (business)': seconds_to_time_format_util_csv(analysis.get('reclassified_business_time_ignored', 0)),
                    'current_status': analysis.get('current_situation', '')
                }
                
                # Adiciona informações de SLA
                sla_deadline = analysis.get('sla', {}).get('deadline', {})
                if sla_deadline:
                    sla_date = sla_deadline.get('date', '')
                    sla_accomplished = "Sim" if sla_deadline.get('accomplished') else "Não"
                    row['sla_deadline'] = sla_date
                    row['sla_accomplished'] = sla_accomplished
                
                # Adiciona data de criação e encerramento
                row['creation_date'] = analysis.get('creation_date', '')
                row['end_date'] = analysis.get('end_date', '')
                
                # Add status times
                for status in status_types:
                    # Tempo total no status
                    time_sec = analysis.get('status_time', {}).get(status, 0)
                    time_hours = seconds_to_time_format_util_csv(time_sec)
                    row[f'Status: {status}'] = time_hours
                    
                    # Tempo comercial no status
                    business_time_sec = analysis.get('status_business_time', {}).get(status, 0)
                    business_time_hours = seconds_to_time_format_util_csv(business_time_sec)
                    row[f'Status (comercial): {status}'] = business_time_hours
                    
                data.append(row)
                
            df = pd.DataFrame(data)
            
            # Save to file
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Salvar CSV", 
                f"ticket_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                "CSV Files (*.csv)"
            )
            
            if filename:
                df.to_csv(filename, index=False, encoding='utf-8-sig')  # Usa codificação UTF-8 com BOM para melhor compatibilidade com Excel
                QMessageBox.information(self, "Sucesso na Exportação", f"Dados Exportados para {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erro na Exportação", str(e))

    def show_status_time_help(self):
        """Show help dialog explaining status time calculations"""
        dialog = StatusTimeHelpDialog(self)
        dialog.exec_()

class AnalysisTab(QWidget):
    """Tab for displaying analysis results"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Os resultados da análise aparecerão aqui após o processamento."))
        self.setLayout(layout)

class StatusTimeHelpDialog(QDialog):
    """Dialog to explain how status time calculations are done"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda para cálculo de tempo em status")
        self.setMinimumSize(650, 400)
        
        layout = QVBoxLayout()
        
        # Use a scroll area to handle long text
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Título
        title = QLabel("Como o Tempo em Status é Calculado")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        content_layout.addWidget(title)

        # Explicação principal
        explanation = QLabel(
            "<p><b>Visão Geral:</b> A seção 'Tempo em Status' mostra quanto tempo cada chamado passou em diferentes status "
            "(como 'Em Andamento', 'Pausado', 'Bug com o Fornecedor', etc.), considerando apenas o horário comercial.</p>"
            
            "<p><b>Apenas Horário Comercial:</b> Todos os cálculos de tempo mostrados nesta seção consideram <i>apenas</i> o tempo "
            "dentro do horário comercial definido. Por exemplo, se o horário comercial for de segunda a sexta, das 8:00 às 12:00 "
            "e das 14:00 às 18:00, o tempo fora desse horário (noites, intervalos de almoço, finais de semana) não é contabilizado.</p>"
            
            "<p><b>Feriados Excluídos:</b> Qualquer dia marcado como feriado no sistema é completamente excluído dos "
            "cálculos de tempo, mesmo que normalmente fosse um dia útil.</p>"
            
            "<p><b>Tempo até o Primeiro Status:</b> Esta coluna especial mostra o tempo comercial entre a criação do chamado e "
            "a primeira atribuição de status. Isso ajuda a acompanhar o tempo de resposta inicial.</p>"
            
            "<p><b>Transições de Status:</b> Quando um chamado muda de um status para outro, o sistema registra o "
            "carimbo de data/hora. O tempo em cada status é calculado entre essas transições.</p>"
            
            "<p><b>Status Atual:</b> Para chamados ainda abertos, o tempo no status atual é calculado desde "
            "a última mudança de status até o momento atual.</p>"
            
            "<p><b>Formato de Tempo:</b> Todos os tempos são exibidos no formato HH:MM:SS (horas:minutos:segundos).</p>"
            
            "<p><b>Gerenciar Configurações:</b> Você pode configurar o horário comercial e os feriados usando os botões "
            "'Configurar Horário Comercial' e 'Gerenciar Feriados' na janela principal.</p>"
        )

        explanation.setWordWrap(True)
        explanation.setTextFormat(Qt.RichText)
        content_layout.addWidget(explanation)

        # Seção de exemplo
        example_title = QLabel("Exemplo:")
        example_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        content_layout.addWidget(example_title)

        example = QLabel(
            "Considere um chamado com estas mudanças de status:\n"
            "- Criado na segunda-feira às 9:00\n"
            "- Alterado para 'Em Andamento' na segunda-feira às 10:30\n"
            "- Alterado para 'Aguardando Cliente' na segunda-feira às 14:30\n"
            "- Alterado novamente para 'Em Andamento' na terça-feira às 11:00\n"
            "- Encerrado na terça-feira às 16:00\n\n"
            
            "Com horário comercial das 8:00 às 12:00 e das 13:00 às 17:00 nos dias úteis:\n"
            "- Tempo até o Primeiro Status: 1:30 (de segunda 9:00 até 10:30)\n"
            "- Tempo em 'Em Andamento': 5:30 (seg 10:30-14:30 + ter 11:00-16:00, contando apenas o horário comercial)\n"
            "- Tempo em 'Aguardando Cliente': 3:00 (de seg 14:30 até ter 11:00, contando apenas o horário comercial)"
        )

        example.setWordWrap(True)
        content_layout.addWidget(example)
        
        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Close button
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize config
        self.config_manager = ConfigManager()
        
        # Initialize API client
        token = self.config_manager.get_api_token()
        self.api_client = ApiClient(token)
        
        # Initialize business hours calculator with holidays
        business_hours_config = self.config_manager.get_business_hours()
        holidays = self.config_manager.get_holidays()
        self.calculator = BusinessHoursCalculator(business_hours_config, holidays)
        
        # Initialize ticket analyzer
        self.analyzer = TicketAnalyzer(self.calculator)
        
        # Set window properties
        self.setWindowTitle("Analisador de Tickets de Suporte")
        self.setMinimumSize(1024, 768)
        self.setWindowState(Qt.WindowMaximized)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F0F2F5;
            }
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #EAEAEA;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                border: 1px solid #CCCCCC;
                background-color: #F5F5F5;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
            QLabel {
                color: #333333;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)  # Reduced spacing
        
        # Header with title, logo and config button
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #2C3E50; color: white; border-radius: 4px;")
        header_layout = QHBoxLayout(header_widget)
        
        app_title = QLabel("Analisador de Tickets de Suporte")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        self.toggle_config_btn = QPushButton()
        self.toggle_config_btn.setToolTip("Mostrar/Ocultar Configurações")

        settings_icon = """
        <svg width="16" height="16" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
            <path fill="#ffffff" d="M15.1 7.3l-1.8-1.1c0.1-0.4 0.1-0.9 0.1-1.3s0-0.9-0.1-1.3l1.8-1.1c0.2-0.1 0.2-0.3 0.1-0.5l-1.4-2.4c-0.1-0.2-0.3-0.2-0.5-0.1l-1.8 1.1c-0.7-0.5-1.4-0.9-2.2-1.2l-0.3-2.2c0-0.2-0.2-0.4-0.4-0.4h-2.8c-0.2 0-0.4 0.2-0.4 0.4l-0.3 2.2c-0.8 0.3-1.5 0.7-2.2 1.2l-1.8-1.1c-0.2-0.1-0.4-0.1-0.5 0.1l-1.4 2.4c-0.1 0.2-0.1 0.4 0.1 0.5l1.8 1.1c-0.1 0.4-0.1 0.9-0.1 1.3s0 0.9 0.1 1.3l-1.8 1.1c-0.2 0.1-0.2 0.3-0.1 0.5l1.4 2.4c0.1 0.2 0.3 0.2 0.5 0.1l1.8-1.1c0.7 0.5 1.4 0.9 2.2 1.2l0.3 2.2c0 0.2 0.2 0.4 0.4 0.4h2.8c0.2 0 0.4-0.2 0.4-0.4l0.3-2.2c0.8-0.3 1.5-0.7 2.2-1.2l1.8 1.1c0.2 0.1 0.4 0.1 0.5-0.1l1.4-2.4c0.1-0.2 0.1-0.4-0.1-0.5zM8 11c-1.7 0-3-1.3-3-3s1.3-3 3-3 3 1.3 3 3-1.3 3-3 3z"/>
        </svg>
        """

        # Cria QPixmap a partir do SVG
        pixmap = QPixmap()
        pixmap.loadFromData(settings_icon.encode('utf-8'))
        
        self.toggle_config_btn.setIcon(QIcon(pixmap))

        # Estilo robusto
        self.toggle_config_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                padding: 1px;
                
                qproperty-iconSize: 16px;
                align-items: baseline;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)

        # Garante que o ícone será mostrado
        # self.toggle_config_btn.setIconSize(QSize(12, 12))
        self.toggle_config_btn.clicked.connect(self.toggle_config_panel)
        
        header_layout.addWidget(app_title)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_config_btn)
        
        # Version info
        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #BDC3C7;")
        header_layout.addWidget(version_label)
        
        layout.addWidget(header_widget)
        
        # Configuration Panel (collapsible)
        self.config_panel = QGroupBox("Configurações")
        self.config_panel.setStyleSheet("""
            QGroupBox {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                margin-top: 6px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: #F0F2F5;
            }
        """)
        self.config_panel.setVisible(False)  # Start hidden
        
        config_layout = QVBoxLayout(self.config_panel)
        config_layout.setContentsMargins(5, 5, 5, 5)
        config_layout.setSpacing(5)
        
        # API token section - more compact version
        token_widget = QWidget()
        token_layout = QHBoxLayout(token_widget)
        token_layout.setContentsMargins(5, 5, 5, 5)
        
        token_label = QLabel("API Token:")
        self.token_input = QLineEdit()
        self.token_input.setText(self.config_manager.get_api_token())
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Insira seu token de API")
        self.token_input.setStyleSheet("padding: 3px; border: 1px solid #CCCCCC; border-radius: 3px;")
        
        save_token_btn = QPushButton("Salvar")
        save_token_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                padding: 3px 8px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        save_token_btn.clicked.connect(self.save_token)
        
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(save_token_btn)
        
        config_layout.addWidget(token_widget)
        
        # Tools section - more compact version
        tools_widget = QWidget()
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setContentsMargins(5, 5, 5, 5)
        tools_layout.setSpacing(5)
        
        # Smaller tool buttons
        configure_hours_btn = QPushButton("Horários")
        configure_hours_btn.setIcon(QIcon.fromTheme("calendar"))
        configure_hours_btn.setStyleSheet("padding: 3px 6px;")
        configure_hours_btn.clicked.connect(self.configure_business_hours)
        
        manage_holidays_btn = QPushButton("Feriados")
        manage_holidays_btn.setIcon(QIcon.fromTheme("appointment"))
        manage_holidays_btn.setStyleSheet("padding: 3px 6px;")
        manage_holidays_btn.clicked.connect(self.manage_holidays)
        
        time_calculator_btn = QPushButton("Calculadora")
        time_calculator_btn.setIcon(QIcon.fromTheme("clock"))
        time_calculator_btn.setStyleSheet("padding: 3px 6px;")
        time_calculator_btn.clicked.connect(self.open_time_calculator)
        
        tools_layout.addWidget(configure_hours_btn)
        tools_layout.addWidget(manage_holidays_btn)
        tools_layout.addWidget(time_calculator_btn)
        tools_layout.addStretch()
        
        config_layout.addWidget(tools_widget)
        
        layout.addWidget(self.config_panel)
        
        # Create tab widget with more space
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                margin-top: 5px;
            }
            QTabBar::tab {
                padding: 5px 10px;
            }
        """)
        
        # Create tabs
        from enhanced_results_tab import EnhancedResultsTab
        self.results_tab = EnhancedResultsTab(self.api_client, self.analyzer)
        self.filter_tab = FilterTab(self.api_client, self.results_tab)
        
        tabs.addTab(self.filter_tab, "Filtros de Pesquisa")
        tabs.addTab(self.results_tab, "Resultados")
        
        layout.addWidget(tabs, 1)  # Give more space to tabs
        
        # Status bar
        status_widget = QWidget()
        status_widget.setStyleSheet("""
            background-color: #F5F5F5; 
            border-top: 1px solid #CCCCCC; 
            padding: 2px;
            font-size: 11px;
        """)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        self.help_link = QPushButton("Guia de Uso")
        self.help_link.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #3498DB;
                padding: 0;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #2980B9;
            }
        """)
        self.help_link.setMaximumWidth(100)
        self.help_link.clicked.connect(self.show_user_guide)
        status_layout.addWidget(self.help_link)
        status_layout.addStretch()
        
        # Add a small button to show config panel if hidden
        self.show_config_btn = QPushButton("Configurações")
        self.show_config_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #3498DB;
                padding: 0;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #2980B9;
            }
        """)
        self.show_config_btn.setMaximumWidth(100)
        self.show_config_btn.clicked.connect(self.show_config_panel)
        status_layout.addWidget(self.show_config_btn)
        
        layout.addWidget(status_widget)
        
        central_widget.setLayout(layout)

    def toggle_config_panel(self):
        """Toggle visibility of config panel"""
        is_visible = self.config_panel.isVisible()
        self.config_panel.setVisible(not is_visible)
        self.show_config_btn.setVisible(is_visible)  # Hide the button when panel is visible

    def show_config_panel(self):
        """Show the config panel"""
        self.config_panel.setVisible(True)
        self.show_config_btn.setVisible(False)
        
    def save_token(self):
        """Save API token to config"""
        token = self.token_input.text().strip()
        self.config_manager.set_api_token(token)
        
        # Update API client
        self.api_client = ApiClient(token)
        self.results_tab.api_client = self.api_client
        self.filter_tab.api_client = self.api_client
        
        # Feedback animado
        save_animation = QPropertyAnimation(self.token_input, b"styleSheet")
        save_animation.setDuration(1000)
        save_animation.setStartValue("padding: 5px; border: 1px solid #CCCCCC; border-radius: 3px; background-color: #DFFFDF;")
        save_animation.setEndValue("padding: 5px; border: 1px solid #CCCCCC; border-radius: 3px;")
        save_animation.start()
        
        QMessageBox.information(self, "Token Salvo", "API token foi salvo com sucesso.")
        
    def configure_business_hours(self):
        """Open dialog to configure business hours"""
        dialog = BusinessHoursDialog(self.config_manager, self)
        if dialog.exec_():
            # Update business hours calculator
            business_hours_config = self.config_manager.get_business_hours()
            holidays = self.config_manager.get_holidays()
            self.calculator = BusinessHoursCalculator(business_hours_config, holidays)
            self.analyzer = TicketAnalyzer(self.calculator)
            self.results_tab.analyzer = self.analyzer
            
    def open_time_calculator(self):
        """Open time calculator dialog"""
        # Criar o diálogo como atributo de classe para manter referência
        self.time_calculator_dialog = TimeCalculatorDialog(self.calculator)
        self.time_calculator_dialog.setWindowModality(Qt.NonModal)  # Non-modal dialog
        self.time_calculator_dialog.show()  
        
    def manage_holidays(self):
        """Open dialog to manage holidays"""
        dialog = HolidaysDialog(self.config_manager, self)
        if dialog.exec_():
            # Update business hours calculator with new holidays
            business_hours_config = self.config_manager.get_business_hours()
            holidays = self.config_manager.get_holidays()
            self.calculator = BusinessHoursCalculator(business_hours_config, holidays)
            self.analyzer = TicketAnalyzer(self.calculator)
            self.results_tab.analyzer = self.analyzer
            
    # Adicione este método à classe MainWindow:
    def show_user_guide(self):
        """Exibe um modal com o guia de uso da aplicação"""
        guide_dialog = QDialog(self)
        guide_dialog.setWindowTitle("Guia de Uso - Analisador de Tickets de Suporte")
        guide_dialog.setMinimumSize(800, 600)
        guide_dialog.setWindowState(Qt.WindowMaximized)
        
        layout = QVBoxLayout()
        
        # Usar um scroll area para conteúdo extenso
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        content = QWidget()
        content_layout = QVBoxLayout()
        
        # Cabeçalho
        header = QWidget()
        header.setStyleSheet("background-color: #F5F8FA; border-radius: 6px; padding: 10px;")
        header_layout = QVBoxLayout()
        
        title = QLabel("Guia de Uso: Analisador de Tickets de Suporte")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2C3E50;")
        
        description = QLabel("Este guia detalha todas as funcionalidades do Analisador de Tickets de Suporte, incluindo configuração inicial, uso diário e solução de problemas comuns.")
        description.setWordWrap(True)
        description.setStyleSheet("color: #7F8C8D; font-size: 13px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(description)
        header.setLayout(header_layout)
        content_layout.addWidget(header)
        
        # Conteúdo do guia
        guide_text = QTextEdit()
        guide_text.setReadOnly(True)
        guide_text.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        
        # Conteúdo do guia em HTML
        guide_content = """
    <h2>Resumo</h2>

    <h3>Primeiros Passos</h3>
    <ul>
    <li>Configuração do Token API</li>
    <li>Configuração de Horário Comercial</li>
    <li>Gestão de Feriados</li>
    </ul>

    <h3>Funcionamento Básico</h3>
    <ul>
    <li>Busca de Tickets de Suporte</li>
    <li>Análise de Tickets</li>
    <li>Visualização de Resultados</li>
    </ul>

    <h3>Recursos Avançados</h3>
    <ul>
    <li>Classificação Manual de Interações</li>
    <li>Calculadora de Tempo</li>
    <li>Exportação de Dados (csv)</li>
    </ul>

    <h3>Conceitos Importantes</h3>
    <ul>
    <li>Lógica de Cálculo de Tempo</li>
    <li>Classificação de Interações</li>
    <li>Tempo Comercial x Tempo Total</li>
    </ul>

    <h3>Solução de Problemas</h3>
    <ul>
    <li>Erros Comuns</li>
    <li>Limites da API</li>
    <li>Perguntas Frequentes</li>
    </ul>

    <hr>

    <h2>Primeiros Passos</h2>

    <h3>Configuração do Token API</h3>

    <ol>
    <li>Abra o painel de configurações clicando no ícone ⚙️, posicionado no canto superior direito (ou em "Configurações no canto inferior direito").</li>
    <li>Na seção "API Token", cole seu token de acesso.</li>
    <li>Clique em <b>Salvar</b>.</li>
    </ol>

    <blockquote>
    <p><b>Nota:</b> Para obter o token da API do TomTicket, acesse: Configurações &gt; API &gt; Gerar Token (https://tomticket.tomticket.com/kb/introducao/criacao-do-token-de-acesso).</p>
    </blockquote>

    <h3>Configuração de Horário Comercial</h3>

    <ol>
    <li>No painel de configurações, clique em <b>Horários</b>.</li>
    <li>Configure os horários comerciais por dia da semana.</li>
    <li>É possível adicionar múltiplos intervalos por dia (ex: 08:00-12:00 e 14:00-18:00).</li>
    <li>Deixe em branco os dias não úteis.</li>
    <li>Clique em <b>Salvar</b>.</li>
    </ol>

    <p><b>Exemplo padrão:</b></p>
    <ul>
    <li>Segunda a Sexta: 08h00-12h00, 14h00-18h00</li>
    <li>Sábado e Domingo: Sem horário comercial</li>
    </ul>

    <h3>Gestão de Feriados</h3>

    <ol>
    <li>Vá em <b>Feriados</b> no painel de configurações.</li>
    <li>Para adicionar um feriado:
    <ul>
    <li>Selecione a data no calendário</li>
    <li>Insira uma descrição</li>
    <li>Clique em <b>Adicionar Feriado</b></li>
    </ul>
    </li>
    <li>Para excluir, clique em <b>Excluir</b> ao lado do item.</li>
    <li>Clique em <b>Importar Feriados Nacionais</b> para carregar feriados automaticamente.</li>
    </ol>

    <p><b>Nota:</b> É de estrema importância o cadastro correto de feriados, pois serão utilizados nos cálculos dos tempos que consideram dias e horários comercias. O uso incorreto poderá ocasionar divergências!</p>

    <hr>

    <h2>Funcionamento Básico</h2>

    <h3>Busca de Tickets</h3>

    <ol>
    <li>Na aba <b>Filtros de Pesquisa</b>, defina:
    <ul>
    <li>Período</li>
    <li>Situação</li>
    <li>Prioridade</li>
    <li>Categoria</li>
    </ul>
    <p><b>Dica:</b> No filtro 'Período', a data final deve ser inferior a data atual.</p>
    </li>
    <li>Clique em <b>Pesquisar Tickets</b>.</li>
    </ol>

    <blockquote>
    <p><b>Dica:</b> Use períodos curtos para resultados mais rápidos (limite da API: 50 tickets por consulta).</p>
    </blockquote>

    <h3>Análise de Tickets</h3>

    <ol>
    <li>Na aba <b>Resultados</b>, selecione os tickets desejados.</li>
    <li>Clique em <b>Analisar Selecionados</b>.</li>
    <li>Escolha entre:
    <ul>
    <li><b>Ver Resumo</b></li>
    <li><b>Classificar Interações</b></li>
    </ul>
    </li>
    </ol>

    <h3>Visualização de Resultados</h3>

    <p>Inclui:</p>
    <ul>
    <li>Tempo total e comercial (cliente e suporte)</li>
    <li>Tempo em status</li>
    <li>Tempo até primeiro status</li>
    </ul>

    <p>Passe o mouse sobre os valores para detalhes.</p>

    <hr>

    <h2>Recursos Avançados</h2>

    <h3>Classificação Manual de Interações</h3>

    <ol>
    <li>Após análise, clique em <b>Classificar Interações</b>.</li>
    <li>Selecione o ticket.</li>
    <li>Navegue pelas interações.</li>
    <li>Para reclassificar:
    <ul>
    <li><code>C</code>: Cliente</li>
    <li><code>A</code>: Suporte</li>
    <li><code>B</code>: Bug</li>
    <li><code>I</code>: Ignorar</li>
    </ul>
    </li>
    <li>Marque como <b>Analisado</b> e clique em <b>Aplicar Alterações</b>.</li>
    </ol>

    <blockquote>
    <p><b>Importante:</b> A classificação afeta os cálculos. Veja <i>Lógica de Cálculo de Tempo</i>.</p>
    <p><b>Importante:</b> Após a classificação e a aplicação das alterações clicando em <b>Aplicar Alterações</b>, a tela de Resumo será aberta. Nesse momento, os dados poderão ser exportados. Se essa tela for fechada, as classificaçõe serão perdidas e deverão ser refeitas, ou seja, <b>o sistema não grava os resultados nem armazena as alterações!</b></p>
    </blockquote>

    <h3>Calculadora de Tempo (utilitário)</h3>

    <ol>
    <li>Clique em <b>Calculadora de Tempos/Período</b>.</li>
    <li>Insira datas e horários (AAAA-MM-DD HH:MM).</li>
    <li>Clique em <b>Calcular</b>.</li>
    </ol>

    <p>Resultados:</p>
    <ul>
    <li>Diferença total</li>
    <li>Tempo em horário comercial</li>
    </ul>

    <p>Você pode acumular múltiplos cálculos.</p>

    <h3>Exportação de Dados</h3>

    <ol>
    <li>Clique em <b>Exportar para CSV</b> na tela de resultados.</li>
    <li>Escolha o local de salvamento.</li>
    </ol>

    <p>Inclui:</p>
    <ul>
    <li>Resumo da análise</li>
    <li>Intervalos entre interações</li>
    <li>Lista de interações</li>
    </ul>

    <blockquote>
    <p><b>Importante:</b> Também é possível exportar um ticket individual na tela de <b>Classificar Interações</b>. Nessa tela, a exportação é individual por ticket selecionado, e o arquivo exportado terá todas as informações de classificação, datas, descrição, alterações, tempos, etc.</p>
    <p><b>Dica:</b> Use esse esportação para manter um backup do registro das classificações dos tickets, para consultas futuras, auditoria e etc.</p>
    </blockquote>

    <hr>

    <h2>Conceitos Importantes</h2>

    <h3>Lógica de Cálculo de Tempo</h3>

    <ul>
    <li>O tempo entre interações é atribuído a quem tinha o ticket no início.</li>
    </ul>

    <p><b>Exemplo:</b></p>
    <ul>
    <li>10:00 Cliente cria (<code>C</code>)</li>
    <li>11:00 Suporte responde (<code>A</code>)</li>
    <li>14:00 Cliente responde (<code>C</code>)</li>
    </ul>

    <p><b>Atribuição:</b></p>
    <ul>
    <li>10:00–11:00: Suporte</li>
    <li>11:00–14:00: Cliente</li>
    </ul>

    <p><b>Classificações Especiais:</b></p>
    <ul>
    <li><code>B</code>: Bug</li>
    <li><code>I</code>: Ignorar</li>
    </ul>

    <h3>Classificação de Interações</h3>

    <p>Tipos:</p>
    <ul>
    <li><code>C</code>: Cliente</li>
    <li><code>A</code>: Suporte</li>
    <li><code>B</code>: Bug</li>
    <li><code>I</code>: Ignorar</li>
    </ul>

    <p>A classificação automática pode ser ajustada manualmente.</p>

    <h3>Tempo Comercial x Tempo Total</h3>

    <ul>
    <li><b>Tempo Total</b>: todo o tempo entre interações</li>
    <li><b>Tempo Comercial</b>: apenas o tempo em horário comercial</li>
    </ul>

    <p>Tempo comercial exclui:</p>
    <ul>
    <li>Fora do expediente</li>
    <li>Finais de semana</li>
    <li>Feriados</li>
    </ul>

    <hr>

    <h2>Solução de Problemas</h2>

    <h3>Erros Comuns</h3>

    <p><b>Token inválido</b></p>
    <ul>
    <li>Verifique o token inserido</li>
    <li>Gere um novo token se necessário</li>
    </ul>

    <p><b>Parâmetros inválidos</b></p>
    <ul>
    <li>Verifique formatos e filtros</li>
    </ul>

    <p><b>Sem resultados</b></p>
    <ul>
    <li>Verifique se há tickets disponíveis</li>
    <li>Tente com apenas um ticket</li>
    </ul>

    <h3>Limites da API</h3>

    <ul>
    <li>Máx. 50 tickets por consulta</li>
    <li>Máx. 100 requisições por minuto</li>
    <li>Timeout após 30s</li>
    </ul>

    <blockquote>
    <p>O sistema tenta automaticamente novas tentativas ao atingir limites.</p>
    </blockquote>

    <h3>Perguntas Frequentes</h3>

    <p><b>P: Por que os tempos calculados são diferentes do TomTicket?</b><br>
    R: O app usa lógica de posse e horário comercial.</p>

    <p><b>P: É possível analisar dados antigos?</b><br>
    R: Sim, se acessíveis pela API.</p>

    <p><b>P: Como resolver o erro de limite de requisições?</b><br>
    R: Reduza a quantidade de tickets analisados por vez.</p>

    <p><b>P: Os dados são salvos localmente?</b><br>
    R: Apenas configurações; os resultados <b>precisam ser exportados</b> para manter um backup local.</p>

    <p><b>P: Como recalcular após reclassificar?</b><br>
    R: Clique em <b>Recalcular Tempos</b> após ajustes.</p>

    <p><b>P: Na tela de Classificação dos Tickets, como identificar as alterações feitas até o momento, no ticket selecionado?</b><br>
    R: Clique na aba <b>Lista de Interações</b> e verifique na na lista as colunas `Tipo Original` e `Classificação Atual`. Nessas colunas, quando uma alteração for feita, estaão com valores diferentes e destaca em amarelo.</p>

    <p><b>P: Na tela de Classificação dos Tickets, como posso voltar um ticket para o status orignal, desfazendo as alterções de classificação?</b><br>
    R: Clique na aba <b>Lista de Interações</b> e verifique na na lista as colunas `Tipo Original` e `Classificação Atual`. Essas colunas irão indicar as alterações feitas até o momento, marcando a coluna `Classificação Atual` em amarelo. Para desfazer as alterações, clique no botão `Resetar para Original`. Essa ação afeta apenas o ticket selecionado.</p>

    <p><b>P: Na tela de Classificação dos Tickets, como posso verificar os tempos calculados para o cliente, suporte, etc?</b><br>
    R: Na parte inferior da tela de <b>Classificação de Interações</b> é exibido uma sessão `Comparação de Métricas de Tempos`. A sessão exibe dinamicamente os cáclulos separados por Cliente, Suporte, Bug e Ignorado, conabilizadas por Tempo Comercial e Tempo Normal. A coluna `Orignal` exibe o cálculo automático inicial (se mantem estática). Já a coluna `Após Reclassificação`, é atualizada a cada alteração de classificação (inicialmente carregado igualmente com os valores da coluna Original). A coluna `Diferençã` exibe as diferêncas a cada alteração de classificação (positiva ou negativa). A coluna `Preview` exibe o resultado final após as alterações (gerlamente igual a coluna Após Reclassificação).</p>

    <hr>

    <p>Para mais informações ou suporte, entre em contato com o desenvolvedor <a href="mailto:thiago.paraizo@scalait.com">thiago.paraizo@scalait.com</a>.</p>
    """
        
        guide_text.setHtml(guide_content)
        content_layout.addWidget(guide_text)
        
        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Botão fechar
        close_btn = QPushButton("Fechar")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498DB;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
        """)
        close_btn.clicked.connect(guide_dialog.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        guide_dialog.setLayout(layout)
        guide_dialog.exec_()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Instala o classificador aprimorado
    install_enhanced_classifier()
    
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()