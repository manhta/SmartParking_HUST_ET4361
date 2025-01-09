from django.db import models

# Create your models here.
class Card(models.Model):
    cardName = models.CharField(max_length=100, blank=False)
    cardBalance = models.DecimalField(decimal_places=2, max_digits=1000, blank=False, null=False)

    def __repr__(self):
        return f'{self.cardName}'
    
    def __str__(self):
        return f'{self.cardName}'
        
