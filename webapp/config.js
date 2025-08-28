// Конфігурація для Telegram WebApp
// Цей файл буде використовуватися для налаштування webapp
const WEBAPP_CONFIG = {
    // Валюта за замовчуванням
    currency: 'РУБ',
    
    // Відсоток комісії
    commissionRate: 0.15,
    
    // Реквізити для оплати за замовчуванням (будуть показані після підтвердження)
    defaultPaymentDetails: `Реквізити будуть надіслані після підтвердження заявки`,

    // Налаштування UI
    ui: {
        title: '🎮 Поповнення Steam',
        subtitle: 'Заповніть форму для оформлення поповнення',
        submitButtonText: '✅ Підтвердити',
        cancelButtonText: '❌ Скасувати'
    },
    
    // Валідація
    validation: {
        minAmount: 100,
        maxAmount: 50000,
        loginMinLength: 3,
        loginMaxLength: 50
    }
};

// Експортуємо конфігурацію
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WEBAPP_CONFIG;
}
