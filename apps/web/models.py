from django.db import models
from django.conf import settings


class CodeAnnotation(models.Model):
    path = models.CharField(max_length=5000)
    line_number = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    annotation = models.TextField()

    def __str__(self):
        return '{}: {}'.format(self.path, self.line_number)
