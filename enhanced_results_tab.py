import time
from ticket_analyzer import ResultsTab, QMessageBox, QDialog, QApplication
from enhanced_classifier import InteractionClassifierDialogUpdated

class EnhancedResultsTab(ResultsTab):
    """Versão melhorada do ResultsTab que usa o diálogo de classificação aprimorado"""
    
    def analyze_selected(self):
        """Versão aprimorada de analyze_selected que usa o novo diálogo"""
        print("EXECUTANDO analyze_selected APRIMORADO!")
        
        selected_ids = self.get_selected_tickets()
        
        if not selected_ids:
            QMessageBox.warning(self, "Seleção Inválida", "Selecione pelo menos um ticket para analisar.")
            return
            
        # Progress dialog melhorado
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt

        # Criar um diálogo de progresso personalizado
        progress = QProgressDialog("Analisando tickets, aguarde...", None, 0, 0)
        progress.setWindowTitle("Processando")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)  # Mostrar imediatamente
        progress.setMinimumWidth(300)
        progress.setAutoClose(True)
        progress.setWindowFlags(progress.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        progress.setStyleSheet("""
            QProgressDialog {
                background-color: #F5F8FA;
                border: 1px solid #E0E0E0;
                border-radius: 6px;
            }
            QLabel {
                font-size: 13px;
                color: #2C3E50;
                padding: 10px;
            }
            QProgressBar {
                border: 1px solid #BBDEFB;
                border-radius: 4px;
                background-color: #E3F2FD;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                width: 20px;
            }
        """)
        progress.show()
        QApplication.processEvents()
        
        try:
            analysis_results = []
        
            for i, ticket_id in enumerate(selected_ids):
                # Atualiza barra de progresso
                progress.setValue(i)
                progress.setLabelText(f"Analisando ticket {i+1} de {len(selected_ids)}...")
                QApplication.processEvents()
                
                if progress.wasCanceled():
                    break
                
                # Tenta obter os detalhes com retry em caso de erro 429
                max_retries = 3
                retry_count = 0
                retry_delay = 2  # segundos iniciais
                
                while retry_count < max_retries:
                    try:
                        response = self.api_client.get_ticket_details(ticket_id)
                        
                        if not response.get('error', True):
                            # Sucesso! Analisa e adiciona ao resultado
                            ticket_data = response.get('data', {})
                            analysis = self.analyzer.analyze_ticket(ticket_data)
                            analysis_results.append(analysis)
                            break  # Sai do loop de retry
                        elif "429" in str(response.get('message', '')):
                            # Erro 429, implementa retry com backoff
                            retry_count += 1
                            if retry_count < max_retries:
                                wait_time = retry_delay * (2 ** (retry_count - 1))  # Backoff exponencial
                                progress.setLabelText(f"Limite de requisições atingido. Tentando novamente em {wait_time} segundos...")
                                
                                # Conta regressiva visual
                                for sec in range(wait_time, 0, -1):
                                    if progress.wasCanceled():
                                        break
                                    progress.setLabelText(f"Limite de requisições atingido. Tentando novamente em {sec} segundos...")
                                    QApplication.processEvents()
                                    time.sleep(1)
                                    
                                if progress.wasCanceled():
                                    break
                            else:
                                QMessageBox.warning(
                                    self, 
                                    "Limite de API", 
                                    f"Erro ao obter detalhes do ticket {ticket_id}: Limite de requisições atingido após várias tentativas."
                                )
                                break
                        else:
                            # Outros erros
                            QMessageBox.warning(
                                self, 
                                "API Error", 
                                f"Erro ao obter detalhes do ticket {ticket_id}: {response.get('message', 'Erro desconhecido')}"
                            )
                            break
                            
                    except Exception as e:
                        # Erro geral
                        retry_count += 1
                        if retry_count >= max_retries:
                            QMessageBox.critical(self, "Erro", f"Falha na requisição após {max_retries} tentativas: {str(e)}")
                            break
            
            progress.setValue(len(selected_ids))
                    
            # Close progress
            progress.close()
            
            # If we have results to show
            if analysis_results:
                # Diálogo de escolha de ação melhorado
                from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
                from PyQt5.QtGui import QIcon, QPixmap

                # Criar um diálogo personalizado em vez de QMessageBox
                action_dialog = QDialog()
                action_dialog.setWindowTitle("Resultados da Análise")
                action_dialog.setWindowModality(Qt.ApplicationModal)
                action_dialog.setMinimumWidth(400)
                action_dialog.setStyleSheet("""
                    QDialog {
                        background-color: #F5F8FA;
                        border-radius: 6px;
                    }
                    QLabel#title {
                        font-size: 16px;
                        font-weight: bold;
                        color: #2C3E50;
                    }
                    QLabel#description {
                        color: #5D6D7E;
                        margin-bottom: 15px;
                    }
                    QPushButton {
                        padding: 10px;
                        border-radius: 4px;
                        font-weight: bold;
                    }
                    QPushButton#summary {
                        background-color: #3498DB;
                        color: white;
                    }
                    QPushButton#summary:hover {
                        background-color: #2980B9;
                    }
                    QPushButton#classify {
                        background-color: #2ECC71;
                        color: white;
                    }
                    QPushButton#classify:hover {
                        background-color: #27AE60;
                    }
                    QPushButton#cancel {
                        background-color: #ECF0F1;
                        color: #7F8C8D;
                        border: 1px solid #BDC3C7;
                    }
                    QPushButton#cancel:hover {
                        background-color: #D0D3D4;
                    }
                """)

                layout = QVBoxLayout()

                # Título e descrição
                title = QLabel("Análise Concluída")
                title.setObjectName("title")
                description = QLabel("Os tickets foram analisados com sucesso. O que você gostaria de fazer agora?")
                description.setObjectName("description")
                description.setWordWrap(True)

                layout.addWidget(title)
                layout.addWidget(description)

                # Botões 
                button_layout = QHBoxLayout()

                summary_btn = QPushButton("Ver Resumo")
                summary_btn.setObjectName("summary")
                summary_btn.setMinimumWidth(120)

                classify_btn = QPushButton("Classificar Interações")
                classify_btn.setObjectName("classify")
                classify_btn.setMinimumWidth(120)

                cancel_btn = QPushButton("Cancelar")
                cancel_btn.setObjectName("cancel")

                button_layout.addWidget(summary_btn)
                button_layout.addWidget(classify_btn)
                button_layout.addWidget(cancel_btn)

                layout.addLayout(button_layout)
                action_dialog.setLayout(layout)

                # Conectar sinais
                result_code = -1  # Valor padrão caso o diálogo seja fechado

                summary_btn.clicked.connect(lambda: setattr(action_dialog, 'result_code', 0))
                summary_btn.clicked.connect(action_dialog.accept)

                classify_btn.clicked.connect(lambda: setattr(action_dialog, 'result_code', 1))
                classify_btn.clicked.connect(action_dialog.accept)

                cancel_btn.clicked.connect(lambda: setattr(action_dialog, 'result_code', 2))
                cancel_btn.clicked.connect(action_dialog.reject)

                # Executar diálogo
                action_dialog.exec_()
                action = getattr(action_dialog, 'result_code', 2)  # 2 = cancelar por padrão
                
                if action == 0:  # View Summary
                    # Mostra o resumo com os dados originais
                    self.show_analysis_results(analysis_results)
                    
                elif action == 1:  # Classify Interactions
                    # AQUI ESTÁ A MUDANÇA: Usar InteractionClassifierDialogUpdated em vez de InteractionClassifierDialog
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
            import traceback
            traceback.print_exc()
            progress.close()
            QMessageBox.critical(self, "Error", str(e))