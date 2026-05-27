import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST, require_GET
from django.contrib import messages
from django.utils import timezone

from hub.models import BusinessInstance, BusinessEmployee
from hub.views import _get_business_for_user
from .models import (
    Board, BoardList, Card, Label, CardLabel,
    Checklist, ChecklistItem, CardComment, CardActivity, BOARD_COLORS, CARD_COLORS,
)


def _log(board, event, description, user, card=None):
    CardActivity.objects.create(board=board, card=card, author=user, event=event, description=description)


def _biz(slug, user):
    """Return business or None."""
    return _get_business_for_user(slug, user)


# ─── Board List ───────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def board_list(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    boards = Board.objects.filter(business=biz, is_archived=False)
    archived = Board.objects.filter(business=biz, is_archived=True)
    return render(request, 'task_board/boards.html', {
        'biz': biz,
        'boards': boards,
        'archived_boards': archived,
        'board_colors': BOARD_COLORS,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def board_create(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    name = request.POST.get('name', '').strip()
    if not name:
        messages.error(request, "Board name is required.")
        return redirect('task_board:board_list', slug=slug)

    board = Board.objects.create(
        business=biz,
        name=name,
        description=request.POST.get('description', '').strip(),
        color=request.POST.get('color', 'default'),
        created_by=request.user,
    )
    # Seed default lists
    defaults = ['Backlog', 'To Do', 'In Progress', 'Review', 'Done']
    for i, col_name in enumerate(defaults):
        BoardList.objects.create(board=board, name=col_name, position=i)

    _log(board, 'board_created', f'Board "{board.name}" created', request.user)
    messages.success(request, f'Board "{board.name}" created.')
    return redirect('task_board:board_detail', slug=slug, board_id=board.id)


# ─── Board Detail (Kanban) ────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def board_detail(request, slug, board_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    board = get_object_or_404(Board, id=board_id, business=biz)
    lists = board.lists.filter(is_archived=False).prefetch_related(
        'cards', 'cards__card_labels__label', 'cards__assignees', 'cards__checklists__items'
    )
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    labels = board.labels.all()
    activities = board.activities.select_related('author', 'card')[:30]

    return render(request, 'task_board/board.html', {
        'biz': biz,
        'board': board,
        'lists': lists,
        'employees': employees,
        'labels': labels,
        'activities': activities,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def board_archive(request, slug, board_id):
    biz = _biz(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()
    board = get_object_or_404(Board, id=board_id, business=biz)
    board.is_archived = True
    board.save(update_fields=['is_archived'])
    messages.info(request, f'"{board.name}" archived.')
    return redirect('task_board:board_list', slug=slug)


# ─── List (Column) Operations ─────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_POST
def list_create(request, slug, board_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    board = get_object_or_404(Board, id=board_id, business=biz)
    name = request.POST.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)

    position = board.lists.count()
    bl = BoardList.objects.create(board=board, name=name, position=position)
    _log(board, 'list_created', f'List "{name}" added', request.user)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'id': bl.id, 'name': bl.name, 'position': bl.position})
    return redirect('task_board:board_detail', slug=slug, board_id=board_id)


@login_required(login_url='/accounts/login/')
@require_POST
def list_update(request, slug, list_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    bl = get_object_or_404(BoardList, id=list_id, board__business=biz)
    bl.name = request.POST.get('name', bl.name).strip() or bl.name
    limit = request.POST.get('task_limit', '')
    if limit.isdigit():
        bl.task_limit = int(limit)
    bl.save()
    return JsonResponse({'ok': True, 'name': bl.name, 'task_limit': bl.task_limit})


@login_required(login_url='/accounts/login/')
@require_POST
def list_reorder(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    try:
        order = json.loads(request.body).get('order', [])
        for pos, list_id in enumerate(order):
            BoardList.objects.filter(id=list_id, board__business=biz).update(position=pos)
        return JsonResponse({'ok': True})
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)


# ─── Card Operations ──────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_POST
def card_create(request, slug, list_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    bl = get_object_or_404(BoardList, id=list_id, board__business=biz)

    if bl.is_over_limit():
        return JsonResponse({'error': f'Column limit ({bl.task_limit}) reached'}, status=400)

    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)

    position = bl.cards.count()
    card = Card.objects.create(
        board_list=bl,
        title=title,
        position=position,
        created_by=request.user,
    )
    _log(bl.board, 'card_created', f'"{title}" added to {bl.name}', request.user, card)

    return JsonResponse({
        'id': card.id,
        'title': card.title,
        'color': card.color,
        'due_date': str(card.due_date) if card.due_date else '',
        'list_id': bl.id,
    })


@login_required(login_url='/accounts/login/')
def card_detail(request, slug, card_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    card = get_object_or_404(Card, id=card_id, board_list__board__business=biz)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    labels = card.board_list.board.labels.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'update':
            card.title = request.POST.get('title', card.title).strip() or card.title
            card.description = request.POST.get('description', card.description)
            card.color = request.POST.get('color', card.color)
            card.story_points = request.POST.get('story_points') or None
            due = request.POST.get('due_date', '')
            card.due_date = due if due else None
            card.save()
            _log(card.board_list.board, 'card_updated', f'"{card.title}" updated', request.user, card)
            return JsonResponse({'ok': True, 'title': card.title})

        if action == 'add_checklist':
            name = request.POST.get('checklist_name', 'Checklist').strip()
            cl = Checklist.objects.create(card=card, name=name, position=card.checklists.count())
            return JsonResponse({'id': cl.id, 'name': cl.name})

        if action == 'add_checklist_item':
            cl_id = request.POST.get('checklist_id')
            title = request.POST.get('item_title', '').strip()
            if cl_id and title:
                cl = get_object_or_404(Checklist, id=cl_id, card=card)
                item = ChecklistItem.objects.create(checklist=cl, title=title, position=cl.items.count())
                return JsonResponse({'id': item.id, 'title': item.title, 'is_done': item.is_done})

        if action == 'toggle_assignee':
            emp_id = request.POST.get('employee_id')
            emp = get_object_or_404(BusinessEmployee, id=emp_id, business=biz)
            if card.assignees.filter(id=emp.id).exists():
                card.assignees.remove(emp)
                assigned = False
            else:
                card.assignees.add(emp)
                assigned = True
            return JsonResponse({'assigned': assigned})

        if action == 'toggle_label':
            lbl_id = request.POST.get('label_id')
            lbl = get_object_or_404(Label, id=lbl_id, board=card.board_list.board)
            existing = CardLabel.objects.filter(card=card, label=lbl)
            if existing.exists():
                existing.delete()
                active = False
            else:
                CardLabel.objects.create(card=card, label=lbl)
                active = True
            return JsonResponse({'active': active})

    checklists = card.checklists.prefetch_related('items')
    comments = card.comments.select_related('author')
    active_labels = [cl.label_id for cl in card.card_labels.all()]

    return render(request, 'task_board/card_detail.html', {
        'biz': biz,
        'card': card,
        'board': card.board_list.board,
        'employees': employees,
        'labels': labels,
        'active_labels': active_labels,
        'checklists': checklists,
        'comments': comments,
        'card_colors': CARD_COLORS,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def card_move(request, slug, card_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    card = get_object_or_404(Card, id=card_id, board_list__board__business=biz)

    try:
        data = json.loads(request.body)
        new_list_id = data.get('list_id')
        new_position = data.get('position', 0)
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_list = get_object_or_404(BoardList, id=new_list_id, board__business=biz)

    if new_list.is_over_limit() and card.board_list_id != new_list.id:
        return JsonResponse({'error': f'Column limit ({new_list.task_limit}) reached'}, status=400)

    old_list_name = card.board_list.name
    card.board_list = new_list
    card.position = new_position
    card.save(update_fields=['board_list', 'position'])

    if old_list_name != new_list.name:
        _log(card.board_list.board, 'card_moved',
             f'"{card.title}" moved from {old_list_name} → {new_list.name}',
             request.user, card)

    return JsonResponse({'ok': True})


@login_required(login_url='/accounts/login/')
@require_POST
def cards_reorder(request, slug):
    """Persist card positions after a drag-drop reorder within or between lists."""
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    try:
        data = json.loads(request.body)
        for list_id, card_ids in data.items():
            bl = BoardList.objects.get(id=list_id, board__business=biz)
            for pos, cid in enumerate(card_ids):
                Card.objects.filter(id=cid, board_list__board__business=biz).update(
                    board_list=bl, position=pos
                )
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required(login_url='/accounts/login/')
@require_POST
def card_archive(request, slug, card_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    card = get_object_or_404(Card, id=card_id, board_list__board__business=biz)
    card.is_archived = True
    card.save(update_fields=['is_archived'])
    _log(card.board_list.board, 'card_archived', f'"{card.title}" archived', request.user, card)
    return JsonResponse({'ok': True})


# ─── Checklist ────────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_POST
def checklist_item_toggle(request, slug, item_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    item = get_object_or_404(ChecklistItem, id=item_id, checklist__card__board_list__board__business=biz)
    item.is_done = not item.is_done
    item.save(update_fields=['is_done'])

    cl = item.checklist
    return JsonResponse({
        'is_done': item.is_done,
        'progress': cl.progress_pct(),
        'done': cl.items.filter(is_done=True).count(),
        'total': cl.items.count(),
    })


@login_required(login_url='/accounts/login/')
@require_POST
def checklist_item_add(request, slug, checklist_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    cl = get_object_or_404(Checklist, id=checklist_id, card__board_list__board__business=biz)
    title = request.POST.get('title', '').strip()
    if not title:
        return JsonResponse({'error': 'Title required'}, status=400)

    item = ChecklistItem.objects.create(checklist=cl, title=title, position=cl.items.count())
    return JsonResponse({'id': item.id, 'title': item.title, 'is_done': item.is_done})


@login_required(login_url='/accounts/login/')
@require_POST
def checklist_item_delete(request, slug, item_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    item = get_object_or_404(ChecklistItem, id=item_id, checklist__card__board_list__board__business=biz)
    item.delete()
    return JsonResponse({'ok': True})


# ─── Comments ─────────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_POST
def comment_add(request, slug, card_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    card = get_object_or_404(Card, id=card_id, board_list__board__business=biz)
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Comment cannot be empty'}, status=400)

    comment = CardComment.objects.create(card=card, author=request.user, content=content)
    _log(card.board_list.board, 'comment_added', f'Comment on "{card.title}"', request.user, card)

    return JsonResponse({
        'id': comment.id,
        'content': comment.content,
        'author': request.user.get_full_name() or request.user.email,
        'created_at': comment.created_at.strftime('%b %d, %H:%M'),
    })


@login_required(login_url='/accounts/login/')
@require_POST
def comment_delete(request, slug, comment_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    comment = get_object_or_404(CardComment, id=comment_id, card__board_list__board__business=biz)
    if comment.author != request.user and biz.owner != request.user:
        return HttpResponseForbidden()
    comment.delete()
    return JsonResponse({'ok': True})


# ─── Labels ───────────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
@require_POST
def label_create(request, slug, board_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    board = get_object_or_404(Board, id=board_id, business=biz)
    name = request.POST.get('name', '').strip()
    color = request.POST.get('color', '#3b82f6')
    if not name:
        return JsonResponse({'error': 'Name required'}, status=400)
    lbl, _ = Label.objects.get_or_create(board=board, name=name, defaults={'color': color})
    return JsonResponse({'id': lbl.id, 'name': lbl.name, 'color': lbl.color})
