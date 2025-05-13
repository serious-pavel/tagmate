from django.shortcuts import render  # noqa


def post_editor(request):
    return render(request, template_name='posts/post_editor.html')
