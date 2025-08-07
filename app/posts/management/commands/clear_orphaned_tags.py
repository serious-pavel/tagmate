"""
Django command for deleting orphaned Tags
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from posts.models import Tag


class Command(BaseCommand):
    def handle(self, *args, **options):
        def get_orphaned_tags():
            """Get all Tags that are not used anywhere"""
            return Tag.objects.all().annotate(
                pt_count=Count('posttag')
            ).annotate(
                tg_count=Count('tag_groups')
            ).filter(
                pt_count=0,
                tg_count=0
            )

        orphaned_tags = get_orphaned_tags()
        count_before = orphaned_tags.count()

        orphaned_tags.delete()
        count_after = get_orphaned_tags().count()

        print(f"Deleted {count_before - count_after} orphaned tags")
