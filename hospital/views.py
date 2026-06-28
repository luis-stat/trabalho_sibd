import random
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Avg, Count, Sum, Q
from django.shortcuts import redirect, render

from . import forms as f
from . import models as m

MODEL_REGISTRY = {
    "convenio": {"model": m.Convenio, "form": f.ConvenioForm, "label": "Convênios"},
    "paciente": {"model": m.Paciente, "form": f.PacienteForm, "label": "Pacientes"},
    "funcionario": {"model": m.Funcionario, "form": f.FuncionarioForm, "label": "Funcionários"},
    "escala": {"model": m.Escala, "form": f.EscalaForm, "label": "Escalas"},
    "atendimento": {"model": m.Atendimento, "form": f.AtendimentoForm, "label": "Atendimentos"},
    "procedimento": {"model": m.Procedimento, "form": f.ProcedimentoForm, "label": "Procedimentos"},
    "leito": {"model": m.Leito, "form": f.LeitoForm, "label": "Leitos"},
    "internacao": {"model": m.Internacao, "form": f.InternacaoForm, "label": "Internações"},
    "medicamento": {"model": m.Medicamento, "form": f.MedicamentoForm, "label": "Medicamentos"},
    "movimentacao": {"model": m.MovimentacaoEstoque, "form": f.MovimentacaoEstoqueForm, "label": "Movimentações de Estoque"},
    "equipamento": {"model": m.Equipamento, "form": f.EquipamentoForm, "label": "Equipamentos"},
    "manutencao": {"model": m.Manutencao, "form": f.ManutencaoForm, "label": "Manutenções"},
    "financeiro": {"model": m.Financeiro, "form": f.FinanceiroForm, "label": "Financeiro"},
    "processo": {"model": m.ProcessoJuridico, "form": f.ProcessoJuridicoForm, "label": "Processos Jurídicos"},
}


def login_view(request):
    if request.method == "POST":
        perfil = request.POST.get("perfil", "diretor")
        return redirect(f"dashboard_{perfil}")
    return render(request, "hospital/login.html")


def dashboard(request):
    cards = [
        {"slug": slug, "label": cfg["label"], "total": cfg["model"].objects.count()}
        for slug, cfg in MODEL_REGISTRY.items()
    ]
    return render(request, "hospital/index.html", {"cards": cards})


def dashboard_diretor(request):
    receita_total = m.Financeiro.objects.filter(tipo="RECEITA").aggregate(total=Sum("valor"))["total"] or 0

    lucro_por_especialidade = (
        m.Procedimento.objects.values("especialidade")
        .annotate(receita=Sum("valor_cobrado"), custo=Sum("custo"))
        .order_by("-receita")
    )
    for item in lucro_por_especialidade:
        item["lucro"] = (item["receita"] or 0) - (item["custo"] or 0)

    total_leitos = m.Leito.objects.count()
    leitos_ocupados = m.Leito.objects.filter(status="OCUPADO").count()
    leitos_disponiveis = total_leitos - leitos_ocupados
    taxa_ocupacao = round((leitos_ocupados / total_leitos * 100) if total_leitos else 0, 1)
    taxa_ocupacao_int = int(taxa_ocupacao)

    custo_processos = m.ProcessoJuridico.objects.aggregate(total=Sum("custo_estimado"))["total"] or 0
    processos_abertos = m.ProcessoJuridico.objects.filter(status="ABERTO").count()
    processos_andamento = m.ProcessoJuridico.objects.filter(status="EM_ANDAMENTO").count()

    participacao_convenios = (
        m.Atendimento.objects.filter(convenio__isnull=False)
        .values("convenio__nome")
        .annotate(total_atendimentos=Count("id"), receita=Sum("procedimentos__valor_cobrado"))
        .order_by("-total_atendimentos")
    )

    ctx = {
        "receita_total": receita_total,
        "lucro_por_especialidade": lucro_por_especialidade,
        "total_leitos": total_leitos,
        "leitos_ocupados": leitos_ocupados,
        "leitos_disponiveis": leitos_disponiveis,
        "taxa_ocupacao": taxa_ocupacao,
        "taxa_ocupacao_int": taxa_ocupacao_int,
        "custo_processos": custo_processos,
        "processos_abertos": processos_abertos,
        "processos_andamento": processos_andamento,
        "participacao_convenios": participacao_convenios,
    }
    return render(request, "hospital/dashboard_diretor.html", ctx)


