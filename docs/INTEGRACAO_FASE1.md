# Fundacao Integrada - Fase 1

Esta fase conecta os modulos da plataforma e adiciona rastreabilidade
completa. Abrange: estrutura organizacional, fluxo de aprovacao de chamados,
auditoria global, notificacoes + caixa de entrada interna + e-mail, e a
conversao de chamado em atividade de projeto.

## Estrutura organizacional

Novos cadastros e vinculos no usuario:

- `Department` (`/api/departments/`) e `Position` (`/api/positions/`).
  Cargos com `auto_approval=true` aprovam chamados automaticamente.
- Campos novos em `User`: `department`, `position`, `supervisor`, `manager`,
  `approval_mode` (`INHERITED|SUPERVISOR|MANAGER|AUTO|SERVICE_DESK`) e
  `is_service_desk_approver`.

## Fluxo de aprovacao de chamados

Quando a categoria do chamado exige aprovacao (`TicketCategory.approval_required`),
ao abrir o chamado o sistema resolve automaticamente (`apps/tickets/approvals.py`):

1. **Regra 3 - Automatica por cargo**: cargo com `auto_approval` (ou
   `approval_mode=AUTO`) -> status `Aprovado` imediatamente.
2. **Regra 1 - Aprovador vinculado**: usa `supervisor`/`manager` -> status
   `Aguardando Aprovacao`, notifica o aprovador.
3. **Regra 2 - Equipe de chamados**: sem aprovador vinculado -> direciona aos
   usuarios `is_service_desk_approver`.

Acoes (em `/api/tickets/{id}/`):

- `POST .../approve/`
- `POST .../reject/`
- `POST .../request-changes/`
- `GET  .../approvals/` (historico)

Cada decisao gera registro em `TicketApproval`, auditoria e notificacao ao
solicitante. Historico completo tambem em `/api/ticket-approvals/`.

## Conversao chamado -> atividade

`POST /api/tickets/{id}/convert-to-activity/` com `{ "project": <id>, "sprint": <id?> }`.

Cria a atividade, transfere comentarios, anexos e horas executadas (como
apontamento), vincula `Activity.ticket` e `Ticket.converted_activity`,
encerra o chamado com status `Convertido em Atividade de Projeto` e motivo
"Chamado convertido em atividade de projeto." (visivel no Portal do Cliente).

## Comentarios e anexos

- Chamados: `/api/ticket-comments/`, `/api/ticket-attachments/`.
- Atividades: `/api/activity-comments/`, `/api/activity-attachments/`.

## Notificacoes e caixa de entrada

- Inbox: `/api/notifications/` com acoes `read`, `unread`, `favorite`,
  `archive`, `read-all`, `unread-count`. Filtros por `category`, `origin`,
  `event`, `is_read`, `is_favorite`, `is_archived`.
- Preferencias: `GET/PATCH /api/notification-preferences/me/`
  (`email_enabled`, `inbox_enabled`, `disabled_events`, `email_disabled_events`).
- E-mail centralizado configuravel por ambiente (`EMAIL_BACKEND`, `EMAIL_HOST`,
  ..., `DEFAULT_FROM_EMAIL`, `PLATFORM_WEB_URL`). Em dev usa console backend.

## Auditoria global

Toda acao critica chama `common.audit.record_audit` registrando usuario, data,
hora, acao, valores anterior/novo, origem e IP. Consulta em `/api/audit-logs/`
(somente leitura, exige `reports.view`/`settings.view`/`users.manage`).

## Migrations adicionadas

- `users/0006_org_structure`
- `tickets/0006_ticket_approval_conversion`
- `activities/0004_activity_comments_attachments`
- `notifications/0001_initial`
- `audit/0001_initial`

> Observacao: nao foi possivel executar `makemigrations`/`migrate` no ambiente
> de geracao (Django 6 exige Python 3.12). As migrations foram escritas a mao
> para refletir os modelos; rode `python manage.py migrate` no ambiente alvo.
