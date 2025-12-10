import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator


def validar_email_formato(email):
    """
    Valida o formato do email usando regex e validador do Django
    
    Formato esperado: usuario@dominio.com
    
    OPERAÇÃO SQL: Nenhuma (validação em memória)
    """
    # Validador padrão do Django
    validator = EmailValidator(message="Formato de email inválido.")
    
    try:
        validator(email)
    except ValidationError:
        raise ValidationError("Digite um email válido no formato usuario@dominio.com")
    
    # Validação extra: verificar se tem pelo menos um ponto após o @
    if email.count('@') != 1:
        raise ValidationError("Email deve conter exatamente um @")
    
    local, dominio = email.split('@')
    
    if not local or not dominio:
        raise ValidationError("Email inválido")
    
    if '.' not in dominio:
        raise ValidationError("O domínio do email deve conter um ponto (ex: gmail.com)")
    
    return email


def validar_cpf_formato(cpf):
    """
    Valida o formato e dígitos verificadores do CPF
    
    Formato aceito: XXX.XXX.XXX-XX ou XXXXXXXXXXX (11 dígitos)
    
    OPERAÇÃO SQL: Nenhuma (validação matemática em memória)
    """
    # Remove caracteres não numéricos
    cpf_numeros = re.sub(r'[^0-9]', '', cpf)
    
    # Verifica se tem 11 dígitos
    if len(cpf_numeros) != 11:
        raise ValidationError("CPF deve conter 11 dígitos")
    
    # Verifica se não é sequência repetida (ex: 111.111.111-11)
    if cpf_numeros == cpf_numeros[0] * 11:
        raise ValidationError("CPF inválido")
    
    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf_numeros[i]) * (10 - i)
    
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_numeros[9]) != digito1:
        raise ValidationError("CPF inválido - primeiro dígito verificador incorreto")
    
    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf_numeros[i]) * (11 - i)
    
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf_numeros[10]) != digito2:
        raise ValidationError("CPF inválido - segundo dígito verificador incorreto")
    
    return cpf_numeros


def formatar_cpf(cpf):
    """
    Formata CPF para o padrão XXX.XXX.XXX-XX
    
    OPERAÇÃO SQL: Nenhuma (formatação em memória)
    """
    cpf_numeros = re.sub(r'[^0-9]', '', cpf)
    
    if len(cpf_numeros) == 11:
        return f"{cpf_numeros[:3]}.{cpf_numeros[3:6]}.{cpf_numeros[6:9]}-{cpf_numeros[9:]}"
    
    return cpf


def limpar_cpf(cpf):
    """
    Remove formatação do CPF, deixando apenas números
    
    OPERAÇÃO SQL: Nenhuma (limpeza em memória)
    """
    return re.sub(r'[^0-9]', '', cpf)