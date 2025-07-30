from django.db import models

# Create your models here.

class CountingSession(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    ripe_count = models.IntegerField(default=0)
    raw_count = models.IntegerField(default=0)
    image = models.ImageField(upload_to='counting_images/')
    status = models.CharField(max_length=20, default='stopped')

    class Meta:
        ordering = ['-date']

class PalmOilCount(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    suitable_count = models.IntegerField(default=0)
    unsuitable_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='stopped')
    image = models.ImageField(upload_to='palm_oil_images/', null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Count on {self.date.strftime('%Y-%m-%d %H:%M:%S')}"
