// Конфігурація для Telegram WebApp
// Цей файл буде використовуватися для налаштування webapp
const WEBAPP_CONFIG = {
    // Валюта за замовчуванням
    currency: 'UAH',
    
    // Відсоток комісії
    commissionRate: 0.15,
    
    // Реквізити для оплати за замовчуванням (можна перевизначити через env)
    defaultPaymentDetails: `Номер карти: 4441 1144 1111 1111
Отримувач: Іван Іванов
Банк: ПриватБанк`,

    // Налаштування UI
    ui: {
        title: '🎮 Поповнення Steam',
        subtitle: 'Заповніть форму для оформлення поповнення',
        submitButtonText: '✅ Підтвердити',
        cancelButtonText: '❌ Скасувати'
    },
    
    // Валідація
    validation: {
        minAmount: 1,
        maxAmount: 10000,
        loginMinLength: 3,
        loginMaxLength: 50
    }
};

// Експортуємо конфігурацію
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WEBAPP_CONFIG;
}