def dashboard_chefe(request):
    tempo_medio = m.Procedimento.objects.aggregate(media=Avg("duracao"))["media"] or 0
    custo_medio = m.Procedimento.objects.aggregate(media=Avg("custo"))["media"] or 0

    escala_por_turno = (
        m.Escala.objects.values("turno")
        .annotate(total=Count("id"))
        .order_by("turno")
    )
    escala_por_setor = (
        m.Escala.objects.values("funcionario__setor")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    produtividade = (
        m.Atendimento.objects.values("funcionario_medico__nome", "funcionario_medico__setor")
        .annotate(total_atendimentos=Count("id"))
        .order_by("-total_atendimentos")[:10]
    )

    cobertura_especialidade = (
        m.Funcionario.objects.filter(cargo="Médico")
        .values("especialidade")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    atendimentos_por_tipo = (
        m.Atendimento.objects.values("tipo_atendimento")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    total_atendimentos = m.Atendimento.objects.count()
    total_procedimentos = m.Procedimento.objects.count()

    ctx = {
        "tempo_medio": round(tempo_medio, 1),
        "custo_medio": round(custo_medio, 2),
        "escala_por_turno": escala_por_turno,
        "escala_por_setor": escala_por_setor,
        "produtividade": produtividade,
        "cobertura_especialidade": cobertura_especialidade,
        "atendimentos_por_tipo": atendimentos_por_tipo,
        "total_atendimentos": total_atendimentos,
        "total_procedimentos": total_procedimentos,
    }
    return render(request, "hospital/dashboard_chefe.html", ctx)


def dashboard_farmaceutico(request):
    estoque = m.Medicamento.objects.all().order_by("quantidade_estoque")

    total_dispensado = (
        m.MovimentacaoEstoque.objects.filter(tipo_movimentacao="SAIDA")
        .aggregate(total=Sum("quantidade"))["total"] or 0
    )

    consumo_por_medicamento = (
        m.MovimentacaoEstoque.objects.filter(tipo_movimentacao="SAIDA")
        .values("medicamento__descricao")
        .annotate(total_saida=Sum("quantidade"))
        .order_by("-total_saida")
    )

    movimentacao_por_funcionario = (
        m.MovimentacaoEstoque.objects.values(
            "funcionario_responsavel__nome",
            "funcionario_responsavel__setor",
        )
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )

    entradas = (
        m.MovimentacaoEstoque.objects.filter(tipo_movimentacao="ENTRADA")
        .aggregate(total=Sum("quantidade"))["total"] or 0
    )
    saidas = (
        m.MovimentacaoEstoque.objects.filter(tipo_movimentacao="SAIDA")
        .aggregate(total=Sum("quantidade"))["total"] or 0
    )

    vencendo = m.Medicamento.objects.filter(
        validade__lte=date.today() + timedelta(days=90)
    ).order_by("validade")

    ctx = {
        "estoque": estoque,
        "total_dispensado": total_dispensado,
        "consumo_por_medicamento": consumo_por_medicamento,
        "movimentacao_por_funcionario": movimentacao_por_funcionario,
        "entradas": entradas,
        "saidas": saidas,
        "vencendo": vencendo,
    }
    return render(request, "hospital/dashboard_farmaceutico.html", ctx)


def diagrama(request):
    return render(request, "hospital/diagrama.html")


def sql_view(request):
    statements = []
    with connection.schema_editor(collect_sql=True, atomic=False) as schema_editor:
        for cfg in MODEL_REGISTRY.values():
            schema_editor.create_model(cfg["model"])
        statements = schema_editor.collected_sql

    blocos_limpos = []
    for stmt in statements:
        linhas = [
            linha for linha in stmt.splitlines()
            if linha.strip() and not linha.strip().startswith("--")
        ]
        if linhas:
            blocos_limpos.append("\n".join(linhas))

    sql_final = ";\n\n".join(blocos_limpos) + ";"
    return render(request, "hospital/sql.html", {"sql": sql_final})


def sobre(request):
    equipe = [
        {"nome": "Ana Lismara da Silva Lopes", "matricula": "580591"},
        {"nome": "Deusdedit Teixeira de Sousa Neto", "matricula": "580811"},
        {"nome": "Ingryd França de Sena Melo", "matricula": "578042"},
        {"nome": "Luís Miguel Frazão de Sousa", "matricula": "581422"},
        {"nome": "Sara Martins de Oliveira", "matricula": "578158"},
    ]
    return render(request, "hospital/sobre.html", {"equipe": equipe})


def list_view(request, model_slug):
    cfg = MODEL_REGISTRY.get(model_slug)
    if not cfg:
        messages.error(request, "Entidade não encontrada.")
        return redirect("dashboard")

    model = cfg["model"]
    objetos = model.objects.all().order_by("-id")[:300]
    campos = [field.verbose_name for field in model._meta.fields]
    linhas = []
    for obj in objetos:
        linha = []
        for field in model._meta.fields:
            display_method = f"get_{field.name}_display"
            if hasattr(obj, display_method) and field.choices:
                linha.append(getattr(obj, display_method)())
            else:
                linha.append(getattr(obj, field.name))
        linhas.append(linha)

    contexto = {
        "label": cfg["label"],
        "slug": model_slug,
        "campos": campos,
        "linhas": linhas,
        "total": model.objects.count(),
    }
    return render(request, "hospital/generic_list.html", contexto)


def create_view(request, model_slug):
    cfg = MODEL_REGISTRY.get(model_slug)
    if not cfg:
        messages.error(request, "Entidade não encontrada.")
        return redirect("dashboard")

    form_class = cfg["form"]
    if request.method == "POST":
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Registro de {cfg['label']} cadastrado com sucesso.")
            return redirect("list_view", model_slug=model_slug)
    else:
        form = form_class()

    contexto = {"label": cfg["label"], "slug": model_slug, "form": form}
    return render(request, "hospital/generic_form.html", contexto)


def popular_mock(request):
    if request.method != "POST":
        return redirect("dashboard")

    nomes = ["Ana", "Carlos", "Beatriz", "Diego", "Elaine", "Fábio", "Gabriela", "Heitor",
             "Isabela", "João", "Karina", "Lucas", "Mariana", "Nelson", "Otávia", "Paulo",
             "Queila", "Rafael", "Sofia", "Tiago"]
    sobrenomes = ["Silva", "Souza", "Oliveira", "Pereira", "Costa", "Rodrigues", "Almeida",
                  "Nascimento", "Lima", "Araújo", "Carvalho", "Gomes", "Martins", "Rocha", "Ribeiro"]
    setores = ["Pronto Socorro", "UTI", "Clínica Geral", "Pediatria", "Ortopedia", "Cardiologia", "Radiologia"]
    cargos = ["Médico", "Enfermeiro", "Técnico de Enfermagem", "Recepcionista", "Administrador"]
    especialidades = ["Clínica Geral", "Cardiologia", "Ortopedia", "Pediatria", "Neurologia", "Ginecologia"]

    def nome_aleatorio():
        return f"{random.choice(nomes)} {random.choice(sobrenomes)}"

    def cpf_aleatorio():
        return f"{random.randint(100,999)}.{random.randint(100,999)}.{random.randint(100,999)}-{random.randint(10,99)}"

    def data_aleatoria(inicio_ano, fim_ano):
        inicio = date(inicio_ano, 1, 1)
        fim = date(fim_ano, 12, 28)
        delta = (fim - inicio).days
        return inicio + timedelta(days=random.randint(0, delta))

    with transaction.atomic():
        convenios = [
            m.Convenio.objects.create(
                nome=nome,
                percentual_repasse=round(random.uniform(40, 90), 2),
                prazo_pagamento=random.choice([15, 30, 45, 60]),
            )
            for nome in ["Unimed", "Bradesco Saúde", "Amil", "SulAmérica", "Particular"]
        ]

        pacientes = [
            m.Paciente.objects.create(
                nome=nome_aleatorio(),
                cpf=cpf_aleatorio(),
                sexo=random.choice(m.Paciente.Sexo.values),
                data_nascimento=data_aleatoria(1940, 2020),
                endereco=f"Rua {random.randint(1, 999)}, Bairro {random.choice(setores)}",
                telefone=f"(85) 9{random.randint(1000,9999)}-{random.randint(1000,9999)}",
                convenio=random.choice(convenios),
            )
            for _ in range(25)
        ]

        funcionarios = [
            m.Funcionario.objects.create(
                nome=nome_aleatorio(),
                cargo=random.choice(cargos),
                especialidade=random.choice(especialidades),
                salario=round(random.uniform(2500, 18000), 2),
                setor=random.choice(setores),
                data_admissao=data_aleatoria(2010, 2024),
            )
            for _ in range(15)
        ]

        for _ in range(30):
            m.Escala.objects.create(
                funcionario=random.choice(funcionarios),
                data=data_aleatoria(2025, 2026),
                turno=random.choice(m.Escala.Turno.values),
            )

        leitos = [
            m.Leito.objects.create(
                setor=random.choice(setores),
                tipo=random.choice(["Enfermaria", "Apartamento", "UTI"]),
                status=random.choice(m.Leito.Status.values),
            )
            for _ in range(20)
        ]

        medicamentos = [
            m.Medicamento.objects.create(
                descricao=desc,
                lote=f"L{random.randint(1000, 9999)}",
                validade=data_aleatoria(2026, 2028),
                quantidade_estoque=random.randint(10, 500),
                custo_unitario=round(random.uniform(1, 80), 2),
            )
            for desc in ["Dipirona", "Paracetamol", "Amoxicilina", "Soro Fisiológico", "Insulina", "Ibuprofeno"]
        ]

        equipamentos = [
            m.Equipamento.objects.create(
                descricao=desc,
                setor=random.choice(setores),
                data_aquisicao=data_aleatoria(2015, 2024),
                custo_aquisicao=round(random.uniform(5000, 150000), 2),
                status=random.choice(m.Equipamento.Status.values),
            )
            for desc in ["Raio-X", "Ultrassom", "Monitor Cardíaco", "Ventilador Pulmonar", "Desfibrilador"]
        ]

        atendimentos = []
        for _ in range(40):
            paciente = random.choice(pacientes)
            chegada = datetime.combine(data_aleatoria(2025, 2026), datetime.min.time()) + timedelta(hours=random.randint(6, 22))
            atendimentos.append(
                m.Atendimento.objects.create(
                    paciente=paciente,
                    funcionario_medico=random.choice(funcionarios),
                    convenio=paciente.convenio,
                    data_hora_chegada=chegada,
                    data_hora_inicio=chegada + timedelta(minutes=random.randint(5, 60)),
                    data_hora_fim=chegada + timedelta(minutes=random.randint(65, 180)),
                    tipo_atendimento=random.choice(m.Atendimento.TipoAtendimento.values),
                )
            )

        for atendimento in atendimentos:
            for _ in range(random.randint(1, 2)):
                custo = round(random.uniform(30, 500), 2)
                m.Procedimento.objects.create(
                    atendimento=atendimento,
                    especialidade=random.choice(especialidades),
                    descricao=random.choice(["Consulta clínica", "Exame de sangue", "Raio-X", "Curativo", "Sutura"]),
                    custo=custo,
                    valor_cobrado=round(custo * random.uniform(1.2, 2.0), 2),
                    duracao=random.randint(15, 90),
                )

        for _ in range(12):
            entrada = datetime.combine(data_aleatoria(2025, 2026), datetime.min.time())
            sai = random.random() > 0.3
            m.Internacao.objects.create(
                paciente=random.choice(pacientes),
                leito=random.choice(leitos),
                data_entrada=entrada,
                data_saida=entrada + timedelta(days=random.randint(1, 15)) if sai else None,
            )

        for _ in range(40):
            m.MovimentacaoEstoque.objects.create(
                medicamento=random.choice(medicamentos),
                funcionario_responsavel=random.choice(funcionarios),
                tipo_movimentacao=random.choice(m.MovimentacaoEstoque.TipoMovimentacao.values),
                quantidade=random.randint(1, 100),
                data=datetime.combine(data_aleatoria(2025, 2026), datetime.min.time()),
            )

        for equipamento in equipamentos:
            for _ in range(random.randint(0, 2)):
                abertura = data_aleatoria(2024, 2026)
                fechou = random.random() > 0.4
                m.Manutencao.objects.create(
                    equipamento=equipamento,
                    data_abertura=abertura,
                    data_fechamento=abertura + timedelta(days=random.randint(1, 20)) if fechou else None,
                    custo=round(random.uniform(200, 5000), 2),
                    tipo=random.choice(["Preventiva", "Corretiva"]),
                )

        for _ in range(30):
            m.Financeiro.objects.create(
                categoria=random.choice(["Atendimento", "Internação", "Folha de Pagamento", "Compra de Insumos", "Manutenção"]),
                valor=round(random.uniform(100, 20000), 2),
                data=data_aleatoria(2025, 2026),
                centro_custo=random.choice(setores),
                tipo=random.choice(m.Financeiro.Tipo.values),
            )

        for _ in range(8):
            m.ProcessoJuridico.objects.create(
                paciente=random.choice(pacientes),
                tipo=random.choice(["Indenização", "Erro Médico", "Cobrança Indevida", "Trabalhista"]),
                data_abertura=data_aleatoria(2023, 2026),
                status=random.choice(m.ProcessoJuridico.Status.values),
                custo_estimado=round(random.uniform(1000, 50000), 2),
            )

    messages.success(request, "Dados mockados gerados com sucesso.")
    return redirect("dashboard")