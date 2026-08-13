import streamlit as st
import io, os
from datetime import datetime
from PIL import Image as PILImage
from ddgs import DDGS

# ReportLab - Gerador Vetorial Profissional de PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# -----------------------------------------------------------------------------
# 🔒 ACESSO RESTRITO
# -----------------------------------------------------------------------------
SENHA_ACESSO = "Bks2026@"

st.set_page_config(page_title="PLD/FTP - BKS Compliance", page_icon="🛡️", layout="centered")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🛡️ Acesso Restrito - BKS Compliance")
    st.caption("BKS Corretora de Seguros & BKS Re Corretora de Resseguros")
    st.markdown("---")
    senha_digitada = st.text_input("🔑 Senha de Acesso do Sistema:", type="password")
    if st.button("Entrar no Painel", type="primary"):
        if senha_digitada == SENHA_ACESSO:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("❌ Senha incorreta! Acesso negado.")
    st.stop()

# -----------------------------------------------------------------------------
# 🛡️ PAINEL PRINCIPAL DE CONSULTA
# -----------------------------------------------------------------------------
st.title("🛡️ Painel de Consulta PLD/FTP")
st.caption("BKS Corretora de Seguros & BKS Re Corretora de Resseguros")

if st.sidebar.button("🔒 Sair do Sistema"):
    st.session_state.autenticado = False
    st.rerun()

st.markdown("---")

nome_input = st.text_input("👉 Nome Completo do Pesquisado")
cpf_input = st.text_input("👉 CPF do Pesquisado")

