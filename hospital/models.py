from django.db import models


class Convenio(models.Model):
    nome = models.CharField(max_length=150)
    percentual_repasse = models.DecimalField(max_digits=5, decimal_places=2)
    prazo_pagamento = models.IntegerField()

    class Meta:
        verbose_name = "Convênio"
        verbose_name_plural = "Convênios"

    def __str__(self):
        return self.nome


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"
        OUTRO = "O", "Outro"

    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, unique=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    data_nascimento = models.DateField()
    endereco = models.CharField(max_length=255)
    telefone = models.CharField(max_length=20)
    convenio = models.ForeignKey(Convenio, on_delete=models.SET_NULL, null=True, blank=True, related_name="pacientes")

    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"

    def __str__(self):
        return self.nome


class Funcionario(models.Model):
    nome = models.CharField(max_length=200)
    cargo = models.CharField(max_length=100)
    especialidade = models.CharField(max_length=100, blank=True)
    salario = models.DecimalField(max_digits=10, decimal_places=2)
    setor = models.CharField(max_length=100)
    data_admissao = models.DateField()

    class Meta:
        verbose_name = "Funcionário"
        verbose_name_plural = "Funcionários"

    def __str__(self):
        return self.nome


class Escala(models.Model):
    class Turno(models.TextChoices):
        MANHA = "MANHA", "Manhã"
        TARDE = "TARDE", "Tarde"
        NOITE = "NOITE", "Noite"

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name="escalas")
    data = models.DateField()
    turno = models.CharField(max_length=10, choices=Turno.choices)

    class Meta:
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"

    def __str__(self):
        return f"{self.funcionario} - {self.data} ({self.get_turno_display()})"


class Atendimento(models.Model):
    class TipoAtendimento(models.TextChoices):
        CONSULTA = "CONSULTA", "Consulta"
        EMERGENCIA = "EMERGENCIA", "Emergência"
        EXAME = "EXAME", "Exame"
        RETORNO = "RETORNO", "Retorno"

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="atendimentos")
    funcionario_medico = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, related_name="atendimentos")
    convenio = models.ForeignKey(Convenio, on_delete=models.SET_NULL, null=True, blank=True, related_name="atendimentos")
    data_hora_chegada = models.DateTimeField()
    data_hora_inicio = models.DateTimeField(null=True, blank=True)
    data_hora_fim = models.DateTimeField(null=True, blank=True)
    tipo_atendimento = models.CharField(max_length=20, choices=TipoAtendimento.choices)

    class Meta:
        verbose_name = "Atendimento"
        verbose_name_plural = "Atendimentos"

    def __str__(self):
        return f"Atendimento {self.id} - {self.paciente}"


class Procedimento(models.Model):
    atendimento = models.ForeignKey(Atendimento, on_delete=models.CASCADE, related_name="procedimentos")
    especialidade = models.CharField(max_length=100)
    descricao = models.CharField(max_length=255)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    valor_cobrado = models.DecimalField(max_digits=10, decimal_places=2)
    duracao = models.IntegerField()

    class Meta:
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"

    def __str__(self):
        return self.descricao


class Leito(models.Model):
    class Status(models.TextChoices):
        DISPONIVEL = "DISPONIVEL", "Disponível"
        OCUPADO = "OCUPADO", "Ocupado"
        MANUTENCAO = "MANUTENCAO", "Manutenção"

    setor = models.CharField(max_length=100)
    tipo = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices)

    class Meta:
        verbose_name = "Leito"
        verbose_name_plural = "Leitos"

    def __str__(self):
        return f"Leito {self.id} - {self.setor}"


class Internacao(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="internacoes")
    leito = models.ForeignKey(Leito, on_delete=models.SET_NULL, null=True, related_name="internacoes")
    data_entrada = models.DateTimeField()
    data_saida = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Internação"
        verbose_name_plural = "Internações"

    def __str__(self):
        return f"Internação {self.id} - {self.paciente}"


class Medicamento(models.Model):
    descricao = models.CharField(max_length=200)
    lote = models.CharField(max_length=50)
    validade = models.DateField()
    quantidade_estoque = models.IntegerField()
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Medicamento"
        verbose_name_plural = "Medicamentos"

    def __str__(self):
        return self.descricao


class MovimentacaoEstoque(models.Model):
    class TipoMovimentacao(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SAIDA = "SAIDA", "Saída"

    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name="movimentacoes")
    funcionario_responsavel = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, related_name="movimentacoes_estoque")
    tipo_movimentacao = models.CharField(max_length=10, choices=TipoMovimentacao.choices)
    quantidade = models.IntegerField()
    data = models.DateTimeField()

    class Meta:
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque"

    def __str__(self):
        return f"{self.tipo_movimentacao} - {self.medicamento}"


class Equipamento(models.Model):
    class Status(models.TextChoices):
        ATIVO = "ATIVO", "Ativo"
        EM_MANUTENCAO = "EM_MANUTENCAO", "Em Manutenção"
        INATIVO = "INATIVO", "Inativo"

    descricao = models.CharField(max_length=200)
    setor = models.CharField(max_length=100)
    data_aquisicao = models.DateField()
    custo_aquisicao = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices)

    class Meta:
        verbose_name = "Equipamento"
        verbose_name_plural = "Equipamentos"

    def __str__(self):
        return self.descricao


class Manutencao(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name="manutencoes")
    data_abertura = models.DateField()
    data_fechamento = models.DateField(null=True, blank=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    tipo = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Manutenção"
        verbose_name_plural = "Manutenções"

    def __str__(self):
        return f"Manutenção {self.id} - {self.equipamento}"


class Financeiro(models.Model):
    class Tipo(models.TextChoices):
        RECEITA = "RECEITA", "Receita"
        DESPESA = "DESPESA", "Despesa"

    categoria = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    data = models.DateField()
    centro_custo = models.CharField(max_length=100)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)

    class Meta:
        verbose_name = "Lançamento Financeiro"
        verbose_name_plural = "Financeiro"

    def __str__(self):
        return f"{self.categoria} - {self.valor}"


class ProcessoJuridico(models.Model):
    class Status(models.TextChoices):
        ABERTO = "ABERTO", "Aberto"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em Andamento"
        ENCERRADO = "ENCERRADO", "Encerrado"

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="processos_juridicos")
    tipo = models.CharField(max_length=100)
    data_abertura = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices)
    custo_estimado = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Processo Jurídico"
        verbose_name_plural = "Processos Jurídicos"

    def __str__(self):
        return f"Processo {self.id} - {self.paciente}"