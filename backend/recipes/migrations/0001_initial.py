# Generated by Django 3.2.18 on 2023-03-30 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AmountIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveSmallIntegerField(default=0, help_text='Введите количество ингредиентов', verbose_name='Количество')),
            ],
            options={
                'verbose_name': 'Ингредиент из рецепта',
                'verbose_name_plural': 'Игредиенты из рецептов',
                'ordering': ('recipe',),
            },
        ),
        migrations.CreateModel(
            name='Carts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
            ],
            options={
                'verbose_name': 'Рецепт в списке покупок',
                'verbose_name_plural': 'Рецепты в списке покупок',
            },
        ),
        migrations.CreateModel(
            name='Favorites',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
            ],
            options={
                'verbose_name': 'Избранный рецепт',
                'verbose_name_plural': 'Избранные рецепты',
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название ингредиента', max_length=100, verbose_name='Название ингредиента')),
                ('measurement_unit', models.CharField(help_text='Введите единицы измерения', max_length=100, verbose_name='Единицы измерения')),
            ],
            options={
                'verbose_name': 'Ингредиент',
                'verbose_name_plural': 'Ингредиенты',
                'ordering': ('name',),
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название рецепта', max_length=100, verbose_name='Название рецепта')),
                ('image', models.ImageField(help_text='Выберите изображение рецепта', upload_to='recipe_images/', verbose_name='Изображение')),
                ('text', models.TextField(db_index=True, help_text='Введите описание рецепта', max_length=1000, verbose_name='Описание рецепта')),
                ('cooking_time', models.PositiveSmallIntegerField(default=0, help_text='Введите время приготовления', verbose_name='Время приготовления')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
            ],
            options={
                'verbose_name': 'Рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ('-pub_date',),
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Введите название тега', max_length=100, unique=True, verbose_name='Название')),
                ('color', models.CharField(default='#FF0000', help_text='Введите HEX-код цвета тега', max_length=7, unique=True, verbose_name='HEX-код')),
                ('slug', models.CharField(help_text='Введите текстовый идентификатор тега', max_length=100, unique=True, verbose_name='Слаг тега')),
            ],
            options={
                'verbose_name': 'Тег',
                'verbose_name_plural': 'Теги',
                'ordering': ('name',),
            },
        ),
    ]
