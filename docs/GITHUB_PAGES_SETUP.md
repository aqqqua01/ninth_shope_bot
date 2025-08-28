# Налаштування GitHub Pages для Telegram WebApp

## Кроки для деплою

### 1. Підготовка репозиторію

1. **Завантажте код на GitHub:**
   ```bash
   git add .
   git commit -m "Add Telegram WebApp with GitHub Pages support"
   git push origin main
   ```

### 2. Увімкнення GitHub Pages

1. Перейдіть до налаштувань репозиторію на GitHub
2. Знайдіть розділ "Pages" в лівому меню
3. У розділі "Source" виберіть "GitHub Actions"
4. Збережіть налаштування

### 3. Автоматичний деплой

После пуша в основну гілку (main/master), GitHub Actions автоматично:
- Скопіює файли з папки `webapp/`
- Розгорне їх на GitHub Pages
- Надасть URL вигляду: `https://username.github.io/repository-name/`

### 4. Налаштування бота

1. **Скопіюйте URL GitHub Pages:**
   - Після успішного деплою URL буде доступний в розділі "Pages" налаштувань репозиторію
   - Або у виводі GitHub Actions

2. **Додайте URL в .env бота:**
   ```env
   WEBAPP_URL=https://username.github.io/repository-name/
   ```

3. **Перезапустіть бота**

### 5. Перевірка роботи

1. Відкрийте бота в Telegram
2. Виконайте команду `/start`
3. Натисніть кнопку "🎮 Оформить пополнение"
4. Переконайтеся, що WebApp відкривається

## Структура файлів

```
.github/workflows/deploy.yml  # GitHub Actions конфігурація
webapp/
  ├── index.html             # Основна сторінка WebApp
  ├── config.js              # Конфігурація WebApp
docs/
  └── GITHUB_PAGES_SETUP.md  # Ця інструкція
.nojekyll                    # Вимикає Jekyll обробку
```

## Налаштування конфігурації

Відредагуйте `webapp/config.js` для зміни:
- Валюти
- Відсотка комісії  
- Реквізитів для оплати
- Текстів інтерфейсу
- Правил валідації

## Troubleshooting

### WebApp не відкривається
- Переконайтеся, що WEBAPP_URL в .env правильний
- Перевірте, що GitHub Pages активовані
- Переконайтеся, що деплой пройшов успішно в розділі "Actions"

### Стилі не застосовуються
- Перевірте наявність файлу `.nojekyll` в корені репозиторію
- Переконайтеся, що всі шляхи в HTML відносні

### Бот не отримує дані з WebApp
- Перевірте консоль браузера на помилки
- Переконайтеся, що Telegram WebApp SDK підключений
- Перевірте налаштування верифікації в боті
