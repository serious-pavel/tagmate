from django.db import models


class StrippedCharField(models.CharField):
    def clean(self, value, model_instance):
        value = super().clean(value, model_instance)
        if isinstance(value, str):
            value = value.strip()
        return value
