from django.db import models


class StrippedCharField(models.CharField):
    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname)
        if isinstance(value, str):
            value = value.strip()
            setattr(model_instance, self.attname, value)
        return value
