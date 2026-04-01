from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.views import generic
from .models import Course, Enrollment, Submission, Choice, Question
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class CourseListView(generic.ListView):
    model = Course
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'courses'


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name,
                                            last_name=last_name, password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def index(request):
    courses = Course.objects.all()
    context = {'courses': courses}
    return render(request, 'onlinecourse/course_list_bootstrap.html', context)


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if user.is_authenticated:
        if not Enrollment.objects.filter(user=user, course=course).exists():
            Enrollment.objects.create(user=user, course=course, mode='honor')
        return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


def course_details(request, course_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    context['course'] = course
    return render(request, 'onlinecourse/course_detail_bootstrap.html', context)


def submit(request, course_id):
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)
    choices = request.POST.getlist('choice')
    for choice_id in choices:
        choice = Choice.objects.get(pk=choice_id)
        submission.choices.add(choice)
    submission.save()
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result',
                                        args=(course_id, submission.id)))


def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = Submission.objects.get(pk=submission_id)
    choices = submission.choices.all()
    total_score = 0
    for question in course.question_set.all():
        correct = True
        for choice in question.choice_set.all():
            if choice.is_correct and choice not in choices:
                correct = False
            if not choice.is_correct and choice in choices:
                correct = False
        if correct:
            total_score += question.grade
    context['course'] = course
    context['submission'] = submission
    context['choices'] = choices
    context['total_score'] = total_score
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
