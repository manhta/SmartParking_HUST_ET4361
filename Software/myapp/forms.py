from django import forms
from .models import Card

class CardAddForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['cardName', 'cardBalance']
