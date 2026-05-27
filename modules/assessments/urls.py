from django.urls import path
from . import views

app_name = 'assessments'
urlpatterns = [
    path('<slug:slug>/', views.assessments_home, name='home'),
    path('<slug:slug>/quizzes/', views.quiz_list, name='quiz_list'),
    path('<slug:slug>/quizzes/new/', views.quiz_create, name='quiz_create'),
    path('<slug:slug>/quizzes/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('<slug:slug>/quizzes/<int:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('<slug:slug>/results/<int:attempt_id>/', views.quiz_result, name='quiz_result'),
]
