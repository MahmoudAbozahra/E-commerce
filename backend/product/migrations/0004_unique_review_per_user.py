from django.db import migrations, models


def reject_duplicate_reviews(apps, schema_editor):
    Review = apps.get_model('product', 'Review')
    duplicates = (
        Review.objects.values('product_id', 'user_id')
        .annotate(row_count=models.Count('id'))
        .filter(row_count__gt=1)
    )
    if duplicates.exists():
        raise RuntimeError(
            'Duplicate product reviews exist; reconcile these rows before migrating.'
        )


class Migration(migrations.Migration):
    dependencies = [('product', '0003_product_quality')]

    operations = [
        migrations.RunPython(reject_duplicate_reviews, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='review',
            constraint=models.UniqueConstraint(
                fields=('product', 'user'), name='unique_product_review_user'
            ),
        ),
    ]
