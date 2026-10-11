from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('order', '0004_order_line_constraints')]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=19),
        ),
    ]
