from django.urls import path
from . import views

app_name = 'task_board'

urlpatterns = [
    # Board list / create
    path('', views.board_list, name='board_list'),
    path('create/', views.board_create, name='board_create'),

    # Board detail + archive
    path('<int:board_id>/', views.board_detail, name='board_detail'),
    path('<int:board_id>/archive/', views.board_archive, name='board_archive'),

    # Labels
    path('<int:board_id>/labels/create/', views.label_create, name='label_create'),

    # List (column) operations
    path('<int:board_id>/lists/create/', views.list_create, name='list_create'),
    path('lists/<int:list_id>/update/', views.list_update, name='list_update'),
    path('lists/reorder/', views.list_reorder, name='list_reorder'),

    # Card operations
    path('lists/<int:list_id>/cards/create/', views.card_create, name='card_create'),
    path('cards/<int:card_id>/', views.card_detail, name='card_detail'),
    path('cards/<int:card_id>/move/', views.card_move, name='card_move'),
    path('cards/<int:card_id>/archive/', views.card_archive, name='card_archive'),
    path('cards/reorder/', views.cards_reorder, name='cards_reorder'),

    # Checklist
    path('checklists/<int:checklist_id>/items/add/', views.checklist_item_add, name='checklist_item_add'),
    path('checklist-items/<int:item_id>/toggle/', views.checklist_item_toggle, name='checklist_item_toggle'),
    path('checklist-items/<int:item_id>/delete/', views.checklist_item_delete, name='checklist_item_delete'),

    # Comments
    path('cards/<int:card_id>/comments/add/', views.comment_add, name='comment_add'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
]
