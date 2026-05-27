from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
import uuid

from hub.views import _get_business_for_user
from .models import LoyaltyProgram, LoyaltyTier, LoyaltyMember, PointTransaction


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _generate_card_number():
    return uuid.uuid4().hex[:12].upper()


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    programs = LoyaltyProgram.objects.filter(business=biz)
    stats = {
        'programs': programs.count(),
        'members': LoyaltyMember.objects.filter(program__business=biz, is_active=True).count(),
        'transactions_today': PointTransaction.objects.filter(member__program__business=biz).count(),
        'total_points_outstanding': sum(m.total_points for m in LoyaltyMember.objects.filter(program__business=biz, is_active=True)),
    }
    top_members = LoyaltyMember.objects.filter(program__business=biz, is_active=True).order_by('-total_points')[:10]
    return render(request, 'loyalty/index.html', {
        'biz': biz, 'programs': programs, 'stats': stats, 'top_members': top_members,
    })


@login_required(login_url='/accounts/login/')
def programs(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            LoyaltyProgram.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', ''),
                reward_type=request.POST.get('reward_type', 'points'),
                points_per_currency=request.POST.get('points_per_currency', 1) or 1,
                currency_per_point=request.POST.get('currency_per_point', 0.01) or 0.01,
                min_redemption_points=request.POST.get('min_redemption_points', 100) or 100,
                expiry_days=request.POST.get('expiry_days', 0) or 0,
            )
            messages.success(request, 'Loyalty program created.')
        elif action == 'delete':
            LoyaltyProgram.objects.filter(pk=request.POST.get('program_id'), business=biz).delete()
            messages.success(request, 'Program deleted.')
        return redirect('loyalty:programs', slug=slug)
    all_programs = LoyaltyProgram.objects.filter(business=biz).prefetch_related('tiers')
    return render(request, 'loyalty/programs.html', {'biz': biz, 'programs': all_programs})


@login_required(login_url='/accounts/login/')
def program_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    program = get_object_or_404(LoyaltyProgram, pk=pk, business=biz)
    tiers = program.tiers.order_by('min_points')
    members = program.members.filter(is_active=True).order_by('-total_points')[:20]
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_tier':
            LoyaltyTier.objects.create(
                program=program,
                name=request.POST.get('tier_name', '').strip(),
                min_points=request.POST.get('min_points', 0) or 0,
                point_multiplier=request.POST.get('multiplier', 1.0) or 1.0,
                color=request.POST.get('color', '#f59e0b').strip(),
                benefits=request.POST.get('benefits', ''),
                position=tiers.count(),
            )
            messages.success(request, 'Tier added.')
        elif action == 'delete_tier':
            LoyaltyTier.objects.filter(pk=request.POST.get('tier_id'), program=program).delete()
            messages.success(request, 'Tier removed.')
        return redirect('loyalty:program_detail', slug=slug, pk=pk)
    return render(request, 'loyalty/program_detail.html', {
        'biz': biz, 'program': program, 'tiers': tiers, 'members': members,
    })


@login_required(login_url='/accounts/login/')
def members(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    qs = LoyaltyMember.objects.filter(program__business=biz).select_related('program', 'tier').order_by('-total_points')
    programs = LoyaltyProgram.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'enroll':
            program = get_object_or_404(LoyaltyProgram, pk=request.POST.get('program'), business=biz)
            card = _generate_card_number()
            while LoyaltyMember.objects.filter(card_number=card).exists():
                card = _generate_card_number()
            LoyaltyMember.objects.create(
                program=program,
                card_number=card,
                name=request.POST.get('name', '').strip(),
                email=request.POST.get('email', '').strip(),
                phone=request.POST.get('phone', '').strip(),
            )
            messages.success(request, f'Member enrolled with card {card}.')
        return redirect('loyalty:members', slug=slug)
    return render(request, 'loyalty/members.html', {
        'biz': biz, 'members': qs, 'programs': programs,
    })


@login_required(login_url='/accounts/login/')
def member_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    member = get_object_or_404(LoyaltyMember, pk=pk, program__business=biz)
    transactions = member.transactions.order_by('-created_at')[:50]
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'adjust_points':
            points = int(request.POST.get('points', 0) or 0)
            tx_type = request.POST.get('type', 'adjust')
            if tx_type == 'redeem':
                points = -abs(points)
            PointTransaction.objects.create(
                member=member,
                transaction_type=tx_type,
                points=points,
                description=request.POST.get('description', '').strip(),
                created_by=request.user,
            )
            member.total_points = max(0, member.total_points + points)
            if points > 0:
                member.lifetime_points += points
            member.save(update_fields=['total_points', 'lifetime_points'])
            messages.success(request, f'Points adjusted: {points:+d}.')
        return redirect('loyalty:member_detail', slug=slug, pk=pk)
    return render(request, 'loyalty/member_detail.html', {
        'biz': biz, 'member': member, 'transactions': transactions,
    })
