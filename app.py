def buscar_na_planilha_pep(nome_input, cpf_input):
    caminho_final = identificar_arquivo_pep()
    if not caminho_final:
        return None

    nome_norm = normalizar_texto(nome_input)
    if not nome_norm or len(nome_norm.split()) < 2:
        return None

    cpf_numeros = re.sub(r'\D', '', cpf_input)
    miolo_cpf = cpf_numeros[3:9] if len(cpf_numeros) == 11 else ""

    try:
        with open(caminho_final, mode='r', encoding='utf-8', errors='ignore') as f:
            primeira_linha = f.readline()
            sep = ';' if ';' in primeira_linha else (',' if ',' in primeira_linha else '\t')
            f.seek(0)

            reader = csv.DictReader(f, delimiter=sep)
            for row in reader:
                nome_pep_row = row.get('Nome_PEP') or row.get('NOME_PEP') or row.get('Nome') or row.get('NOME') or ""
                nome_pep_norm = normalizar_texto(nome_pep_row)

                # Comparação exata de Nome
                if nome_norm == nome_pep_norm:
                    cpf_row = row.get('CPF') or row.get('Cpf') or row.get('CPF_PEP') or ""
                    cpf_row_numeros = re.sub(r'\D', '', cpf_row)

                    # Se houver miolo e o CPF da base não estiver vazio/mascarado, valida.
                    # Se estiver oculto na planilha, valida pelo Nome Completo Exato!
                    if miolo_cpf and cpf_row_numeros and len(cpf_row_numeros) == 11:
                        if miolo_cpf != cpf_row_numeros[3:9]:
                            continue

                    cargo = row.get('Descrição_Função') or row.get('DESCRICAO_FUNCAO') or row.get('Função') or row.get('Cargo') or "Agente Político / Função Pública"
                    orgao = row.get('Nome_Órgão') or row.get('NOME_ORGAO') or row.get('Órgão') or row.get('Orgao') or "Administração Pública (CGU)"

                    return {
                        "cargo": cargo.strip(),
                        "orgao": orgao.strip(),
                        "detalhe": f"Registro Oficial na Base da CGU ({caminho_final})"
                    }
    except Exception:
        pass

    return None
