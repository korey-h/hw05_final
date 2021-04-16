from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['group'].empty_label = '-без группы-'

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
