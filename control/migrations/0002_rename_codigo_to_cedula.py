from django.db import migrations, models
import control.models


class Migration(migrations.Migration):

    dependencies = [
        ("control", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="estudiante",
            old_name="codigo",
            new_name="cedula",
        ),
        migrations.AlterField(
            model_name="estudiante",
            name="cedula",
            field=models.CharField(
                max_length=10,
                unique=True,
                help_text="Cédula de identidad ecuatoriana (10 dígitos).",
                validators=[control.models.validar_cedula_ecuatoriana],
            ),
        ),
    ]
