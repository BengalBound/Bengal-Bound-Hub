from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import Product, EngineeringChangeOrder, ProductDocument, ProductStage, ShoeArticle, SampleOrder, SampleBuyerComment


def _plm_check(slug, user, min_level=4):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def plm_dashboard(request, slug):
    biz, err = _plm_check(slug, request.user)
    if err:
        return err

    products = Product.objects.filter(business=biz)
    stage_counts = {}
    for choice in Product.STAGES:
        stage_counts[choice[0]] = products.filter(stage=choice[0]).count()

    open_ecos = EngineeringChangeOrder.objects.filter(
        business=biz, status__in=['draft', 'submitted', 'under_review']
    ).count()

    return render(request, 'plm/dashboard.html', {
        'biz': biz,
        'product_count': products.count(),
        'stage_counts': stage_counts,
        'open_ecos': open_ecos,
        'recent_products': products.order_by('-updated_at')[:5],
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def plm_products(request, slug):
    biz, err = _plm_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST' and get_access_level(biz, request.user) >= 5:
        from hub.models import BusinessEmployee
        owner_id = request.POST.get('owner_id', '')
        Product.objects.create(
            business=biz,
            product_code=request.POST.get('product_code', '').strip(),
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            category=request.POST.get('category', '').strip(),
            stage=request.POST.get('stage', 'concept'),
            version=request.POST.get('version', '1.0'),
            owner_id=int(owner_id) if owner_id else None,
        )
        messages.success(request, "Product created.")
        return redirect('plm:products', slug=slug)

    from hub.models import BusinessEmployee
    stage_filter = request.GET.get('stage', '')
    products = Product.objects.filter(business=biz)
    if stage_filter:
        products = products.filter(stage=stage_filter)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'plm/products.html', {
        'biz': biz,
        'products': products,
        'employees': employees,
        'stages': Product.STAGES,
        'stage_filter': stage_filter,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def plm_product_detail(request, slug, product_id):
    biz, err = _plm_check(slug, request.user)
    if err:
        return err

    product = get_object_or_404(Product, pk=product_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'stage_change' and get_access_level(biz, request.user) >= 6:
            old_stage = product.stage
            new_stage = request.POST.get('stage', product.stage)
            product.stage = new_stage
            product.save(update_fields=['stage'])
            ProductStage.objects.create(
                product=product, from_stage=old_stage, to_stage=new_stage,
                changed_by=request.user, notes=request.POST.get('notes', '').strip()
            )
            messages.success(request, f"Stage updated to {product.get_stage_display()}.")
        elif action == 'upload_doc':
            doc_file = request.FILES.get('file')
            ProductDocument.objects.create(
                product=product,
                doc_type=request.POST.get('doc_type', 'other'),
                title=request.POST.get('title', '').strip(),
                file=doc_file,
                version=request.POST.get('version', '1.0'),
                notes=request.POST.get('notes', '').strip(),
                uploaded_by=request.user,
            )
            messages.success(request, "Document uploaded.")
        return redirect('plm:product_detail', slug=slug, product_id=product_id)

    boms = product.boms.filter(is_active=True)
    documents = product.documents.all()
    stage_history = product.stage_history.all()

    return render(request, 'plm/product_detail.html', {
        'biz': biz,
        'product': product,
        'boms': boms,
        'documents': documents,
        'stage_history': stage_history,
        'stages': Product.STAGES,
        'doc_types': ProductDocument.TYPES,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def plm_ecos(request, slug):
    biz, err = _plm_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST' and get_access_level(biz, request.user) >= 4:
        product_id = request.POST.get('product_id', '')
        import random
        import string
        eco_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        EngineeringChangeOrder.objects.create(
            business=biz,
            eco_number=eco_num,
            product_id=int(product_id) if product_id else None,
            title=request.POST.get('title', '').strip(),
            reason=request.POST.get('reason', '').strip(),
            description=request.POST.get('description', '').strip(),
            priority=request.POST.get('priority', 'normal'),
            requested_by=request.user,
        )
        messages.success(request, "ECO submitted.")
        return redirect('plm:ecos', slug=slug)

    status_filter = request.GET.get('status', '')
    ecos = EngineeringChangeOrder.objects.filter(business=biz).select_related('product')
    if status_filter:
        ecos = ecos.filter(status=status_filter)
    products = Product.objects.filter(business=biz, is_active=True)

    return render(request, 'plm/ecos.html', {
        'biz': biz,
        'ecos': ecos,
        'products': products,
        'statuses': EngineeringChangeOrder.STATUS,
        'priorities': EngineeringChangeOrder.PRIORITY,
        'status_filter': status_filter,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


# ── Shoe Article Views ────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def shoe_articles(request, slug):
    biz, err = _plm_check(slug, request.user, min_level=2)
    if err:
        return err
    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_article':
            ShoeArticle.objects.create(
                business=biz,
                article_code=request.POST['article_code'].strip(),
                sku_code=request.POST.get('sku_code', '').strip(),
                name=request.POST.get('name', '').strip(),
                category=request.POST.get('category', 'other'),
                construction=request.POST.get('construction', 'cemented'),
                gender=request.POST.get('gender', 'U'),
                tier=request.POST.get('tier', 'core'),
                last_code=request.POST.get('last_code', '').strip(),
                size_run=request.POST.get('size_run', '').strip(),
                sample_size=request.POST.get('sample_size', '').strip(),
                lifecycle=request.POST.get('lifecycle', 'development'),
                ex_factory_price=request.POST.get('ex_factory_price') or None,
                currency=request.POST.get('currency', 'USD'),
                moq=request.POST.get('moq') or None,
                moq_per_colour=request.POST.get('moq_per_colour') or None,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'Article created.')
        return redirect('plm:shoe_articles', slug=slug)

    lifecycle_filter = request.GET.get('lifecycle', '')
    cat_filter = request.GET.get('category', '')
    articles = ShoeArticle.objects.filter(business=biz)
    if lifecycle_filter:
        articles = articles.filter(lifecycle=lifecycle_filter)
    if cat_filter:
        articles = articles.filter(category=cat_filter)

    return render(request, 'plm/shoe_articles.html', {
        'biz': biz,
        'articles': articles,
        'access_level': level,
        'lifecycle_filter': lifecycle_filter,
        'cat_filter': cat_filter,
        'lifecycles': ShoeArticle.LIFECYCLE,
        'categories': ShoeArticle.CATEGORY,
        'constructions': ShoeArticle.CONSTRUCTION,
        'genders': ShoeArticle.GENDER,
        'tiers': ShoeArticle.TIER,
    })


@login_required(login_url='/accounts/login/')
def shoe_article_detail(request, slug, article_id):
    biz, err = _plm_check(slug, request.user, min_level=2)
    if err:
        return err
    level = get_access_level(biz, request.user)
    article = get_object_or_404(ShoeArticle, pk=article_id, business=biz)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'update_article':
            article.article_code = request.POST.get('article_code', article.article_code).strip()
            article.sku_code = request.POST.get('sku_code', article.sku_code).strip()
            article.name = request.POST.get('name', article.name).strip()
            article.category = request.POST.get('category', article.category)
            article.construction = request.POST.get('construction', article.construction)
            article.gender = request.POST.get('gender', article.gender)
            article.tier = request.POST.get('tier', article.tier)
            article.last_code = request.POST.get('last_code', article.last_code).strip()
            article.size_run = request.POST.get('size_run', article.size_run).strip()
            article.sample_size = request.POST.get('sample_size', article.sample_size).strip()
            article.lifecycle = request.POST.get('lifecycle', article.lifecycle)
            article.ex_factory_price = request.POST.get('ex_factory_price') or None
            article.currency = request.POST.get('currency', article.currency)
            article.moq = request.POST.get('moq') or None
            article.moq_per_colour = request.POST.get('moq_per_colour') or None
            article.pattern_ready = 'pattern_ready' in request.POST
            article.grading_done = 'grading_done' in request.POST
            article.sample_approved = 'sample_approved' in request.POST
            article.costed_bom_ref = request.POST.get('costed_bom_ref', '').strip()
            article.notes = request.POST.get('notes', '').strip()
            article.save()
            messages.success(request, 'Article updated.')

        elif action == 'create_sdo':
            import uuid
            sdo_num = 'SDO-' + uuid.uuid4().hex[:6].upper()
            SampleOrder.objects.create(
                article=article,
                sdo_number=sdo_num,
                stage=request.POST.get('stage', 'proto'),
                status='pending',
                buyer=request.POST.get('buyer', '').strip(),
                quantity=request.POST.get('quantity', 1),
                size_set=request.POST.get('size_set', '').strip(),
                material_colour_spec=request.POST.get('material_colour_spec', '').strip(),
                tech_pack_ref=request.POST.get('tech_pack_ref', '').strip(),
                target_date=request.POST.get('target_date') or None,
                is_charged='is_charged' in request.POST,
                sample_charge=request.POST.get('sample_charge') or None,
                special_instructions=request.POST.get('special_instructions', '').strip(),
                raised_by=request.user,
            )
            messages.success(request, 'Sample order raised.')

        elif action == 'update_sdo_status':
            sdo = get_object_or_404(SampleOrder, pk=request.POST.get('sdo_id'), article=article)
            sdo.status = request.POST.get('status', sdo.status)
            sdo.actual_date = request.POST.get('actual_date') or None
            sdo.save(update_fields=['status', 'actual_date'])
            messages.success(request, 'Sample status updated.')

        elif action == 'add_buyer_comment':
            sdo = get_object_or_404(SampleOrder, pk=request.POST.get('sdo_id'), article=article)
            SampleBuyerComment.objects.create(
                sample_order=sdo,
                aspect=request.POST.get('aspect', 'overall_appearance'),
                comment=request.POST.get('comment', '').strip(),
                action_required=request.POST.get('action_required', '').strip(),
                owner_status=request.POST.get('owner_status', '').strip(),
            )
            messages.success(request, 'Buyer comment logged.')

        return redirect('plm:shoe_article_detail', slug=slug, article_id=article_id)

    sample_orders = article.sample_orders.prefetch_related('buyer_comments').order_by('-created_at')

    return render(request, 'plm/shoe_article_detail.html', {
        'biz': biz,
        'article': article,
        'sample_orders': sample_orders,
        'access_level': level,
        'lifecycles': ShoeArticle.LIFECYCLE,
        'categories': ShoeArticle.CATEGORY,
        'constructions': ShoeArticle.CONSTRUCTION,
        'genders': ShoeArticle.GENDER,
        'tiers': ShoeArticle.TIER,
        'sdo_stages': SampleOrder.STAGE,
        'sdo_statuses': SampleOrder.STATUS,
        'comment_aspects': SampleBuyerComment.ASPECTS,
    })
