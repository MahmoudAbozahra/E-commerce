from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('product', '0003_product_quality'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('order', '0002_alter_order_state'),
    ]

    operations = [
        migrations.CreateModel(name='Cart', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('updated_at', models.DateTimeField(auto_now=True)),
            ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cart', to=settings.AUTH_USER_MODEL)),
        ]),
        migrations.AlterField(model_name='order', name='city', field=models.CharField(max_length=100)),
        migrations.AlterField(model_name='order', name='country', field=models.CharField(max_length=100)),
        migrations.AlterField(model_name='order', name='payment_method', field=models.CharField(choices=[('cod', 'Cod')], default='cod', max_length=50)),
        migrations.AlterField(model_name='order', name='phone_no', field=models.CharField(max_length=30)),
        migrations.AlterField(model_name='order', name='state', field=models.CharField(blank=True, default='', max_length=100)),
        migrations.AlterField(model_name='order', name='status', field=models.CharField(choices=[('Processing', 'Processing'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')], default='Processing', max_length=50)),
        migrations.AlterField(model_name='order', name='street', field=models.CharField(max_length=255)),
        migrations.AlterField(model_name='order', name='total_amount', field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=11)),
        migrations.AlterField(model_name='order', name='user', field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to=settings.AUTH_USER_MODEL)),
        migrations.AlterField(model_name='order', name='zip_code', field=models.CharField(max_length=20)),
        migrations.AlterField(model_name='orderitem', name='name', field=models.CharField(max_length=200)),
        migrations.AlterField(model_name='orderitem', name='price', field=models.DecimalField(decimal_places=2, max_digits=9)),
        migrations.AlterField(model_name='orderitem', name='quantity', field=models.PositiveIntegerField(default=1)),
        migrations.CreateModel(name='CartItem', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('quantity', models.PositiveIntegerField()),
            ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='order.cart')),
            ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='product.products')),
        ]),
        migrations.AddConstraint(model_name='cartitem', constraint=models.UniqueConstraint(fields=('cart', 'product'), name='unique_cart_product')),
        migrations.AddConstraint(model_name='cartitem', constraint=models.CheckConstraint(check=models.Q(('quantity__gte', 1)), name='cart_quantity_positive')),
    ]
