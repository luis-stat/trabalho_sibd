from django import forms
from .models import (
    Convenio, Paciente, Funcionario, Escala, Atendimento, Procedimento,
    Leito, Internacao, Medicamento, MovimentacaoEstoque, Equipamento,
    Manutencao, Financeiro, ProcessoJuridico,
)


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            css_class = "form-select" if isinstance(widget, forms.Select) else "form-control"
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css_class}".strip()
            if isinstance(widget, forms.DateInput):
                widget.attrs["type"] = "date"
            if isinstance(widget, forms.DateTimeInput):
                widget.attrs["type"] = "datetime-local"


class ConvenioForm(BaseModelForm):
    class Meta:
        model = Convenio
        fields = "__all__"


class PacienteForm(BaseModelForm):
    class Meta:
        model = Paciente
        fields = "__all__"


class FuncionarioForm(BaseModelForm):
    class Meta:
        model = Funcionario
        fields = "__all__"


class EscalaForm(BaseModelForm):
    class Meta:
        model = Escala
        fields = "__all__"


class AtendimentoForm(BaseModelForm):
    class Meta:
        model = Atendimento
        fields = "__all__"
        widgets = {
            "data_hora_chegada": forms.DateTimeInput(),
            "data_hora_inicio": forms.DateTimeInput(),
            "data_hora_fim": forms.DateTimeInput(),
        }


class ProcedimentoForm(BaseModelForm):
    class Meta:
        model = Procedimento
        fields = "__all__"


class LeitoForm(BaseModelForm):
    class Meta:
        model = Leito
        fields = "__all__"


class InternacaoForm(BaseModelForm):
    class Meta:
        model = Internacao
        fields = "__all__"
        widgets = {
            "data_entrada": forms.DateTimeInput(),
            "data_saida": forms.DateTimeInput(),
        }


class MedicamentoForm(BaseModelForm):
    class Meta:
        model = Medicamento
        fields = "__all__"


class MovimentacaoEstoqueForm(BaseModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = "__all__"
        widgets = {
            "data": forms.DateTimeInput(),
        }


class EquipamentoForm(BaseModelForm):
    class Meta:
        model = Equipamento
        fields = "__all__"


class ManutencaoForm(BaseModelForm):
    class Meta:
        model = Manutencao
        fields = "__all__"


class FinanceiroForm(BaseModelForm):
    class Meta:
        model = Financeiro
        fields = "__all__"


class ProcessoJuridicoForm(BaseModelForm):
    class Meta:
        model = ProcessoJuridico
        fields = "__all__"