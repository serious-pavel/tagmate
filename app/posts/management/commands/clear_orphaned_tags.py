"""
Django command for deleting orphaned Tags
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from posts.models import Tag


class Command(BaseCommand):
    help = 'Delete orphaned tags that are not used by any posts or tag groups'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        def get_orphaned_tags():
            """Get all Tags that are not used anywhere"""
            return Tag.objects.annotate(
                pt_count=Count('posttag'),
                tg_count=Count('tag_groups')
            ).filter(
                pt_count=0,
                tg_count=0
            )

        orphaned_tags = get_orphaned_tags()
        count = orphaned_tags.count()

        if count == 0:
            self.stdout.write("No orphaned tags found.")
            return

        if options['verbosity'] >= 2:
            tag_names = list(orphaned_tags.values_list('name', flat=True))
            self.stdout.write(f"Orphaned tags: {', '.join(tag_names)}")

        if options['dry_run']:
            self.stdout.write(f"Would delete {count} orphaned tags (dry run)")
        else:
            orphaned_tags.delete()
            result = count - get_orphaned_tags().count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {result} orphaned tags")
            )