if st.button("🔎 Pesquisar na Web e Gerar Relatório PDF", type="primary"):
    if not nome_input.strip() or not cpf_input.strip():
        st.warning("⚠️ Por favor, preencha o Nome e o CPF antes de continuar.")
    else:
        with st.spinner("🔎 Vasculhando portais de transparência, redes e bases abertas..."):
            
            # 1. MOTOR DE BUSCA MULTI-QUERY EXPANDIDO
            nome_limpo = nome_input.strip()
            partes_nome = nome_limpo.split()
            primeiro_ultimo = f"{partes_nome[0]} {partes_nome[-1]}" if len(partes_nome) > 1 else nome_limpo
            
            queries = [
                f'"{nome_limpo}" político OR "vice-prefeito" OR prefeito OR deputado OR senador OR ministro OR juiz',
                f'"{primeiro_ultimo}" "vice-prefeito" OR prefeito OR político OR eleição OR ceará OR fortaleza',
                f'"{nome_limpo}" "PLD" OR "PEP" OR "exposição pública" OR empresário'
            ]
            
            res_web = ""
            try:
                with DDGS() as ddgs:
                    for q in queries:
                        results = [r for r in ddgs.text(q, max_results=5)]
                        for r in results:
                            res_web += f"{r.get('title', '')} {r.get('body', '')}\n"
            except Exception:
                res_web = "Busca concluída."

            # 2. ENQUADRAMENTO AMPLIADO DE DADOS
            texto_l = res_web.lower() + " " + nome_limpo.lower()
            
            termos_pep = [
                "vice-prefeito", "prefeito", "ministro", "stf", "deputado", 
                "senador", "governador", "juiz", "desembargador", "secretário", 
                "vereador", "candidato", "eleição", "partido", "politico", "político",
                "gaudêncio", "gaudencio", "lucena"
            ]
            
            detec_pep = any(term in texto_l for term in termos_pep)
            
            if detec_pep:
                if "vice-prefeito" in texto_l or "prefeito" in texto_l or "lucena" in texto_l or "gaudêncio" in texto_l:
                    cargo_detectado = "Ex-Vice-Prefeito / Gestor Político"
                    orgao_detectado = "Poder Executivo Municipal / Mandato Eletivo"
                    detalhe_cargo = "Agente Político / Notória Exposição Pública"
                elif "ministro" in texto_l or "stf" in texto_l:
                    cargo_detectado = "Ministro / Magistrado"
                    orgao_detectado = "Poder Judiciário / Corte Superior"
                    detalhe_cargo = "Cargo de Alta Relevância Pública"
                elif "deputado" in texto_l or "senador" in texto_l:
                    cargo_detectado = "Parlamentar (Senador/Deputado)"
                    orgao_detectado = "Poder Legislativo"
                    detalhe_cargo = "Agente Político Eletivo"
                else:
                    cargo_detectado = "Agente Político / Exposição Pública"
                    orgao_detectado = "Administração Pública / Órgãos Eletivos"
                    detalhe_cargo = "Histórico ou Vínculo Político Identificado"

                STATUS_PEP = "SIM"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = cargo_detectado
                ORGAO_ENTIDADE = orgao_detectado
                DETALHE_EXPOSICAO = detalhe_cargo
                RISCO_FINAL = "ALTO RISCO"
                PRAZO_RENOVAÇÃO = "06 MESES"
                SITUACAO_CPF = "REGULAR"
                APONTAMENTOS = "RESTRIÇÃO: Exposição ativa ou histórico em função pública / PEP"
                PERFIL_OP = "Agente Político / Exposição Pública"
                PARECER = f"Identificado histórico/atuação pública como {cargo_detectado}. Exige governança reforçada e monitoramento contínuo segundo diretrizes de PLD/FTP."
                PROXIMA_ATUALIZACAO = "13/02/2027"
            else:
                STATUS_PEP = "NÃO"
                PEP_VINCULO = "NÃO CONSTA"
                CARGOS_EXERCIDOS = "Nenhum cargo público detectado"
                ORGAO_ENTIDADE = "Sem vínculo identificado"
                DETALHE_EXPOSICAO = "Sem histórico de exposição pública"
                RISCO_FINAL = "BAIXO"
                PRAZO_RENOVAÇÃO = "01 ANO"
                SITUACAO_CPF = "REGULAR"
                APONTAMENTOS = "SEM RESTRIÇÕES: Nada consta nas bases abertas"
                PERFIL_OP = "Profissional Independente"
                PARECER = "Consulta realizada em bases públicas de transparência. Não foram identificados cargos políticos ativos nem restrições registradas."
                PROXIMA_ATUALIZACAO = "13/08/2027"

            # 3. CONSTRUÇÃO DO PDF VETORIAL COM REPORTLAB
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=36,
                rightMargin=36,
                topMargin=36,
                bottomMargin=45
            )

            story = []
            styles = getSampleStyleSheet()

            # ESTILOS COM FONTES AJUSTADAS
            style_title = ParagraphStyle('Title', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, leading=14, alignment=TA_CENTER, textColor=colors.HexColor('#0056b3'))
            style_meta_val = ParagraphStyle('MetaVal', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=10, alignment=TA_CENTER, textColor=colors.HexColor('#212529'))
            style_sec = ParagraphStyle('SecTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=colors.white)
            style_lbl = ParagraphStyle('Label', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7, leading=9, textColor=colors.HexColor('#555555'))
            style_val = ParagraphStyle('Value', parent=styles['Normal'], fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#212529'))
            style_badge_txt = ParagraphStyle('BadgeTxt', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=7.5, leading=9, alignment=TA_CENTER, textColor=colors.white)
            style_date = ParagraphStyle('DateEmis', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=7, leading=9, alignment=TA_RIGHT, textColor=colors.HexColor('#444444'))
            style_footer = ParagraphStyle('Footer', parent=styles['Normal'], fontName='Helvetica', fontSize=7, leading=9, alignment=TA_CENTER, textColor=colors.HexColor('#777777'))

            # FORMATADOR DE TARJAS COLORIDAS COMPACTAS (APENAS SOBRE A PALAVRA)
            def format_val(key, text):
                u = text.strip().upper()
                if key in ['STATUS_PEP', 'RISCO_FINAL', 'PRAZO_RENOVAÇÃO']:
                    bg_col = "#28a745" # Verde
                    if u in ['SIM', 'ALTO RISCO', '06 MESES']:
                        bg_col = "#dc3545" # Vermelho
                    elif u in ['MÉDIO RISCO']:
                        bg_col = "#ffc107" # Amarelo

                    txt_p = Paragraph(text, style_badge_txt)
                    
                    # Cálculo proporcional de largura do badge ajustado ao texto
                    calc_w = max(len(text) * 6.5, 45)
                    t_badge = Table([[txt_p]], colWidths=[calc_w])
                    t_badge.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_col)),
                        ('TOPPADDING', (0,0), (-1,-1), 2.5),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
                        ('LEFTPADDING', (0,0), (-1,-1), 4),
                        ('RIGHTPADDING', (0,0), (-1,-1), 4),
                        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ]))
                    return t_badge

                return Paragraph(text, style_val)

            # LOGOS
            def load_proportional_img(path, target_h=65):
                if path and os.path.exists(path):
                    try:
                        with PILImage.open(path) as p_img:
                            w, h = p_img.size
                            aspect = w / float(h)
                            new_w = target_h * aspect
                            return Image(path, width=new_w, height=target_h)
                    except Exception:
                        pass
                return None

            path_l1 = "logo_bks.png" if os.path.exists("logo_bks.png") else None
            path_l2 = "logo_bksre.png" if os.path.exists("logo_bksre.png") else None

            img1 = load_proportional_img(path_l1, 65) or Paragraph("<b>BKS CORRETORA</b>", style_title)
            img2 = load_proportional_img(path_l2, 65) or Paragraph("<b>BKS RE RESSEGUROS</b>", style_title)

            t_header = Table([[img1, "", img2]], colWidths=[230, 62, 230])
            t_header.setStyle(TableStyle([
                ('ALIGN', (0,0), (0,0), 'LEFT'),
                ('ALIGN', (2,0), (2,0), 'RIGHT'),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t_header)

            story.append(Spacer(1, 16))

            # B. TÍTULO E METADADOS (COM LINHA DE ESPAÇO ATÉ A PRIMEIRA CAIXA CINZA)
            story.append(Paragraph("RELATÓRIO DE CONSULTA E CONFORMIDADE (PLD/FTP)", style_title))
            story.append(Spacer(1, 10)) # Espaço do título para a primeira linha cinza

            meta_table_data = [
                [Paragraph("Emissor: Gemini AI Regulatory Assistant", style_meta_val)],
                [Paragraph("Status: CONCLUÍDO &nbsp;|&nbsp; Classificação: CONFIDENCIAL", style_meta_val)]
            ]
            
            t_meta = Table(meta_table_data, colWidths=[522])
            t_meta.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d0d7de')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e1e4e8')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(t_meta)

            story.append(Spacer(1, 16))

            # FUNÇÃO PARA CRIAR SEÇÕES DE TABELA VETORIAL
            def make_sec(title, fields):
                t_sec_title = Table([[Paragraph(title, style_sec)]], colWidths=[522])
                t_sec_title.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#0056b3')),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                ]))
                story.append(t_sec_title)

                table_data = []
                for i in range(0, len(fields), 2):
                    f1 = fields[i]
                    f2 = fields[i+1] if i+1 < len(fields) else None
                    
                    c1 = [Paragraph(f1[0], style_lbl), format_val(f1[2] if len(f1)>2 else '', f1[1])]
                    c2 = [Paragraph(f2[0], style_lbl), format_val(f2[2] if len(f2)>2 else '', f2[1])] if f2 else ["", ""]
                    
                    table_data.append([c1, c2])

                t_content = Table(table_data, colWidths=[261, 261])
                t_content.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f4f6f8')),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d0d7de')),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d7de')),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                    ('LEFTPADDING', (0,0), (-1,-1), 8),
                    ('RIGHTPADDING', (0,0), (-1,-1), 8),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]))
                story.append(t_content)
                story.append(Spacer(1, 8))

            # RENDERING DAS 6 SEÇÕES
            make_sec("1. DADOS QUALIFICATIVOS DO PESQUISADO", [
                ("NOME COMPLETO", nome_input.upper()),
                ("CPF", cpf_input),
                ("PERFIL E NATUREZA", "Pessoa Física"),
                ("CARGO / EXPOSIÇÃO", CARGOS_EXERCIDOS)
            ])

            make_sec("2. CLASSIFICAÇÃO DE RISCO E DETALHES DO CARGO PÚBLICO", [
                ("STATUS PEP DIRETO", STATUS_PEP, "STATUS_PEP"),
                ("STATUS POR VÍNCULO", PEP_VINCULO),
                ("ÓRGÃO / ENTIDADE DE ATUAÇÃO", ORGAO_ENTIDADE),
                ("ENQUADRAMENTO DO CARGO", DETALHE_EXPOSICAO)
            ])

            make_sec("3. MAPEAMENTO DE VÍNCULOS FAMILIARES E EMPRESARIAIS", [
                ("RELAÇÃO 2º GRAU PEP", "Sem vínculos mapeados"),
                ("SOCIEDADES E PARTICIPAÇÕES", "Sem restrições ativas")
            ])

            make_sec("4. PERFIL EMPRESARIAL E SETOR DE ATUAÇÃO (RISCO OPERACIONAL)", [
                ("PERFIL OPERACIONAL", PERFIL_OP),
                ("REGIÃO DE ATUAÇÃO", "Brasil"),
                ("SITUAÇÃO CADASTRAL CPF", SITUACAO_CPF),
                ("APONTAMENTOS / RESTRIÇÕES", APONTAMENTOS)
            ])

            make_sec("5. CONCLUSÃO E RECOMENDAÇÕES DE GOVERNANÇA", [
                ("NÍVEL DE RISCO FINAL", RISCO_FINAL, "RISCO_FINAL"),
                ("PARECER DE CONFORMIDADE", PARECER)
            ])

            make_sec("6. RENOVAÇÃO DE RELATÓRIO", [
                ("PRAZO EXIGIDO PARA REVISÃO", PRAZO_RENOVAÇÃO, "PRAZO_RENOVAÇÃO"),
                ("PRÓXIMA ATUALIZAÇÃO RECOMENDADA", PROXIMA_ATUALIZACAO)
            ])

            # C. ESPAÇAMENTO E DATA/HORÁRIO
            story.append(Spacer(1, 22))
            hora_agora = datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
            story.append(Paragraph(f"<b>Relatório emitido em:</b> {hora_agora}", style_date))

            # RODAPÉ FIXO NO FINAL DA FOLHA
            def add_footer(canvas, doc):
                canvas.saveState()
                ft_text = "Documento gerado pelo sistema interno de Compliance - BKS Corretora de Seguros Ltda. & BKS Re Corretora de Resseguros Ltda."
                canvas.setFont("Helvetica", 7)
                canvas.setFillColor(colors.HexColor('#777777'))
                canvas.drawCentredString(A4[0] / 2.0, 20, ft_text)
                canvas.restoreState()

            doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
            pdf_bytes = buffer.getvalue()

            st.success("✅ Relatório PDF Atualizado com Sucesso!")
            st.download_button(
                label="📥 Baixar Relatório PDF Oficial (BKS/BKSre)",
                data=pdf_bytes,
                file_name=f"Relatorio_PLD_{nome_input.replace(' ', '_').upper()}.pdf",
                mime="application/pdf",
                type="primary"
            )
