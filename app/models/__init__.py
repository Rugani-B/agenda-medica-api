# app/models/__init__.py
from app.models.usuario          import Usuario
from app.models.especialidade    import Especialidade
from app.models.medico           import Medico
from app.models.pacientes        import Paciente
from app.models.consulta         import Consulta
from app.models.confirmacao      import Confirmacao
from app.models.reagendamento    import Reagendamento
from app.models.responsavel      import Responsavel
from app.models.anexo_exame      import AnexoExame
from app.models.medicamento      import Medicamento
from app.models.prescricao       import Prescricao, PrescricaoItem
from app.models.tipo_exame       import TipoExame
from app.models.local_exame      import LocalExame
from app.models.exame            import Exame
from app.models.pedido_exame     import PedidoExame
from app.models.adesao_tratamento import AdesaoTratamento
