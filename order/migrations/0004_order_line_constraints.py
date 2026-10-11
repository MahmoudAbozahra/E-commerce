from django.db import migrations, models


def validate_existing_data(apps, schema_editor):
    Order = apps.get_model('order', 'Order')
    OrderItem = apps.get_model('order', 'OrderItem')
    if Order.objects.filter(total_amount__lt=0).exists():
        raise RuntimeError('Negative order totals exist; reconcile these rows before migrating.')
    if OrderItem.objects.filter(quantity__lt=1).exists() or OrderItem.objects.filter(price__lt=0).exists():
        raise RuntimeError('Invalid order item quantity or price exists; reconcile these rows before migrating.')


class Migration(migrations.Migration):
    dependencies = [('order', '0003_cart_and_order_integrity')]
    operations = [
        migrations.RunPython(validate_existing_data, migrations.RunPython.noop),
        migrations.AddConstraint(model_name='order', constraint=models.CheckConstraint(check=models.Q(total_amount__gte=0), name='order_total_nonnegative')),
        migrations.AddConstraint(model_name='orderitem', constraint=models.CheckConstraint(check=models.Q(quantity__gte=1), name='order_item_quantity_positive')),
        migrations.AddConstraint(model_name='orderitem', constraint=models.CheckConstraint(check=models.Q(price__gte=0), name='order_item_price_nonnegative')),
    ]
